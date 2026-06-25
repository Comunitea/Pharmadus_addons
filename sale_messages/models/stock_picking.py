# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models

# from odoo.exceptions import RedirectWarning, UserError, ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_message_ids = fields.One2many(
        comodel_name="sale.order.message",
        inverse_name="picking_id",
        compute="_compute_messages_ids",
    )
    sale_message_count = fields.Integer(
        "number of messages", compute="_compute_messages_ids"
    )

    def _compute_messages_ids(self):
        for pick in self:
            pick.sale_message_ids = False
            pick_messages = pick.sale_id.mapped("order_message_ids").filtered(
                lambda r: r.picking_available
            )
            pick.sale_message_ids = pick_messages.ids
            pick.sale_message_count = len(pick_messages)
