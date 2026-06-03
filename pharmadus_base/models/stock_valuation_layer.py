# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    pharmadus_quantity = fields.Integer(
        related="product_id.product_tmpl_id.pharmadus_quantity",
        string="Cantidad",
        store=True,
        readonly=True,
    )
    pharmadus_elements_per_outer_box = fields.Integer(
        related="product_id.product_tmpl_id.pharmadus_elements_per_outer_box",
        string="Elementos por caja contenedora",
        store=True,
        readonly=True,
    )
    pharmadus_elements_per_display_box = fields.Integer(
        related="product_id.product_tmpl_id.pharmadus_elements_per_display_box",
        string="Elementos por caja expositora",
        store=True,
        readonly=True,
    )
    pharmadus_elements_per_full_box = fields.Integer(
        related="product_id.product_tmpl_id.pharmadus_elements_per_full_box",
        string="Elementos por caja (Completo)",
        store=True,
        readonly=True,
    )
    pharmadus_line_id = fields.Many2one(
        related="product_id.product_tmpl_id.pharmadus_line_id",
        string="Línea",
        store=True,
        readonly=True,
        index=True,
    )
    pharmadus_subline_id = fields.Many2one(
        related="product_id.product_tmpl_id.pharmadus_subline_id",
        string="SubLínea",
        store=True,
        readonly=True,
        index=True,
    )
    pharmadus_packaging_type_id = fields.Many2one(
        related="product_id.product_tmpl_id.pharmadus_packaging_type_id",
        string="Envasado",
        store=True,
        readonly=True,
        index=True,
    )
    pharmadus_base_form_id = fields.Many2one(
        related="product_id.product_tmpl_id.pharmadus_base_form_id",
        string="Forma base",
        store=True,
        readonly=True,
        index=True,
    )
    pharmadus_garment_id = fields.Many2one(
        related="product_id.product_tmpl_id.pharmadus_garment_id",
        string="Vestimenta",
        store=True,
        readonly=True,
        index=True,
    )
    pharmadus_purchase_line_id = fields.Many2one(
        related="product_id.product_tmpl_id.pharmadus_purchase_line_id",
        string="Línea compras",
        store=True,
        readonly=True,
        index=True,
    )
    pharmadus_purchase_subline_id = fields.Many2one(
        related="product_id.product_tmpl_id.pharmadus_purchase_subline_id",
        string="Sublínea compras",
        store=True,
        readonly=True,
        index=True,
    )
    pharmadus_grouping_id = fields.Many2one(
        related="product_id.product_tmpl_id.pharmadus_grouping_id",
        string="Agrupación",
        store=True,
        readonly=True,
        index=True,
    )
    pharmadus_subgrouping = fields.Char(
        related="product_id.product_tmpl_id.pharmadus_subgrouping",
        string="Subagrupación",
        store=True,
        readonly=True,
    )
