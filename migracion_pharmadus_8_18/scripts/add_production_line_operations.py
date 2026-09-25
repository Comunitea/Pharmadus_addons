#!/usr/bin/env python3

"""Anade a cada BoM de Odoo 18 la operacion de su linea de produccion de Odoo 8.

La linea de produccion de Odoo 8 (``mrp.routing``) no tiene equivalente en Odoo 18,
asi que se representa como **una operacion de la BoM** cuyo centro de trabajo es el
de esa linea: el nombre de la operacion es el nombre de la linea (por ejemplo
"Linea 01") y el centro de trabajo lleva su codigo (LIN01).

Entrada: el mapa producto -> primera linea generado por
''export_source_lines_map.py''. Para cada BoM activa cuyo producto este en el mapa:

- localiza el centro de trabajo de la linea por su codigo,
- si la BoM ya tenia operaciones, las elimina (``--keep-existing`` para no hacerlo),
- crea una unica operacion con ``sequence=10``, duracion manual 0 minutos y modo de
  duracion manual, y anota su id en el fichero de reversion.

Es idempotente: si la BoM ya tiene una operacion con ese nombre y ese centro de
trabajo, no crea otra. Sin ``--write`` solo informa.
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
OPERATION_SEQUENCE = 10
OPERATION_DURATION = 0.0


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Anade una operacion por BoM con el centro de trabajo de la primera linea de "
            "produccion de su producto en Odoo 8."
        )
    )
    parser.add_argument("--config", required=True, help="Configuracion; se usa 'target' (Odoo 18).")
    parser.add_argument("--map", required=True, help="JSON de export_source_lines_map.py.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Escribe cambios. Sin este parametro, el script se ejecuta en modo simulacion.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="No elimina las operaciones que ya tuviera la BoM (por defecto si se eliminan).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Procesa solo las primeras N BoMs (util para pruebas).",
    )
    parser.add_argument(
        "--target-url",
        default="",
        help="Sobrescribe la URL del destino del config (por ejemplo http://127.0.0.1:18069).",
    )
    parser.add_argument(
        "--revert-out",
        default="/tmp/add_line_operations_revert.json",
        help="Fichero con lo creado y lo eliminado, para poder revertir (solo con --write).",
    )
    parser.add_argument("--timeout", type=int, default=60, help="Timeout de las llamadas XML-RPC.")
    return parser.parse_args()


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def log(message):
    print(message)


def read_all(client, model, fields, domain=None):
    records, offset = [], 0
    while True:
        batch = client.search_read(
            model, domain or [], fields=fields, limit=READ_BATCH, offset=offset, order="id"
        )
        if not batch:
            return records
        records.extend(batch)
        offset += len(batch)


def run():
    args = parse_args()
    config = load_json(args.config)
    socket.setdefaulttimeout(args.timeout)

    target_config = dict(config["target"])
    if args.target_url:
        target_config["url"] = args.target_url
    target = OdooXmlRpcClient(**target_config)

    line_map = load_json(args.map)
    line_codes = sorted({info["line_code"] for info in line_map.values()})
    workcenters = {}
    for index in range(0, len(line_codes), READ_BATCH):
        chunk = line_codes[index : index + READ_BATCH]
        for record in target.search_read(
            "mrp.workcenter",
            [("code", "in", chunk)],
            fields=["id", "code", "name"],
            context={"active_test": False},
        ):
            workcenters.setdefault(record["code"], record)

    missing = sorted(set(line_codes) - set(workcenters))
    if missing:
        log("AVISO: sin centro de trabajo para las lineas: {}".format(", ".join(missing)))
        log("")

    boms = read_all(target, "mrp.bom", ["id", "code", "product_tmpl_id"])
    template_ids = sorted({bom["product_tmpl_id"][0] for bom in boms})
    product_codes = {}
    for index in range(0, len(template_ids), READ_BATCH):
        chunk = template_ids[index : index + READ_BATCH]
        for record in target.read("product.template", chunk, fields=["default_code"]):
            product_codes[record["id"]] = (record["default_code"] or "").strip()

    operations = read_all(
        target, "mrp.routing.workcenter", ["id", "name", "bom_id", "workcenter_id", "sequence",
                                           "time_mode", "time_cycle_manual"]
    )
    operations_by_bom = {}
    for operation in operations:
        operations_by_bom.setdefault(operation["bom_id"][0], []).append(operation)

    log(
        "BoMs activas: {} | operaciones activas: {} | modo: {} | keep_existing: {}".format(
            len(boms), len(operations), "escritura" if args.write else "simulacion",
            args.keep_existing,
        )
    )
    log("")

    summary = {
        "matched": 0,
        "created": 0,
        "replaced": 0,
        "operations_removed": 0,
        "already_ok": 0,
        "without_line": 0,
        "missing_workcenter": 0,
        "without_operations": 0,
    }
    created_entries, removed_entries = [], []
    processed = 0

    for bom in boms:
        product_code = product_codes.get(bom["product_tmpl_id"][0], "")
        info = line_map.get(product_code) if product_code else None
        if not info:
            summary["without_line"] += 1
            continue

        summary["matched"] += 1
        workcenter = workcenters.get(info["line_code"])
        if not workcenter:
            summary["missing_workcenter"] += 1
            continue

        if args.limit and processed >= args.limit:
            continue
        processed += 1

        existing = operations_by_bom.get(bom["id"], [])
        if not existing:
            summary["without_operations"] += 1
        already = [
            op
            for op in existing
            if op["name"] == info["line_name"]
            and op["workcenter_id"]
            and op["workcenter_id"][0] == workcenter["id"]
        ]
        if already:
            summary["already_ok"] += 1
            log(
                "YA OK      BoM {:<6} prod={:<22} operacion={:<20} id={}".format(
                    bom["id"], product_code[:22], info["line_name"][:20], already[0]["id"]
                )
            )
            continue

        removed = []
        if existing and not args.keep_existing:
            removed = existing
            summary["operations_removed"] += len(removed)
            summary["replaced"] += 1

        log(
            "{:<10} BoM {:<6} prod={:<22} operacion={:<20} centro={:<7} operaciones_previas={}".format(
                "SUSTITUIR" if removed else "CREAR",
                bom["id"],
                product_code[:22],
                info["line_name"][:20],
                info["line_code"],
                len(removed),
            )
        )

        if not args.write:
            summary["created"] += 1
            continue

        for operation in removed:
            target.execute("mrp.routing.workcenter", "unlink", [operation["id"]])
            removed_entries.append(
                {
                    "id": operation["id"],
                    "name": operation["name"],
                    "bom_id": operation["bom_id"][0],
                    "workcenter_id": operation["workcenter_id"][0] if operation["workcenter_id"] else False,
                    "sequence": operation["sequence"],
                    "time_mode": operation["time_mode"],
                    "time_cycle_manual": operation["time_cycle_manual"],
                }
            )

        new_id = target.execute(
            "mrp.routing.workcenter",
            "create",
            {
                "name": info["line_name"],
                "bom_id": bom["id"],
                "workcenter_id": workcenter["id"],
                "sequence": OPERATION_SEQUENCE,
                "time_mode": "manual",
                "time_cycle_manual": OPERATION_DURATION,
            },
        )
        created_entries.append(
            {
                "id": new_id,
                "bom_id": bom["id"],
                "product_code": product_code,
                "name": info["line_name"],
                "workcenter_id": workcenter["id"],
                "workcenter_code": info["line_code"],
            }
        )
        summary["created"] += 1

    log("")
    log("Resumen")
    log("boms_activas={}".format(len(boms)))
    log("boms_con_linea_en_origen={}".format(summary["matched"]))
    log("boms_procesadas={}".format(processed))
    log("operaciones_creadas={}".format(summary["created"]))
    log("boms_sustituidas={}".format(summary["replaced"]))
    log("operaciones_eliminadas={}".format(summary["operations_removed"]))
    log("boms_ya_correctas={}".format(summary["already_ok"]))
    log("boms_sin_operaciones_previas={}".format(summary["without_operations"]))
    log("boms_sin_linea_en_origen={}".format(summary["without_line"]))
    log("boms_sin_centro_de_linea={}".format(summary["missing_workcenter"]))
    log("modo={}".format("escritura" if args.write else "simulacion"))

    if args.write:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target_url": target_config.get("url"),
            "created": created_entries,
            "removed": removed_entries,
        }
        with open(args.revert_out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=1)
        log(
            "Reversion: {} (creadas={}, eliminadas={})".format(
                args.revert_out, len(created_entries), len(removed_entries)
            )
        )
    else:
        log("Ejecuta de nuevo con --write para aplicar los cambios.")


if __name__ == "__main__":
    run()
