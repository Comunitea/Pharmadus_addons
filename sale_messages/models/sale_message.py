# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models

# from odoo.exceptions import RedirectWarning, UserError, ValidationError


class SaleOrderMessage(models.Model):
    _name = "sale.order.message"
    _description = "Mensaje de ventas"

    _order = "date DESC"

    content = fields.Text("Content", required=True)
    datas = fields.Binary("File")
    picking_available = fields.Boolean("Available in pickings", default=True)
    invoice_available = fields.Boolean("Available in invoices", default=True)
    date = fields.Date("Date", required=True, default=fields.Date.context_today)
    sale_id = fields.Many2one(comodel_name="sale.order", string="Sale Order")
    picking_id = fields.Many2one(comodel_name="stock.picking")
    invoice_id = fields.Many2one(comodel_name="account.move")
