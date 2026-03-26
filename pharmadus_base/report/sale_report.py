# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    pharmadus_line_id = fields.Many2one(
        comodel_name="pharmadus.product.line",
        string="Línea",
        readonly=True,
    )
    pharmadus_subline_id = fields.Many2one(
        comodel_name="pharmadus.product.subline",
        string="SubLínea",
        readonly=True,
    )

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res.update(
            {
                "pharmadus_line_id": "t.pharmadus_line_id",
                "pharmadus_subline_id": "t.pharmadus_subline_id",
            }
        )
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        return f"{res}, t.pharmadus_line_id, t.pharmadus_subline_id"
