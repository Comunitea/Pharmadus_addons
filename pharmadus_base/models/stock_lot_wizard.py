# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

class StockLotCreationWizard(models.TransientModel):
    _name = 'stock.lot.creation.wizard'
    _description = 'Stock Lot Creation Wizard'

    lot_name = fields.Char(string='Lote', required=True)
    product_id = fields.Many2one(comodel_name='product.product',
                                string='Producto', required=True,
                                default=lambda self: self._default_product())
    company_id = fields.Many2one(related='product_id.company_id')
    packaging_type_id = fields.Many2one(
        comodel_name="pharmadus.product.packaging.type",
        string="Tipo de envase"
    )
    package_count = fields.Integer(string="Nº de envases")
    pallet_count = fields.Integer(string="Nº de pallets")

    source_move_id = fields.Many2one(comodel_name='stock.move',
                                    string='Movimiento de origen')

    source_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Albarán de origen',
    )

    def _get_default_source_move(self):
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        if not active_id:
            return self.env['stock.move']
        if active_model == 'stock.move':
            return self.env['stock.move'].browse(active_id).exists()
        if active_model == 'stock.picking':
            picking = self.env['stock.picking'].browse(active_id).exists()
            moves = picking.move_ids.filtered(
                lambda move: move.product_id and any(
                    not line.lot_id for line in move.move_line_ids
                )
            )
            return moves[:1]
        return self.env['stock.move']

    @api.constrains('package_count', 'pallet_count')
    def _check_non_negative_counts(self):
        for wizard in self:
            if wizard.package_count < 0:
                raise ValidationError("El número de envases no puede ser negativo.")
            if wizard.pallet_count < 0:
                raise ValidationError("El número de pallets no puede ser negativo.")

    @api.model
    def _default_product(self):
        """Get the product from the context"""
        return self._get_default_source_move().product_id.id or False

    def create_lot_and_assign(self):
        """Create a new lot based on product configuration and assign to source move"""
        if not self.source_move_id:
            raise UserError("No se encontró el movimiento de origen")
        if self.source_move_id.product_id != self.product_id:
            raise UserError("El producto debe coincidir con el movimiento de origen")
        if self.source_picking_id and self.source_picking_id != self.source_move_id.picking_id:
            raise UserError("El albarán debe coincidir con el movimiento de origen")
        if self.source_move_id.picking_id.picking_type_code != 'incoming':
            raise UserError("Solo se pueden crear lotes desde recepciones")

        lot_values = {
            'name': self.lot_name,
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
            'pharmadus_packaging_type_id': self.packaging_type_id.id,
            'pharmadus_package_count': self.package_count,
            'pharmadus_pallet_count': self.pallet_count
        }

        lot_values = {k: v for k, v in lot_values.items() if v is not None}

        new_lot = self.env['stock.lot'].create(lot_values)

        moves_to_update = self.source_move_id.mapped('move_line_ids').filtered(
            lambda line: not line.lot_id and line.product_id == self.product_id
        )

        if not moves_to_update:
            raise UserError("No se encontraron líneas de movimiento sin lote asignado")

        for move_line in moves_to_update:
            move_line.write({'lot_id': new_lot.id})

        return {
            'type': 'ir.actions.act_window_close',
            'res_id': self.source_move_id.id,
        }

    def default_get(self, fields):
        """Set default values based on context"""
        res = super(StockLotCreationWizard, self).default_get(fields)
        move = self._get_default_source_move()
        if move:
            res.update({
                'source_move_id': move.id,
                'source_picking_id': move.picking_id.id,
                'product_id': move.product_id.id,
            })
        return res
