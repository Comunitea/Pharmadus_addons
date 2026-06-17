# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    pharmadus_packaging_type_id = fields.Many2one(
        comodel_name="pharmadus.product.packaging.type",
        string="Tipo de envase",
        ondelete="restrict",
    )
    pharmadus_package_count = fields.Integer(string="Nº de envases")
    pharmadus_pallet_count = fields.Integer(string="Nº de pallets")

    def _prepare_new_lot_vals(self):
        vals = super()._prepare_new_lot_vals()
        if self.pharmadus_packaging_type_id:
            vals["pharmadus_packaging_type_id"] = self.pharmadus_packaging_type_id.id
        if self.pharmadus_package_count:
            vals["pharmadus_package_count"] = self.pharmadus_package_count
        if self.pharmadus_pallet_count:
            vals["pharmadus_pallet_count"] = self.pharmadus_pallet_count
        return vals

    @api.model
    def _pharmadus_get_lot_name_from_sequence(self, product, picking=None):
        if not product or product.tracking == "none" or not product.lot_sequence_id:
            return False
        if picking and picking.picking_type_code != "incoming":
            return False
        return product.lot_sequence_id.next_by_id()

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if "lot_name" not in fields_list or defaults.get("lot_name") or defaults.get("lot_id"):
            return defaults

        product = self.env["product.product"].browse(
            defaults.get("product_id") or self.env.context.get("default_product_id")
        )
        picking = self.env["stock.picking"].browse(
            defaults.get("picking_id") or self.env.context.get("default_picking_id")
        )
        if not picking and (move_id := defaults.get("move_id") or self.env.context.get("default_move_id")):
            picking = self.env["stock.move"].browse(move_id).picking_id

        lot_name = self._pharmadus_get_lot_name_from_sequence(product, picking)
        if lot_name:
            defaults["lot_name"] = lot_name
        return defaults

    @api.onchange("product_id", "picking_id", "move_id")
    def _onchange_pharmadus_lot_name_from_sequence(self):
        for line in self:
            if line.lot_name or line.lot_id:
                continue
            lot_name = line._pharmadus_get_lot_name_from_sequence(
                line.product_id,
                line.picking_id or line.move_id.picking_id,
            )
            if lot_name:
                line.lot_name = lot_name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("lot_name") or vals.get("lot_id"):
                continue
            product = self.env["product.product"].browse(vals.get("product_id"))
            picking = self.env["stock.picking"].browse(vals.get("picking_id"))
            if not picking and vals.get("move_id"):
                picking = self.env["stock.move"].browse(vals["move_id"]).picking_id
            lot_name = self._pharmadus_get_lot_name_from_sequence(product, picking)
            if lot_name:
                vals["lot_name"] = lot_name

        return super().create(vals_list)
