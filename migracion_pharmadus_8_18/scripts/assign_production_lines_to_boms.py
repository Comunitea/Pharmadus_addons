#!/usr/bin/env python3

"""Asigna la linea de produccion de Odoo 8 a las BoMs de Odoo 18.

Odoo 18 no tiene el modelo ``mrp.routing`` ni ningun campo de linea en la BoM: el
unico sitio donde puede vivir la linea es el centro de trabajo de las operaciones
de la BoM. Este script toma el mapa generado por ''export_source_lines_map.py''
(producto -> primera linea de SIGI) y, para cada BoM de Odoo 18 cuyo producto este
en el mapa, apunta sus operaciones al centro de trabajo de esa linea.

Las BoMs sin operaciones no se pueden asignar todavia: se informan aparte, porque
la linea se les quedara puesta cuando se migren las operaciones.

Debe ejecutarse donde Odoo 18 sea alcanzable. Sin ``--write`` solo informa.

Con ``--write`` guarda ademas un fichero de reversion con los centros de trabajo
anteriores de cada operacion tocada.
"""

import argparse
import json
import os
import socket
import sys
from datetime import datetime, timezone

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from scripts.odoo_xmlrpc import OdooXmlRpcClient

READ_BATCH = 200


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Asigna a las operaciones de cada BoM de Odoo 18 el centro de trabajo de la "
            "primera linea de produccion de su producto en Odoo 8."
        )
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al fichero JSON de configuracion; se usa la seccion 'target' (Odoo 18).",
    )
    parser.add_argument(
        "--map",
        required=True,
        help="Fichero JSON generado por export_source_lines_map.py.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Escribe cambios en Odoo 18. Sin este parametro, el script se ejecuta en modo simulacion.",
    )
    parser.add_argument(
        "--target-url",
        default="",
        help="Sobrescribe la URL del destino del config (por ejemplo http://127.0.0.1:18069).",
    )
    parser.add_argument(
        "--revert-out",
        default="/tmp/assign_lines_revert.json",
        help="Fichero donde guardar los valores anteriores para poder revertir (solo con --write).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Muestra tambien las BoMs que no se pueden asignar por no tener operaciones.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout en segundos para las llamadas XML-RPC.",
    )
    return parser.parse_args()


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def log(message):
    print(message)


def read_all(client, model, fields, domain=None):
    records = []
    offset = 0
    while True:
        batch = client.search_read(
            model, domain or [], fields=fields, limit=READ_BATCH, offset=offset, order="id"
        )
        if not batch:
            return records
        records.extend(batch)
        offset += len(batch)


def resolve_line_workcenters(target, line_codes):
    workcenters = {}
    codes = sorted(line_codes)
    for index in range(0, len(codes), READ_BATCH):
        chunk = codes[index : index + READ_BATCH]
        for record in target.search_read(
            "mrp.workcenter",
            [("code", "in", chunk)],
            fields=["id", "code", "name"],
            context={"active_test": False},
        ):
            workcenters.setdefault(record["code"], record)
    return workcenters


