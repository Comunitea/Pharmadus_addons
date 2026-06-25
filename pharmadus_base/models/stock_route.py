# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockRoute(models.Model):
    _inherit = "stock.route"

    pharmadus_auto_approve_lot = fields.Boolean(string="Aprobado automático de lote")
