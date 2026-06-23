# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    pharmadus_signature_image = fields.Binary(
        string="Firma manuscrita",
        attachment=True,
    )
