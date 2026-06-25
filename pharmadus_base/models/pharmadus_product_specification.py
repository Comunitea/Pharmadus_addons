# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PharmadusCatalogMixin(models.AbstractModel):
    _name = "pharmadus.catalog.mixin"
    _description = "Pharmadus Catalog Mixin"
    _order = "sequence, name, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compañía",
    )


class PharmadusProductLine(models.Model):
    _name = "pharmadus.product.line"
    _description = "Product Line"
    _inherit = "pharmadus.catalog.mixin"

    _sql_constraints = [
        (
            "pharmadus_product_line_name_company_uniq",
            "unique(name, company_id)",
            "No puede haber dos líneas con el mismo nombre en la misma compañía.",
        ),
    ]


class PharmadusProductSubline(models.Model):
    _name = "pharmadus.product.subline"
    _description = "Product Subline"
    _inherit = "pharmadus.catalog.mixin"

    _sql_constraints = [
        (
            "pharmadus_product_subline_name_company_uniq",
            "unique(name, company_id)",
            "No puede haber dos sublíneas con el mismo nombre en la misma compañía.",
        ),
    ]

    line_id = fields.Many2one(
        comodel_name="pharmadus.product.line",
        required=True,
        ondelete="cascade",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        index=True,
    )

    @api.constrains("company_id", "line_id")
    def _check_company_id_line_id(self):
        for record in self:
            if (
                record.company_id
                and record.line_id.company_id
                and record.company_id != record.line_id.company_id
            ):
                raise ValidationError(
                    "La sublínea debe pertenecer a la misma compañía que su línea."
                )


class PharmadusProductPackaging(models.Model):
    _name = "pharmadus.product.packaging.type"
    _description = "Product Packaging Type"
    _inherit = "pharmadus.catalog.mixin"

    _sql_constraints = [
        (
            "pharmadus_product_packaging_type_name_company_uniq",
            "unique(name, company_id)",
            "No puede haber dos envasados con el mismo nombre en la misma compañía.",
        ),
    ]


class PharmadusProductBaseForm(models.Model):
    _name = "pharmadus.product.base.form"
    _description = "Product Base Form"
    _inherit = "pharmadus.catalog.mixin"

    _sql_constraints = [
        (
            "pharmadus_product_base_form_name_company_uniq",
            "unique(name, company_id)",
            "No puede haber dos formas base con el mismo nombre en la misma compañía.",
        ),
    ]


class PharmadusProductGarment(models.Model):
    _name = "pharmadus.product.garment"
    _description = "Product Garment"
    _inherit = "pharmadus.catalog.mixin"

    _sql_constraints = [
        (
            "pharmadus_product_garment_name_company_uniq",
            "unique(name, company_id)",
            "No puede haber dos vestimentas con el mismo nombre en la misma compañía.",
        ),
    ]


class PharmadusProductPurchaseLine(models.Model):
    _name = "pharmadus.product.purchase.line"
    _description = "Purchase Product Line"
    _inherit = "pharmadus.catalog.mixin"

    _sql_constraints = [
        (
            "pharmadus_product_purchase_line_name_company_uniq",
            "unique(name, company_id)",
            "No puede haber dos líneas de compras con el mismo nombre en la misma compañía.",
        ),
    ]


class PharmadusProductPurchaseSubline(models.Model):
    _name = "pharmadus.product.purchase.subline"
    _description = "Purchase Product Subline"
    _inherit = "pharmadus.catalog.mixin"

    _sql_constraints = [
        (
            "pharmadus_product_purchase_subline_name_company_uniq",
            "unique(name, company_id)",
            "No puede haber dos sublíneas de compras con el mismo nombre en la misma compañía.",
        ),
    ]

    line_id = fields.Many2one(
        comodel_name="pharmadus.product.purchase.line",
        required=True,
        ondelete="cascade",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        index=True,
    )

    @api.constrains("company_id", "line_id")
    def _check_company_id_line_id(self):
        for record in self:
            if (
                record.company_id
                and record.line_id.company_id
                and record.company_id != record.line_id.company_id
            ):
                raise ValidationError(
                    "La sublínea de compras debe pertenecer a la misma compañía que su línea."
                )


class PharmadusProductGrouping(models.Model):
    _name = "pharmadus.product.grouping"
    _description = "Product Grouping"
    _inherit = "pharmadus.catalog.mixin"

    _sql_constraints = [
        (
            "pharmadus_product_grouping_name_company_uniq",
            "unique(name, company_id)",
            "No puede haber dos agrupaciones con el mismo nombre en la misma compañía.",
        ),
    ]
