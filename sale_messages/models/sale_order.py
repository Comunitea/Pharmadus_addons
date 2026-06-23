# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models

# from odoo.exceptions import RedirectWarning, UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    order_message_ids = fields.One2many(
        comodel_name="sale.order.message", inverse_name="sale_id", string="Order Messages"
    )
