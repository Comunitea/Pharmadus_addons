from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_invoiced_lot_values(self):
        lot_values = super()._get_invoiced_lot_values()
        lots = self.env["stock.lot"].sudo().browse(
            [lot_value["lot_id"] for lot_value in lot_values if lot_value.get("lot_id")]
        )
        lots_by_id = {lot.id: lot for lot in lots}
        pos_lot_ids = [
            lot_value["pos_lot_id"] for lot_value in lot_values
            if lot_value.get("pos_lot_id")
        ]
        pos_lots_by_id = {}
        stock_lots_by_product_and_name = {}
        if pos_lot_ids:
            pos_lots = self.env["pos.pack.operation.lot"].sudo().browse(pos_lot_ids)
            stock_lots = self.env["stock.lot"].sudo().search([
                ("name", "in", pos_lots.mapped("lot_name")),
                ("product_id", "in", pos_lots.mapped("product_id").ids),
            ])
            pos_lots_by_id = {pos_lot.id: pos_lot for pos_lot in pos_lots}
            stock_lots_by_product_and_name = {
                (stock_lot.product_id.id, stock_lot.name): stock_lot
                for stock_lot in stock_lots
            }

        for lot_value in lot_values:
            lot_value.setdefault("product_id", False)
            lot_value.setdefault("use_date", False)
            lot = lots_by_id.get(lot_value.get("lot_id"))
            if lot:
                lot_value.update({
                    "product_id": lot.product_id.id,
                    "use_date": lot.use_date,
                })
                continue

            pos_lot = pos_lots_by_id.get(lot_value.get("pos_lot_id"))
            if pos_lot:
                stock_lot = stock_lots_by_product_and_name.get(
                    (pos_lot.product_id.id, pos_lot.lot_name)
                )
                lot_value.update({
                    "product_id": pos_lot.product_id.id,
                    "use_date": stock_lot.use_date if stock_lot else False,
                })
        return lot_values