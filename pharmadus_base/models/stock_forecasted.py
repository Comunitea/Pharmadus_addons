# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockForecasted(models.AbstractModel):
    _inherit = "stock.forecasted_product_product"

    def _get_forecast_document_data(self, document):
        if not document:
            return False

        document_data = {
            "_name": document._name,
            "id": document.id,
            "name": document.display_name,
        }
        if "partner_id" in document._fields and document.partner_id:
            document_data["partner_name"] = document.partner_id.display_name
        if document._name == "mrp.production" and "product_id" in document._fields and document.product_id:
            document_data["product_name"] = document.product_id.display_name
        return document_data

    def _add_purchase_partner_fallback(self, document_data, move):
        if not document_data or document_data.get("partner_name"):
            return document_data
        if not move:
            return document_data

        purchase_order = move.purchase_line_id.order_id
        if purchase_order and purchase_order.partner_id:
            document_data["partner_name"] = purchase_order.partner_id.display_name
        return document_data

    def _prepare_report_line(
        self,
        quantity,
        move_out=None,
        move_in=None,
        replenishment_filled=True,
        product=False,
        reserved_move=False,
        in_transit=False,
        read=True,
    ):
        line = super()._prepare_report_line(
            quantity,
            move_out=move_out,
            move_in=move_in,
            replenishment_filled=replenishment_filled,
            product=product,
            reserved_move=reserved_move,
            in_transit=in_transit,
            read=read,
        )

        if move_in:
            document_in = move_in.sudo()._get_source_document()
            line["document_in"] = self._add_purchase_partner_fallback(
                self._get_forecast_document_data(document_in),
                move_in,
            )

        if move_out:
            document_out = move_out.sudo()._get_source_document()
            line["document_out"] = self._add_purchase_partner_fallback(
                self._get_forecast_document_data(document_out),
                move_out,
            )

        return line
