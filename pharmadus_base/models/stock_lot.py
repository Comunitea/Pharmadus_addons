# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import math

from odoo import fields, models


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
        if not package_count:
            return 1
        if not self._pharmadus_is_sampling_label_case():
            return package_count
        # Mantiene la lógica histórica: envases + etiquetas de muestreo.
        return package_count + math.ceil(math.sqrt(package_count)) + 1
