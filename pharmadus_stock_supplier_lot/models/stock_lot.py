# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    ref = fields.Char(string="Lote de proveedor")
