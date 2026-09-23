# Migración Pharmadus 8 18

Utilidades de consola para migrar datos de Pharmadus desde Odoo 8 hacia Odoo 18 sin acoplar la lógica al módulo Odoo.

## Estructura

- `config.example.json`: ejemplo de configuración para conexiones origen y destino.
- `scripts/odoo_xmlrpc.py`: cliente XML-RPC reutilizable.
- `scripts/migrate_product_specifications.py`: primer script para migrar los campos de la pestaña "Especificaciones" de `product.template`.
- `scripts/migrate_product_extra_categories.py`: inspecciona las categorías extra de Odoo 8 (`categ_ids`) y muestra por pantalla las ramas bajo `NoContable`.
  Excluye `Para_Comisiones`, `Farmacia` y `Horeca`.
- `scripts/migrate_product_expiry.py`: migra a `expiration_time` usando `alert_time` en `Materia prima` y `use_time` en el resto, reinicia `use_time` y `removal_time`, y recalcula `alert_time` según la categoría del producto.
- `scripts/migrate_user_signatures.py`: migra firmas de `res.users.signature_moved1` a `res.users.pharmadus_signature_image`.
- `scripts/migrate_customer_valued_picking.py`: marca `res.partner.valued_picking` en todos los clientes de Odoo 18.
- `scripts/create_production_lines.py`: crea las líneas de producción de SIGI (modelo `mrp.routing` de Odoo 8) como centros de trabajo de Odoo 18, con su etiqueta.
- `scripts/export_source_lines_map.py` y `scripts/assign_production_lines_to_boms.py`: exportan desde Odoo 8 la primera línea de cada plantilla de producto y la asignan a las operaciones de sus BoMs en Odoo 18.

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

## Caducidad y alerta de producto

`scripts/migrate_product_expiry.py` aplica estas reglas sobre `product.template`:

- Si la categoría origen contiene `Materia prima`, copia `alert_time` de Odoo 8 al campo `expiration_time` de Odoo 18.
- Si la categoría origen no es `Materia prima`, copia `use_time` de Odoo 8 al campo `expiration_time` de Odoo 18.
- Si la categoría del producto en Odoo 8 contiene `Materia prima`, fija `alert_time = 60` en Odoo 18.
- Si la categoría no es `Materia prima` y `use_time` en origen es distinto de `0`, calcula `alert_time = (expiration_time // 3) + 60`.
- Si ese cálculo sale negativo, el script lo ajusta a `0` y lo informa por pantalla.
- Pone `use_time = 0` y `removal_time = 0` en Odoo 18 para los productos afectados por el script.
- Activa `use_expiration_date` cuando el producto queda con `expiration_time` o `alert_time` informado.

Simulación sin escribir cambios:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_product_expiry.py \
  --config migracion_pharmadus_8_18/config.json
```

Escritura real:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_product_expiry.py \
  --config migracion_pharmadus_8_18/config.json \
  --write
```

Limitar volumen para pruebas:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_product_expiry.py \
  --config migracion_pharmadus_8_18/config.json \
  --limit 20
```

## Firmas de usuario

`scripts/migrate_user_signatures.py` migra las firmas de usuario desde la columna local heredada `res_users.signature_moved1` al campo `pharmadus_signature_image` de Odoo 18.

El script debe ejecutarse dentro de `odoo shell`, usa el `env` local, no usa XML-RPC y solo escribe la firma cuando el campo destino está vacío.

Simulación sin escribir cambios:

```bash
docker compose -f /opt/pharmadus/devel.yaml exec -T odoo \
  odoo shell -d devel --no-http <<'PY'
import sys
sys.path.insert(0, '/opt/odoo/custom/src/private')
from migracion_pharmadus_8_18.scripts.migrate_user_signatures import main
main(env, [])
PY
```

Escritura real:

```bash
docker compose -f /opt/pharmadus/devel.yaml exec -T odoo \
  odoo shell -d devel --no-http <<'PY'
import sys
sys.path.insert(0, '/opt/odoo/custom/src/private')
from migracion_pharmadus_8_18.scripts.migrate_user_signatures import main
main(env, ['--write'])
PY
```

Limitar a usuarios concretos:

```bash
docker compose -f /opt/pharmadus/devel.yaml exec -T odoo \
  odoo shell -d devel --no-http <<'PY'
import sys
sys.path.insert(0, '/opt/odoo/custom/src/private')
from migracion_pharmadus_8_18.scripts.migrate_user_signatures import main
main(env, ['--user-ids', '10,14,15'])
PY
```

## Albaran valorado en clientes

`scripts/migrate_customer_valued_picking.py` marca `valued_picking = True` en todos los partners cliente del Odoo 18 configurado en `target` (`customer_rank > 0`).

El script usa XML-RPC contra el entorno destino y no necesita leer nada desde Odoo 8, aunque reutiliza el mismo `config.json` del paquete.

Simulacion sin escribir cambios:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_customer_valued_picking.py \
  --config migracion_pharmadus_8_18/config.json
```

Escritura real:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_customer_valued_picking.py \
  --config migracion_pharmadus_8_18/config.json \
  --write
```

Limitar volumen para pruebas:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_customer_valued_picking.py \
  --config migracion_pharmadus_8_18/config.json \
  --limit 20
```

Limitar a partners concretos:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_customer_valued_picking.py \
  --config migracion_pharmadus_8_18/config.json \
  --partner-ids 10,14,15
