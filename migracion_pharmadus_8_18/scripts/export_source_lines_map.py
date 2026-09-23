#!/usr/bin/env python3

"""Exporta el mapa producto -> primera linea de produccion desde Odoo 8 (SIGI).

En Odoo 8 la linea de produccion era un registro de ``mrp.routing`` y cada
plantilla de producto declaraba sus lineas validas en
``product.template.routing_ids``. Este script genera un JSON con, para cada
producto, la PRIMERA de esas lineas (la de menor id de ``mrp.routing``, que es el
orden en el que Odoo 8 devuelve el many2many).

El JSON resultante lo consume ''assign_production_lines_to_boms.py'' en el
entorno de Odoo 18. Se hace en dos fases porque no suele haber conectividad
simultanea a los dos Odoo.

Debe ejecutarse donde Odoo 8 sea alcanzable. Sin ``--write`` solo muestra el
resumen, sin escribir el fichero.
"""

import argparse
import json
import os
import socket
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from scripts.odoo_xmlrpc import OdooXmlRpcClient


def parse_args():
    parser = argparse.ArgumentParser(
        description="Exporta el mapa producto -> primera linea de produccion desde Odoo 8."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al fichero JSON de configuracion; se usa la seccion 'source' (Odoo 8).",
    )
    parser.add_argument(
        "--out",
        default="sigi_lines_map.json",
        help="Fichero JSON de salida con el mapa (por defecto sigi_lines_map.json).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Escribe el fichero JSON. Sin este parametro solo muestra el resumen.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout en segundos para las llamadas XML-RPC.",
    )
    return parser.parse_args()


def load_config(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def log(message):
    print(message)


def build_map(source):
    products = source.search_read(
        "product.template",
        [("routing_ids", "!=", False)],
        fields=["id", "default_code", "name", "routing_ids"],
        limit=0,
    )
    routing_ids = sorted({rid for product in products for rid in product["routing_ids"]})
    routings = {
        record["id"]: record
        for record in source.read("mrp.routing", routing_ids, fields=["code", "name"])
    }

    mapping = {}
    skipped_no_code = 0
    for product in products:
        code = (product["default_code"] or "").strip()
        if not code:
            skipped_no_code += 1
            continue
        first_id = min(product["routing_ids"])
        routing = routings[first_id]
        mapping[code] = {
            "line_code": routing["code"],
            "line_name": routing["name"],
            "odoo8_routing_id": first_id,
            "odoo8_product_id": product["id"],
            "odoo8_lines_all": [
                routings[rid]["code"] for rid in sorted(product["routing_ids"])
            ],
        }
    return mapping, len(products), skipped_no_code, len(routing_ids)


def run():
    args = parse_args()
    config = load_config(args.config)
    socket.setdefaulttimeout(args.timeout)
    source = OdooXmlRpcClient(**config["source"])

    mapping, total_products, skipped_no_code, total_routings = build_map(source)

    log("Productos de Odoo 8 con lineas: {}".format(total_products))
    log("  exportados: {}".format(len(mapping)))
    log("  omitidos sin default_code: {}".format(skipped_no_code))
    log("  lineas distintas referenciadas: {}".format(total_routings))

    if not args.write:
        log("")
        log("Modo simulacion: no se ha escrito el fichero. Usa --write para generarlo.")
        return

    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(mapping, handle, ensure_ascii=False, indent=1, sort_keys=True)
    log("")
    log("Mapa escrito en {}".format(os.path.abspath(args.out)))


if __name__ == "__main__":
    run()
