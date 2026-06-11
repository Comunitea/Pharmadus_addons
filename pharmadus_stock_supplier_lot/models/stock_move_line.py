# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    supplier_lot_ref = fields.Char(string="Lote de proveedor")

    def _prepare_new_lot_vals(self):
        vals = super()._prepare_new_lot_vals()
        if self.supplier_lot_ref:
            vals["ref"] = self.supplier_lot_ref
        return vals