```

## Canales de venta

`scripts/migrate_sale_channels.py` migra los canales de `sale.channel` desde
Odoo 8 y los asigna, cuando existe una coincidencia inequívoca por referencia,
a pedidos, facturas y albaranes de Odoo 18.

El script es idempotente: reutiliza canales con el mismo nombre, no sobrescribe
un canal ya asignado en destino y omite coincidencias ambiguas o inexistentes.
Sin `--write` solo muestra las operaciones previstas.

Simulación limitada:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_sale_channels.py \
  --config migracion_pharmadus_8_18/config.json \
  --limit 20
```

Escritura real, después de realizar un backup:

```bash
python3 migracion_pharmadus_8_18/scripts/migrate_sale_channels.py \
  --config migracion_pharmadus_8_18/config.json \
  --write
```

Se pueden limitar canales o documentos concretos con `--channel-ids`,
`--order-ids`, `--invoice-ids` y `--picking-ids`. Los pedidos se emparejan por
`name`; las facturas usan `number` en Odoo 8 y `name` en Odoo 18; los albaranes
se emparejan por `name`. Los registros que no cumplan una coincidencia única se
informan y no se modifican.

## Líneas de producción

`scripts/create_production_lines.py` replica las **líneas de producción** de Odoo 8.
En SIGI no eran centros de trabajo: eran registros de `mrp.routing` (17 rutas con
código `LIN01`, `FUS01`, `EMS01`…). Odoo 18 ya no tiene ese modelo, así que se crean
como centros de trabajo (`mrp.workcenter`) con el mismo código y nombre, más la
etiqueta de centro de trabajo `Línea de producción` para poder separarlas con un
filtro de las etapas de proceso (Acopio, Acondicionamiento, Fabricación…).

Características:

- El listado de líneas está en el propio script, con el id y las OF históricas de cada
  ruta en Odoo 8 como comentario.
- Es idempotente: empareja por `code`, no duplica y no sobrescribe el nombre de un
  centro existente (también detecta centros archivados).
- Crea los centros con capacidad 1, eficiencia 100 % y coste horario 0, equivalentes a
  los valores que tenían las rutas en Odoo 8.
- Sin `--write` solo informa de lo que haría.

Simulación (contra el destino del `config.json`):

```bash
python3 migracion_pharmadus_8_18/scripts/create_production_lines.py \
  --config migracion_pharmadus_8_18/config.json
```

Escritura real, después de realizar un backup:

```bash
python3 migracion_pharmadus_8_18/scripts/create_production_lines.py \
  --config migracion_pharmadus_8_18/config.json \
  --write
```

Opciones útiles:

- `--codes LIN01,FUS01`: procesa solo esas líneas (comprueba el código antes de escribir).
- `--tag-name "Otra etiqueta"`: cambia el nombre de la etiqueta agrupadora.
- `--no-tag`: crea los centros sin etiqueta.
- `--target-url http://127.0.0.1:18069`: sobrescribe la URL de destino, útil para probar
  contra el proxy local de desarrollo cuando `odoo.pharmadus.com` no es alcanzable.
- `--timeout 60`: timeout de las llamadas XML-RPC.

## Asignar la línea de producción a las BoMs

Odoo 18 **no tiene ningún campo de línea en la BoM** (ni existe `mrp.routing`): el único
sitio donde puede vivir la línea es el **centro de trabajo de las operaciones** de la BoM.
El flujo va en dos fases porque no suele haber conectividad simultánea a SIGI y al Odoo 18.

Fase 1, donde Odoo 8 sea alcanzable: exporta `producto -> primera línea` a un JSON. La
"primera línea" es la de **menor id de `mrp.routing`** en Odoo 8, que es el orden en el que
Odoo devuelve `product.template.routing_ids`.

```bash
python3 migracion_pharmadus_8_18/scripts/export_source_lines_map.py \
  --config migracion_pharmadus_8_18/config.json \
  --out sigi_lines_map.json --write
```

Fase 2, donde Odoo 18 sea alcanzable: apunta las operaciones de cada BoM al centro de
trabajo de la línea de su producto.

```bash
# simulación
python3 migracion_pharmadus_8_18/scripts/assign_production_lines_to_boms.py \
  --config migracion_pharmadus_8_18/config.json --map sigi_lines_map.json

# escritura, guardando fichero de reversión
python3 migracion_pharmadus_8_18/scripts/assign_production_lines_to_boms.py \
  --config migracion_pharmadus_8_18/config.json --map sigi_lines_map.json \
  --write --revert-out /tmp/assign_lines_revert.json
```

Notas:

- Solo se pueden asignar BoMs que **ya tengan operaciones**. Las que no las tengan se
  informan aparte (`boms_sin_operaciones`) y habrá que asignarles la línea cuando se
  migren sus operaciones.
- Con `--write` se guarda un fichero de reversión con el centro de trabajo anterior de
  cada operación tocada, por si hay que deshacer.
- `--target-url` permite apuntar al proxy local de desarrollo cuando el destino del
  `config.json` no sea alcanzable.
- Resultado de la primera pasada en el entorno de desarrollo: 1.462 BoMs activas, 1.368 con
  línea en origen, **7 asignadas** (40 operaciones), 1.361 sin operaciones y 94 BoMs sin
  línea en origen.