def run():
    args = parse_args()
    config = load_json(args.config)
    socket.setdefaulttimeout(args.timeout)

    target_config = dict(config["target"])
    if args.target_url:
        target_config["url"] = args.target_url
    target = OdooXmlRpcClient(**target_config)

    line_map = load_json(args.map)
    line_codes = {info["line_code"] for info in line_map.values()}
    workcenters = resolve_line_workcenters(target, line_codes)

    missing_lines = sorted(line_codes - set(workcenters))
    if missing_lines:
        log(
            "AVISO: no existen centros de trabajo para las lineas: {}".format(
                ", ".join(missing_lines)
            )
        )
        log("       Ejecuta antes create_production_lines.py en este entorno.")
        log("")

    boms = read_all(target, "mrp.bom", ["id", "code", "product_tmpl_id"])
    template_ids = sorted({bom["product_tmpl_id"][0] for bom in boms})
    product_codes = {}
    for index in range(0, len(template_ids), READ_BATCH):
        chunk = template_ids[index : index + READ_BATCH]
        for record in target.read("product.template", chunk, fields=["default_code"]):
            product_codes[record["id"]] = (record["default_code"] or "").strip()

    operations = read_all(
        target, "mrp.routing.workcenter", ["id", "name", "bom_id", "workcenter_id"]
    )
    operations_by_bom = {}
    for operation in operations:
        operations_by_bom.setdefault(operation["bom_id"][0], []).append(operation)

    log(
        "BoMs activas: {} | operaciones: {} en {} BoMs | modo: {}".format(
            len(boms),
            len(operations),
            len(operations_by_bom),
            "escritura" if args.write else "simulacion",
        )
    )
    log("")

    summary = {
        "matched": 0,
        "assigned": 0,
        "operations_changed": 0,
        "without_operations": 0,
        "without_line": 0,
        "missing_line_workcenter": 0,
    }
    revert_entries = []
    pending_samples = []

    for bom in boms:
        product_code = product_codes.get(bom["product_tmpl_id"][0], "")
        info = line_map.get(product_code) if product_code else None
        if not info:
            summary["without_line"] += 1
            continue

        summary["matched"] += 1
        workcenter = workcenters.get(info["line_code"])
        if not workcenter:
            summary["missing_line_workcenter"] += 1
            continue

        bom_operations = operations_by_bom.get(bom["id"], [])
        if not bom_operations:
            summary["without_operations"] += 1
            pending_samples.append((bom["id"], product_code, info["line_code"]))
            continue

        changed = 0
        for operation in bom_operations:
            current_id = operation["workcenter_id"][0] if operation["workcenter_id"] else False
            if current_id == workcenter["id"]:
                continue
            changed += 1
            summary["operations_changed"] += 1
            revert_entries.append(
                {
                    "operation_id": operation["id"],
                    "old_workcenter_id": current_id,
                    "old_workcenter_name": operation["workcenter_id"][1]
                    if operation["workcenter_id"]
                    else False,
                    "new_workcenter_id": workcenter["id"],
                }
            )
            if args.write:
                target.write(
                    "mrp.routing.workcenter", [operation["id"]], {"workcenter_id": workcenter["id"]}
                )

        summary["assigned"] += 1
        log(
            "BoM {:<6} prod={:<22} linea={:<7} ({:<14}) operaciones={} cambiadas={}".format(
                bom["id"],
                product_code[:22],
                info["line_code"],
                info["line_name"][:14],
                len(bom_operations),
                changed,
            )
        )

    if args.verbose and pending_samples:
        log("")
        log("BoMs sin operaciones (nada que asignar todavia):")
        for bom_id, product_code, line_code in pending_samples[:50]:
            log("  BoM {:<6} prod={:<22} linea pendiente={}".format(bom_id, product_code[:22], line_code))

    log("")
    log("Resumen")
    log("boms_activas={}".format(len(boms)))
    log("boms_con_linea_en_origen={}".format(summary["matched"]))
    log("boms_asignadas={}".format(summary["assigned"]))
    log("operaciones_cambiadas={}".format(summary["operations_changed"]))
    log("boms_sin_operaciones={}".format(summary["without_operations"]))
    log("boms_sin_linea_en_origen={}".format(summary["without_line"]))
    log("boms_con_linea_no_creada_en_destino={}".format(summary["missing_line_workcenter"]))
    log("modo={}".format("escritura" if args.write else "simulacion"))

    if args.write:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target_url": target_config.get("url"),
            "entries": revert_entries,
        }
        with open(args.revert_out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=1)
        log("Fichero de reversion: {} ({} operaciones)".format(args.revert_out, len(revert_entries)))
    else:
        log("Ejecuta de nuevo con --write para aplicar los cambios.")


if __name__ == "__main__":
    run()
