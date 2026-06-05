# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Actualiza la etiqueta del campo ref de stock.lot a 'Lote de proveedor' en es_ES."""
    field = env["ir.model.fields"].search(
        [("model", "=", "stock.lot"), ("name", "=", "ref")], limit=1
    )
    if field:
        field.with_context(lang="es_ES").field_description = "Lote de proveedor"
