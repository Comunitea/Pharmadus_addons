# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools.sql import SQL


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    pharmadus_purchase_line_id = fields.Many2one(
        comodel_name="pharmadus.product.purchase.line",
        string="Línea compras",
        readonly=True,
    )
    pharmadus_purchase_subline_id = fields.Many2one(
        comodel_name="pharmadus.product.purchase.subline",
        string="Sublínea compras",
        readonly=True,
    )

    def _select(self) -> SQL:
        return SQL(
            "%s, t.pharmadus_purchase_line_id AS pharmadus_purchase_line_id, "
            "t.pharmadus_purchase_subline_id AS pharmadus_purchase_subline_id",
            super()._select(),
        )

    def _group_by(self) -> SQL:
        return SQL(
            "%s, t.pharmadus_purchase_line_id, t.pharmadus_purchase_subline_id",
            super()._group_by(),
        )
