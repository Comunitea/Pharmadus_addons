# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api
from odoo.exceptions import UserError

class StockLotCreationWizard(models.TransientModel):
    _name = 'stock.lot.creation.wizard'
    _description = 'Stock Lot Creation Wizard'

    # Fields for the wizard
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

    # Reference to the stock move that triggered this wizard
    source_move_id = fields.Many2one(comodel_name='stock.move',
                                    string='Movimiento de origen')

    @api.model
    def _default_product(self):
        """Get the product from the context"""
        if self._context.get('active_model') == 'stock.move' and self._context.get('active_id'):
            move = self.env['stock.move'].browse(self._context['active_id'])
            return move.product_id.id
        return False

    def create_lot_and_assign(self):
        """Create a new lot based on product configuration and assign to source move"""
        if not self.source_move_id:
            raise UserError("No se encontró el movimiento de origen")

        # Create the new lot
        lot_values = {
            'name': self.lot_name,
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
            'pharmadus_packaging_type_id': self.packaging_type_id.id,
            'pharmadus_package_count': self.package_count,
            'pharmadus_pallet_count': self.pallet_count
        }

        # Remove None values to avoid validation errors
        lot_values = {k: v for k, v in lot_values.items() if v is not None}

        new_lot = self.env['stock.lot'].create(lot_values)

        # Assign the lot to the source move
        moves_to_update = self.source_move_id.mapped('move_line_ids').filtered(
            lambda line: not line.lot_id and line.product_id == self.product_id
        )

        if not moves_to_update:
            raise UserError("No se encontraron líneas de movimiento sin lote asignado")

        # Assign the new lot to all matching move lines
        for move_line in moves_to_update:
            move_line.write({'lot_id': new_lot.id})

        return {
            'type': 'ir.actions.act_window_close',
            'res_id': self.source_move_id.id,
        }

    def default_get(self, fields):
        """Set default values based on context"""
        res = super(StockLotCreationWizard, self).default_get(fields)
        if self._context.get('active_model') == 'stock.move' and self._context.get('active_id'):
            move = self.env['stock.move'].browse(self._context['active_id'])
            res.update({
                'source_move_id': move.id,
                'product_id': move.product_id.id
            })
        return res

# Error handling for missing dependencies
class UserError(Exception):
    """Custom user error class"""
    pass
