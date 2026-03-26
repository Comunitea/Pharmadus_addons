#!/usr/bin/env python3

import argparse
import json
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from scripts.odoo_xmlrpc import OdooXmlRpcClient


SOURCE_FIELDS = ["name", "default_code", "categ_ids"]
TARGET_MATCH_FIELDS = ["name", "default_code", "product_tag_ids"]
SOURCE_CATEGORY_PREFIX = "NoContable"
EXCLUDED_CATEGORY_NAMES = {
    "NoContable",
    "Departamento",
    "Para_Comisiones",
    "Farmacia",
    "Horeca",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Inspecciona las categorías extra de producto en Odoo 8 "
            "y muestra las ramas que cuelgan de 'NoContable'."
        )
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al fichero JSON de configuración con credenciales de origen y destino.",
    )
    parser.add_argument(
        "--match-field",
        default="default_code",
        help="Campo usado para emparejar product.template entre origen y destino.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Límite opcional de productos de origen a procesar.",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Desplazamiento para la búsqueda de productos de origen.",
    )
    parser.add_argument(
        "--product-ids",
        default="",
        help="IDs de product.template del origen, separados por comas, para revisar solo esos productos.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Escribe cambios en Odoo 18. Sin este parámetro, el script se ejecuta en modo simulación.",
    )
    return parser.parse_args()


def load_config(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_id_list(raw_value):
    if not raw_value:
        return []
    result = []
    for part in raw_value.split(","):
        part = part.strip()
        if not part:
            continue
        result.append(int(part))
    return result


def log(message):
    print(message)


def build_source_domain(product_ids):
    domain = [("categ_ids", "!=", False)]
    if product_ids:
        domain.append(("id", "in", product_ids))
    return domain


def format_product_label(product):
    return "[id={}] {} ({})".format(
        product["id"],
        product.get("name") or "-",
        product.get("default_code") or "sin default_code",
    )


def find_target_product(target, match_field, source_product):
    match_value = source_product.get(match_field)
    if not match_value:
        return None, "missing_match_value"

    records = target.search_read(
        "product.template",
        [(match_field, "=", match_value)],
        fields=TARGET_MATCH_FIELDS,
    )
    if not records:
        return None, "not_found"
    if len(records) > 1:
        return None, "multiple_found"
    return records[0], None


def read_categories(source, category_ids, cache):
    missing_ids = [cat_id for cat_id in category_ids if cat_id not in cache]
    if missing_ids:
        records = source.read(
            "product.category",
            missing_ids,
            fields=["name", "complete_name", "parent_id"],
        )
        for record in records:
            cache[record["id"]] = record
    return [cache[cat_id] for cat_id in category_ids if cat_id in cache]


def filter_extra_categories(categories):
    filtered = []
    for category in categories:
        if category.get("name") in EXCLUDED_CATEGORY_NAMES:
            continue
        complete_name = category.get("complete_name") or category.get("name") or ""
        if complete_name == SOURCE_CATEGORY_PREFIX or complete_name.startswith(
            SOURCE_CATEGORY_PREFIX + " /"
        ):
            filtered.append(category)
    return filtered


def ensure_target_tags(target, tag_names, cache):
    tag_ids = []
    for tag_name in tag_names:
        if tag_name in cache:
            tag_ids.append(cache[tag_name])
            continue

        records = target.search_read("product.tag", [("name", "=", tag_name)], fields=["name"])
        if records:
            tag_id = records[0]["id"]
        else:
            tag_id = target.execute("product.tag", "create", {"name": tag_name})
        cache[tag_name] = tag_id
        tag_ids.append(tag_id)
    return tag_ids


def run():
    args = parse_args()
    config = load_config(args.config)
    source = OdooXmlRpcClient(**config["source"])
    target = OdooXmlRpcClient(**config["target"])
    product_ids = parse_id_list(args.product_ids)

    if args.match_field not in ("name", "default_code", "id"):
        raise ValueError("Campo de emparejamiento no soportado: {}".format(args.match_field))

    domain = build_source_domain(product_ids)
    search_kwargs = {"offset": args.offset}
    if args.limit:
        search_kwargs["limit"] = args.limit

    source_products = source.search_read(
        "product.template",
        domain,
        fields=SOURCE_FIELDS,
        order="id",
        **search_kwargs
    )

    log(
        "Se han encontrado {} productos de origen con categorías extra. Modo: {}.".format(
            len(source_products),
            "escritura" if args.write else "simulación",
        )
    )

    category_cache = {}
    tag_cache = {}
    summary = {
        "processed": 0,
        "updated": 0,
        "with_nocontable_categories": 0,
        "skipped_missing_target": 0,
        "skipped_multiple_target": 0,
        "skipped_missing_match_value": 0,
    }

    for source_product in source_products:
        summary["processed"] += 1
        target_product, error_code = find_target_product(target, args.match_field, source_product)

        if error_code == "missing_match_value":
            summary["skipped_missing_match_value"] += 1
            log(
                "OMITIDO origen {}: el campo de emparejamiento '{}' está vacío.".format(
                    format_product_label(source_product), args.match_field
                )
            )
            continue

        if error_code == "not_found":
            summary["skipped_missing_target"] += 1
            log(
                "OMITIDO origen {}: no se ha encontrado producto destino por {}='{}'.".format(
                    format_product_label(source_product),
                    args.match_field,
                    source_product.get(args.match_field),
                )
            )
            continue

        if error_code == "multiple_found":
            summary["skipped_multiple_target"] += 1
            log(
                "OMITIDO origen {}: se han encontrado varios productos destino por {}='{}'.".format(
                    format_product_label(source_product),
                    args.match_field,
                    source_product.get(args.match_field),
                )
            )
            continue

        categories = read_categories(source, source_product.get("categ_ids") or [], category_cache)
        extra_categories = filter_extra_categories(categories)
        if not extra_categories:
            continue

        summary["with_nocontable_categories"] += 1
        category_paths = [cat["complete_name"] for cat in extra_categories]
        category_leaf_names = [cat["name"] for cat in extra_categories]

        target_tag_ids = ensure_target_tags(target, category_leaf_names, tag_cache)
        existing_tag_ids = target_product.get("product_tag_ids") or []
        final_tag_ids = sorted(set(existing_tag_ids + target_tag_ids))

        log(
            "CATEGORÍAS EXTRA origen {} -> destino {} | rutas={} | etiquetas_sugeridas={} | tag_ids_destino={}".format(
                format_product_label(source_product),
                format_product_label(target_product),
                category_paths,
                category_leaf_names,
                final_tag_ids,
            )
        )

        if args.write:
            target.write(
                "product.template",
                [target_product["id"]],
                {"product_tag_ids": [(6, 0, final_tag_ids)]},
            )
            summary["updated"] += 1

    log("")
    log("Resumen")
    log("processed={}".format(summary["processed"]))
    log("updated={}".format(summary["updated"]))
    log("with_nocontable_categories={}".format(summary["with_nocontable_categories"]))
    log("skipped_missing_target={}".format(summary["skipped_missing_target"]))
    log("skipped_multiple_target={}".format(summary["skipped_multiple_target"]))
    log("skipped_missing_match_value={}".format(summary["skipped_missing_match_value"]))


if __name__ == "__main__":
    run()
