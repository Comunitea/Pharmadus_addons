# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    # Keep Odoo's sequence on creation, but allow editing once the record exists.
    name = fields.Char(readonly=False)
