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


RAW_MATERIAL_LABEL = "materia prima"
RAW_MATERIAL_ALERT_DAYS = 60
SOURCE_FIELDS = ["name", "default_code", "alert_time", "use_time", "categ_id"]
TARGET_MATCH_FIELDS = [
    "name",
    "default_code",
    "company_id",
    "use_expiration_date",
    "expiration_time",
    "use_time",
    "removal_time",
    "alert_time",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Migra la configuracion de caducidad/alerta de producto desde Odoo 8 "
            "hacia Odoo 18."
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
        help="IDs de product.template del origen, separados por comas, para migrar solo esos productos.",
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
    return [int(part.strip()) for part in raw_value.split(",") if part.strip()]


def log(message):
    print(message)


def m2o_id(value):
    if not value:
        return None
    if isinstance(value, (list, tuple)) and value:
        return value[0]
    return None


def normalize_positive_int(value):
    if value in (None, False, ""):
        return None
    try:
        normalized = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    if normalized <= 0:
        return None
    return normalized


def build_source_domain(product_ids):
    if product_ids:
        return [("id", "in", product_ids)]
    return []


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


def read_source_category(source, category_id, cache):
    if not category_id:
        return None
    if category_id not in cache:
        records = source.read(
            "product.category",
            [category_id],
            fields=["name", "complete_name"],
        )
        cache[category_id] = records[0] if records else None
    return cache[category_id]


def is_raw_material_category(category):
    if not category:
        return False
    complete_name = (category.get("complete_name") or category.get("name") or "").lower()
    return RAW_MATERIAL_LABEL in complete_name


def compute_target_alert_days(is_raw_material, expiration_days):
    if is_raw_material:
        return RAW_MATERIAL_ALERT_DAYS, False
    if expiration_days is None:
        return None, False
    computed_days = (expiration_days // 3) + RAW_MATERIAL_ALERT_DAYS
    if computed_days < 0:
        return 0, True
    return computed_days, False


def build_write_values(source_product, source_category, summary):
    raw_material = is_raw_material_category(source_category)
    source_expiration_field = "alert_time" if raw_material else "use_time"
    expiration_days = normalize_positive_int(source_product.get(source_expiration_field))
    alert_days, clamped = compute_target_alert_days(raw_material, expiration_days)

    if raw_material:
        summary["raw_material_products"] += 1
    elif expiration_days is not None:
        summary["computed_alert_products"] += 1
    else:
        summary["products_without_source_expiration"] += 1

    if clamped:
        summary["warnings_clamped_alert"] += 1

    values = {
        "expiration_time": expiration_days or False,
        "use_time": 0,
        "removal_time": 0,
        "alert_time": alert_days if alert_days is not None else False,
        "use_expiration_date": bool(expiration_days or alert_days),
    }
    return (
        values,
        expiration_days,
        alert_days,
        raw_material,
        clamped,
        source_expiration_field,
    )


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
        "Se han encontrado {} productos de origen. Modo: {}.".format(
            len(source_products), "escritura" if args.write else "simulación"
        )
    )

    category_cache = {}
    summary = {
        "processed": 0,
        "updated": 0,
        "skipped_missing_target": 0,
        "skipped_multiple_target": 0,
        "skipped_missing_match_value": 0,
        "raw_material_products": 0,
        "computed_alert_products": 0,
        "products_without_source_expiration": 0,
        "warnings_clamped_alert": 0,
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

        source_category = read_source_category(
            source,
            m2o_id(source_product.get("categ_id")),
            category_cache,
        )
        (
            values,
            expiration_days,
            alert_days,
            raw_material,
            clamped,
            source_expiration_field,
        ) = build_write_values(source_product, source_category, summary)

        if clamped:
            log(
                "AVISO origen {}: la fecha de alerta calculada era negativa y se ajusta a 0.".format(
                    format_product_label(source_product)
                )
            )

        log(
            "SINCRONIZAR origen {} -> destino {} | categoria_origen={} | campo_origen_expiration={} | expiration_time={} | alert_time={} | use_expiration_date={}{}".format(
                format_product_label(source_product),
                format_product_label(target_product),
                repr(source_category.get("complete_name") if source_category else False),
                source_expiration_field,
                expiration_days,
                alert_days,
                values["use_expiration_date"],
                " | regla=Materia prima" if raw_material else " | regla=1/3 caducidad + 60",
            )
        )

        if args.write:
            target.write("product.template", [target_product["id"]], values)
            summary["updated"] += 1

    log("")
    log("Resumen")
    for key, value in summary.items():
        log("{}={}".format(key, value))


if __name__ == "__main__":
    run()
