# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.depends("name", "default_code", "product_tmpl_id")
    @api.depends_context(
        "display_default_code", "seller_id", "company_id", "partner_id", "lang"
    )
    def _compute_display_name(self):
        super()._compute_display_name()
        if not self.env.context.get("display_default_code", True):
            return
        for product in self:
            prefix = f"[{product.default_code}] "
            if product.default_code and product.display_name.startswith(prefix):
                product.display_name = (
                    f"{product.display_name[len(prefix):]} [{product.default_code}]"
                )