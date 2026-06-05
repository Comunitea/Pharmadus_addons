# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pending_confirmation = fields.Boolean(
        string="Pendiente de confirmar",
        default=False,
    )

    def action_set_pending_confirmation(self):
        self.pending_confirmation = True

    def action_unset_pending_confirmation(self):
        self.pending_confirmation = False

    blocked = fields.Boolean(
        string="Pedido Bloqueado",
        default=False,
    )

    def action_set_blocked(self):
        self.blocked = True
