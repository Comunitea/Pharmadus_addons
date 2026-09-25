#!/usr/bin/env python3

"""Crea las lineas de produccion de Pharmadus en Odoo 18.

En Odoo 8 las lineas de produccion no eran centros de trabajo: eran registros de
``mrp.routing`` (17 registros en SIGI, con codigo LIN01, FUS01, ...). Odoo 18 ya
no tiene ese modelo, asi que se replican como centros de trabajo
(``mrp.workcenter``) con el mismo codigo y nombre que tenian en Odoo 8, mas la
etiqueta de centro de trabajo "Linea de produccion" para poder separarlas con un
filtro de las etapas de proceso (Acopio, Acondicionamiento, Fabricacion, ...).

El script es idempotente: empareja por ``code``, no duplica y no sobrescribe el
nombre de un centro existente. Sin ``--write`` solo informa de lo que haria.
"""

import argparse
import json
import os
import socket
import sys
import xmlrpc.client

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from scripts.odoo_xmlrpc import OdooXmlRpcClient


# Lineas de produccion de SIGI (mrp.routing de Odoo 8): (codigo, nombre).
# El comentario de cada linea indica el id original en Odoo 8 y sus OF historicas.
PRODUCTION_LINES = [
    ("LIN01", "Linea 01"),  # Odoo 8 id 9, 1674 OF
    ("LIN02", "Linea 02"),  # Odoo 8 id 11, 760 OF
    ("LIN03", "Linea 03"),  # Odoo 8 id 12, 378 OF
    ("LIN04", "Linea 04"),  # Odoo 8 id 13, 621 OF
    ("LIN05", "Linea 05"),  # Odoo 8 id 24, 2284 OF
    ("FUS01", "Fuso 01"),  # Odoo 8 id 14, 140 OF
    ("FUS02", "Fuso 02"),  # Odoo 8 id 15, 2159 OF
    ("EMS01", "Envasados Manual 01"),  # Odoo 8 id 18, 4887 OF
    ("EMS02", "Envasados Manual 02"),  # Odoo 8 id 26, 699 OF
    ("LNDA01", "Llenado Granel Automatico 01 (Sin Uso Por Ahora)"),  # Odoo 8 id 17, 23 OF
    ("LNDM01", "Llenado Granel Manual 01"),  # Odoo 8 id 21, 2283 OF
    ("ESPA01", "Envasados Sobres Piramides Automatico 01 (Sin Uso Por Ahora)"),  # Odoo 8 id 22, 0 OF
    ("MZD01", "Mezcladora 01"),  # Odoo 8 id 19, 891 OF
    ("LAP01", "Limpieza y Acond. de producto 01"),  # Odoo 8 id 20, 49 OF
    ("PM01", "Procesos Manuales 01"),  # Odoo 8 id 25, 400 OF
    ("REP01", "Reprocesado"),  # Odoo 8 id 23, 131 OF
    ("Otros", "Otros"),  # Odoo 8 id 16, 182 OF
]

DEFAULT_TAG_NAME = "Línea de producción"

