# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Pharmadus Base",
    "summary": "Base module for Pharmadus-specific customizations",
    "version": "18.0.1.0.0",
    "category": "Hidden",
    "website": "https://github.com/Ipharmadus/odoo",
    "author": "Ipharmadus",
    "license": "AGPL-3",
    "depends": ["base", "mail", "sale", "purchase", "stock", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/pharmadus_product_specification_views.xml",
        "views/product_template_views.xml",
        "views/report_views.xml",
        "data/pharmadus.product.line.csv",
        "data/pharmadus.product.subline.csv",
        "data/pharmadus.product.purchase.line.csv",
        "data/pharmadus.product.purchase.subline.csv",
        "data/pharmadus.product.packaging.type.csv",
        "data/pharmadus.product.base.form.csv",
        "data/pharmadus.product.grouping.csv",
        "data/pharmadus_product_specification_data.xml",
    ],
    "installable": True,
    "application": False,
}
