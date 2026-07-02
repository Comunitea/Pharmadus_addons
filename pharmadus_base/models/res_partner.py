# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        is_customer_context = (
            self.env.context.get("res_partner_search_mode") == "customer"
            or self.env.context.get("default_customer_rank")
        )
        if not is_customer_context:
            return partners

        partners_to_mark = self.browse()
        for partner, vals in zip(partners, vals_list):
            if "valued_picking" in vals:
                continue
            if partner.customer_rank > 0 and not partner.valued_picking:
                partners_to_mark |= partner

        if partners_to_mark:
            partners_to_mark.valued_picking = True
        return partners