# Valores equivalentes a los que tenian las rutas en Odoo 8 (eficiencia 100 %,
# sin coste horario definido). La capacidad se deja en 1, como los demas centros.
WORKCENTER_VALUES = {
    "default_capacity": 1.0,
    "time_efficiency": 100.0,
    "costs_hour": 0.0,
    "active": True,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Replica las lineas de produccion de Odoo 8 (mrp.routing) como centros de "
            "trabajo de Odoo 18, con su etiqueta."
        )
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al fichero JSON de configuracion con las conexiones de origen y destino.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Escribe cambios en Odoo 18. Sin este parametro, el script se ejecuta en modo simulacion.",
    )
    parser.add_argument(
        "--tag-name",
        default=DEFAULT_TAG_NAME,
        help="Nombre de la etiqueta de centro de trabajo que agrupa las lineas.",
    )
    parser.add_argument(
        "--no-tag",
        action="store_true",
        help="No crea ni asigna la etiqueta de lineas de produccion.",
    )
    parser.add_argument(
        "--codes",
        default="",
        help="Codigos concretos a procesar, separados por comas (por defecto, todas las lineas).",
    )
    parser.add_argument(
        "--target-url",
        default="",
        help=(
            "Sobrescribe la URL del entorno destino del config; util para probar contra "
            "el proxy local de desarrollo, por ejemplo http://127.0.0.1:18069."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout en segundos para las llamadas XML-RPC (evita que el script se quede colgado).",
    )
    return parser.parse_args()


def load_config(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def log(message):
    print(message)


def parse_codes(raw_value):
    if not raw_value:
        return []
    return [part.strip() for part in raw_value.split(",") if part.strip()]


def select_lines(codes):
    if not codes:
        return list(PRODUCTION_LINES)
    known = {code: name for code, name in PRODUCTION_LINES}
    unknown = [code for code in codes if code not in known]
    if unknown:
        raise ValueError(
            "Codigos desconocidos: {}. Disponibles: {}".format(
                ", ".join(unknown), ", ".join(code for code, _ in PRODUCTION_LINES)
            )
        )
    return [(code, known[code]) for code in codes]


def check_mrp_installed(target):
    count = target.execute(
        "ir.module.module",
        "search_count",
        [("name", "=", "mrp"), ("state", "=", "installed")],
    )
    if not count:
        raise RuntimeError(
            "El modulo 'mrp' no esta instalado en el entorno destino; no se pueden crear centros de trabajo."
        )


def find_workcenter(target, code):
    records = target.search_read(
        "mrp.workcenter",
        [("code", "=", code)],
        fields=["id", "code", "name", "active"],
        context={"active_test": False},
    )
    if not records:
        return None
    if len(records) > 1:
        log(
            "AVISO: hay {} centros de trabajo con el codigo '{}'; se usa el id {}".format(
                len(records), code, records[0]["id"]
            )
        )
    return records[0]


def find_or_create_tag(target, name, write):
    records = target.search_read("mrp.workcenter.tag", [("name", "=", name)], fields=["id", "name"])
    if records:
        return records[0], False
    if not write:
        return None, True
    tag_id = target.execute("mrp.workcenter.tag", "create", {"name": name})
    return {"id": tag_id, "name": name}, True


def run():
    args = parse_args()
    config = load_config(args.config)
    socket.setdefaulttimeout(args.timeout)

    target_config = dict(config["target"])
    if args.target_url:
        target_config["url"] = args.target_url

    try:
        target = OdooXmlRpcClient(**target_config)
    except (OSError, xmlrpc.client.ProtocolError, xmlrpc.client.Fault) as error:
        raise RuntimeError(
            "No se ha podido conectar con el entorno destino {}: {}".format(
                target_config.get("url"), error
            )
        )

    lines = select_lines(parse_codes(args.codes))

    check_mrp_installed(target)

    log(
        "Lineas a procesar: {} | modo: {}".format(
            len(lines), "escritura" if args.write else "simulacion"
        )
    )

    created, existing, tagged = [], [], []
    for code, name in lines:
        record = find_workcenter(target, code)
        if record:
            existing.append((code, record["name"], record["id"], record["active"]))
            log(
                "YA EXISTE  {:<7} {:<55} id={} activo={}".format(
                    code, record["name"], record["id"], record["active"]
                )
            )
        elif args.write:
            values = dict(WORKCENTER_VALUES)
            values.update({"name": name, "code": code})
            new_id = target.execute("mrp.workcenter", "create", values)
            created.append((code, name, new_id))
            log("CREADO     {:<7} {:<55} id={}".format(code, name, new_id))
        else:
            log("CREARIA    {:<7} {}".format(code, name))

    if not args.no_tag:
        tag, tag_created = find_or_create_tag(target, args.tag_name, args.write)
        if tag is None:
            log("CREARIA ETIQUETA '{}'".format(args.tag_name))
        else:
            log(
                "{} ETIQUETA '{}' id={}".format(
                    "CREADA" if tag_created else "YA EXISTE", tag["name"], tag["id"]
                )
            )
            for code, _name in lines:
                record = find_workcenter(target, code)
                if not record:
                    continue
                if args.write:
                    target.write("mrp.workcenter", [record["id"]], {"tag_ids": [[4, tag["id"]]]})
                tagged.append((code, record["id"]))
                log("  ETIQUETARIA/ETIQUETADO {} (id={})".format(code, record["id"]))

    log("")
    log("Resumen")
    log("lineas_definidas={}".format(len(lines)))
    log("creadas={}".format(len(created)))
    log("ya_existentes={}".format(len(existing)))
    log("etiquetadas={}".format(len(tagged)))
    log("modo={}".format("escritura" if args.write else "simulacion"))
    if not args.write:
        log("Ejecuta de nuevo con --write para aplicar los cambios.")


if __name__ == "__main__":
    run()
