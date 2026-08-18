# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPharmadusAccountInvoiceReport(TransactionCase):

    def setUp(self):
        super().setUp()
        income_account = self.env["account.account"].sudo().search([
            ("account_type", "=", "income"),
        ], limit=1)
        self.assertTrue(income_account)
        self.partner = self.env["res.partner"].sudo().create({
            "name": "Invoice Partner",
        })
        self.shipping_address = self.env["res.partner"].sudo().create({
            "name": "Delivery Address",
            "parent_id": self.partner.id,
            "type": "delivery",
        })
        product = self.env["product.product"].sudo().create({
            "name": "Invoice Analysis Product",
            "property_account_income_id": income_account.id,
        })
        self.invoice = self.env["account.move"].sudo().create({
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [
                (0, 0, {
                    "product_id": product.id,
                    "account_id": income_account.id,
                    "quantity": 1,
                    "price_unit": 100,
                }),
            ],
        })

    def test_invoice_report_partner_fields(self):
        report = self.env["account.invoice.report"].sudo().search([
            ("move_id", "=", self.invoice.id),
        ])

        self.assertEqual(len(report), 1)
        self.assertEqual(report.partner_shipping_id, self.invoice.partner_shipping_id)
        self.assertEqual(report.commercial_partner_id, self.partner)

        groups = self.env["account.invoice.report"].sudo().read_group(
            [("move_id", "=", self.invoice.id)],
            ["partner_shipping_id"],
            ["partner_shipping_id"],
        )
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["partner_shipping_id"][0], self.shipping_address.id)