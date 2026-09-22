# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductDisplayName(TransactionCase):

    def test_product_display_name_uses_name_before_reference(self):
        product = self.env["product.product"].create(
            {"name": "Product Test Name", "default_code": "PTN"}
        )

        self.assertEqual(product.display_name, "Product Test Name [PTN]")
        self.assertEqual(
            product.product_tmpl_id.display_name, "Product Test Name [PTN]"
        )
        self.assertEqual(
            product.with_context(display_default_code=False).display_name,
            "Product Test Name",
        )