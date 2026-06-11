# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Pharmadus Custom",
    "summary": "Personalizaciones menores de la interfaz para Pharmadus",
    "version": "18.0.1.0.0",
    "category": "Hidden",
    "author": "Pharmadus Botanicals",
    "license": "AGPL-3",
    "depends": [
        "sale",
        "stock",
    ],
    "data": [
        "views/sale_order_views.xml",
        "views/stock_lot_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
