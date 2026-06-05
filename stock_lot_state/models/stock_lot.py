from odoo import _, api, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    state = fields.Selection(
        selection=[
            ("pending", "Pendiente"),
            ("approved", "Aprobado"),
            ("rejected", "Rechazado"),
        ],
        string="State",
        default="pending",
        tracking=True,
        copy=False,
        help="Estado del lote. Pendiente: editable. Aprobado/Rechazado: solo lectura.",
    )
    approved_by = fields.Many2one(
        comodel_name="res.users",
        string="Aprobado por",
        readonly=True,
        copy=False,
        help="Usuario que aprobó este lote",
    )
    approved_date = fields.Datetime(
        string="Fecha de aprobación",
        readonly=True,
        copy=False,
        help="Fecha en la que se aprobó este lote",
    )

    def _set_locked(self, locked):
        """Set the locked field bypassing the permission check."""
        self.with_context(bypass_lock_permission_check=True).write(
            {"locked": locked}
        )

    def action_set_pending(self):
        """Set lot state to pending and unlock if it was locked."""
        for lot in self:
            vals = {
                "state": "pending",
                "approved_by": False,
                "approved_date": False,
            }
            lot.write(vals)
            if lot.locked:
                lot._set_locked(False)

    def action_set_approved(self):
        """Set lot state to approved, record who and when, and unlock if locked."""
        for lot in self:
            lot.write({
                "state": "approved",
                "approved_by": self.env.user.id,
                "approved_date": fields.Datetime.now(),
            })
            if lot.locked:
                lot._set_locked(False)

    def action_set_rejected(self):
        """Set lot state to rejected, clear approval data and lock the lot."""
        for lot in self:
            lot.write({
                "state": "rejected",
                "approved_by": False,
                "approved_date": False,
            })
            if not lot.locked:
                lot._set_locked(True)
