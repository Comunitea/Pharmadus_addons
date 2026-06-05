# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Pharmadus Stock Supplier Lot",
    "summary": "Permite registrar el lote de proveedor en recepciones con auto-creación de lote",
    "version": "18.0.1.0.0",
    "category": "Hidden",
    "website": "https://github.com/Ipharmadus/odoo",
    "author": "Pharmadus Botanicals",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["stock_picking_auto_create_lot"],
    "post_init_hook": "post_init_hook",
    "data": [
        "views/stock_move_line_views.xml",
    ],
}
