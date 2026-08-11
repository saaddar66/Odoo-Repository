from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Approval State', default='draft', copy=False, tracking=True)

    is_manual_bill = fields.Boolean(
        string='Is Manual Bill',
        compute='_compute_is_manual_bill',
        store=True,
    )

    @api.depends('move_type', 'invoice_origin')
    def _compute_is_manual_bill(self):
        # We don't depend on purchase_id in api.depends to avoid registry issues if purchase is delayed
        # but we check it inside.
        for move in self:
            if move.move_type == 'in_invoice':
                # purchase_id is added by the 'purchase' module. 
                # Since 'purchase' is in depends, it's safe to use getattr or check move.purchase_id
                p_id = getattr(move, 'purchase_id', False)
                if not p_id and not move.invoice_origin:
                    move.is_manual_bill = True
                else:
                    move.is_manual_bill = False
            else:
                move.is_manual_bill = False

    def action_submit_for_approval(self):
        for move in self:
            if move.state != 'draft':
                raise UserError(_('Only draft bills can be submitted for approval.'))
            if not move.is_manual_bill:
                raise UserError(_('Only manual vendor bills require approval.'))
            move.approval_state = 'pending'

    def action_approve(self):
        for move in self:
            if move.approval_state != 'pending':
                raise UserError(_('Only pending bills can be approved.'))
            move.approval_state = 'approved'

    def action_reject(self):
        for move in self:
            if move.approval_state != 'pending':
                raise UserError(_('Only pending bills can be rejected.'))
            move.approval_state = 'rejected'

    def action_post(self):
        for move in self:
            if move.move_type == 'in_invoice' and move.is_manual_bill and move.approval_state != 'approved':
                raise UserError(_("You cannot post a manual vendor bill that has not been approved."))
        return super().action_post()
