# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class IrModelData(models.Model):
    _inherit = "ir.model.data"

    def _pharmadus_mark_catalog_seed_noupdate(self):
        catalog_models = (
            "pharmadus.product.line",
            "pharmadus.product.subline",
            "pharmadus.product.purchase.line",
            "pharmadus.product.purchase.subline",
            "pharmadus.product.packaging.type",
            "pharmadus.product.base.form",
            "pharmadus.product.garment",
            "pharmadus.product.grouping",
        )
        records = self.search([
            ("module", "=", "pharmadus_base"),
            ("model", "in", catalog_models),
        ])
        records.write({"noupdate": True})
