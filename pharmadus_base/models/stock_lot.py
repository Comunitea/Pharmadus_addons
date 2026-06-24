# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval


class StockLot(models.Model):
    _inherit = "stock.lot"

    pharmadus_packaging_type_id = fields.Many2one(
        comodel_name="pharmadus.product.packaging.type",
        string="Tipo de envase",
        ondelete="restrict",
    )
    pharmadus_package_count = fields.Integer(
        string="Nº de envases",
    )
    pharmadus_pallet_count = fields.Integer(
        string="Nº de pallets",
    )

    def _pharmadus_is_sampling_label_case(self):
        self.ensure_one()
        packaging_type = self.pharmadus_packaging_type_id
        if not packaging_type:
            return False

        sampling_packaging_xmlids = (
            "pharmadus_base.pharmadus_packaging_saco_s",
            "pharmadus_base.pharmadus_packaging_bolsa_s",
            "pharmadus_base.pharmadus_packaging_caja_s",
        )
        sampling_packaging_ids = {
            record.id
            for xmlid in sampling_packaging_xmlids
            if (record := self.env.ref(xmlid, raise_if_not_found=False))
        }
        if packaging_type.id not in sampling_packaging_ids:
            return False

        category_name = (self.product_id.categ_id.complete_name or "").lower()
        return "materia prima" in category_name

    def _pharmadus_get_labels_to_print(self):
        self.ensure_one()
        package_count = max(self.pharmadus_package_count or 0, 0)
        pallet_count = max(self.pharmadus_pallet_count or 0, 0)
        labels = [
            {
                "display": f"{index} de {package_count}",
            }
            for index in range(1, package_count + 1)
        ]
        labels.extend(
            {
                "display": "PALET",
            }
            for _ in range(pallet_count)
        )
        return labels

    def _pharmadus_get_move_history_domain(self, lot_ids=None):
        lot_ids = lot_ids or self.ids
        return [
            ("lot_id", "in", lot_ids),
            ("state", "=", "done"),
            "|",
            ("picking_id", "=", False),
            ("picking_id.picking_type_id.code", "!=", "internal"),
        ]

    def action_open_pharmadus_move_history(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.stock_move_line_action"
        )
        action["domain"] = self._pharmadus_get_move_history_domain(lot_ids=[self.id])
        base_action_context = action.get("context", {})
        if isinstance(base_action_context, str):
            base_action_context = safe_eval(base_action_context, {})
        action_context = dict(self.env.context)
        action_context.update(base_action_context)
        action_context.update(
            {
                "search_default_done": 1,
                "default_lot_id": self.id,
            }
        )
        action["context"] = action_context
        return action
