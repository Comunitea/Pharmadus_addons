# Migración Pharmadus 8 18

Utilidades de consola para migrar datos de Pharmadus desde Odoo 8 hacia Odoo 18 sin acoplar la lógica al módulo Odoo.

## Estructura

- `config.example.json`: ejemplo de configuración para conexiones origen y destino.
- `scripts/odoo_xmlrpc.py`: cliente XML-RPC reutilizable.
- `scripts/migrate_product_specifications.py`: primer script para migrar los campos de la pestaña "Especificaciones" de `product.template`.
- `scripts/migrate_product_extra_categories.py`: inspecciona las categorías extra de Odoo 8 (`categ_ids`) y muestra por pantalla las ramas bajo `NoContable`.
  Excluye `Para_Comisiones`, `Farmacia` y `Horeca`.

## Requisitos

- Python 3.8 o superior.
- Acceso por XML-RPC a ambos Odoo.
- El módulo con los campos de destino debe estar instalado en Odoo 18.

## Configuración

1. Copia `config.example.json` a un fichero privado, por ejemplo `config.json`.
2. Rellena credenciales, URL y bases de datos.

Ejemplo:

```json
{
  "source": {
    "url": "https://odoo8.example.com",
    "db": "odoo8_db",
    "username": "admin",
    "password": "secret",
    "verify_ssl": true
  },
  "target": {
    "url": "https://odoo18.example.com",
    "db": "odoo18_db",
    "username": "admin",
    "password": "secret",
    "verify_ssl": true
  }
}
```

Si alguno de los entornos usa un certificado interno o una cadena incompleta, puedes usar `false` temporalmente en `verify_ssl`.

## Primer script disponible

`scripts/migrate_product_specifications.py` migra estos campos de `product.template`:

- `pharmadus_quantity`
- `pharmadus_elements_per_outer_box`
- `pharmadus_elements_per_display_box`
- `pharmadus_elements_per_full_box`
- `pharmadus_line_id`
- `pharmadus_subline_id`
- `pharmadus_packaging_type_id`
- `pharmadus_base_form_id`
- `pharmadus_garment_id`
- `pharmadus_purchase_line_id`
- `pharmadus_purchase_subline_id`
- `pharmadus_grouping_id`
- `pharmadus_subgrouping`

Los many2one se resuelven por `name`, no por `xml_id`.

Para `pharmadus_subline_id` y `pharmadus_purchase_subline_id`, el script también filtra por la línea ya resuelta en Odoo 18 para evitar asignaciones incorrectas cuando existan nombres repetidos.

## Mapeo de campos

Correspondencia principal entre Odoo 8 y Odoo 18:

| Odoo 8 | Odoo 18 | Notas |
|---|---|---|
| `qty` | `pharmadus_quantity` | Se normaliza a entero mínimo 1. |
| `line` | `pharmadus_line_id` | Coincidencia por `name`. |
| `subline` | `pharmadus_subline_id` | Coincidencia por `name` y por la línea ya resuelta en destino. |
| `container_id` | `pharmadus_packaging_type_id` | Coincidencia por `name`. |
| `base_form_id` | `pharmadus_base_form_id` | Coincidencia por `name`. |
| `clothing` | `pharmadus_garment_id` | `dressed` -> `Vestida`, `naked` -> `Desnuda`. |
| `purchase_line` | `pharmadus_purchase_line_id` | Coincidencia por `name`. |
| `purchase_subline` | `pharmadus_purchase_subline_id` | Coincidencia por `name` y por la línea de compra ya resuelta en destino. |
| `grouping` | `pharmadus_grouping_id` | Coincidencia por `name`. |
| `subgrouping` | `pharmadus_subgrouping` | Texto directo. |
| `packing_internal` | `pharmadus_elements_per_outer_box` | Se normaliza a entero mínimo 1. |
| `packing` | `pharmadus_elements_per_display_box` | Se normaliza a entero mínimo 1. |
| `box_elements` | `pharmadus_elements_per_full_box` | Se normaliza a entero mínimo 1. |

Notas sobre los numéricos:

- Si el origen viene vacío, a cero o con un valor no válido, el script usa `1` para respetar las restricciones del modelo en Odoo 18.
- La correspondencia de cajas se basa en la estructura de la vista "Specs" de Odoo 8.

## Uso

Simulación sin escribir cambios:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_product_specifications.py \
  --config migracion_pharmadus_8_18/config.json
```

Escritura real:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_product_specifications.py \
  --config migracion_pharmadus_8_18/config.json \
  --write
```

Limitar volumen para pruebas:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_product_specifications.py \
  --config migracion_pharmadus_8_18/config.json \
  --limit 20
```

Migrar solo productos concretos del origen:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_product_specifications.py \
  --config migracion_pharmadus_8_18/config.json \
  --product-ids 10,25,30
```

Cambiar el campo de emparejamiento del producto:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_product_specifications.py \
  --config migracion_pharmadus_8_18/config.json \
  --match-field name
```

## Notas importantes

- El script busca el producto destino por el campo indicado en `--match-field`. Por defecto usa `default_code`.
- Si no encuentra producto destino, lo informa y lo omite.
- Si encuentra más de un producto destino con el mismo valor de emparejamiento, lo informa y lo omite.
- Si un valor de catálogo no encuentra coincidencia en Odoo 18, lo informa y no toca ese campo en el producto destino.
- El script no crea productos ni valores de catálogo. Solo asigna valores ya existentes en Odoo 18.
