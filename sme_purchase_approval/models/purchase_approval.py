# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def _read_group_status(self, stages, domain, order):
        status_list = dict(self._fields['state'].selection).keys()
        return status_list

    approver_ids = fields.One2many('purchase.approver', 'order_id', string="Approvers")
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True,
        store = True, compute_sudo = True, )

    user_status = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancel')], compute="_compute_user_status")

    @api.depends('approver_ids.status')
    def _compute_user_status(self):
        for order in self:
            order.user_status = order.approver_ids.filtered(lambda approver: approver.user_id == self.env.user).status


    def _get_user_approval_activities(self, user):
        domain = [
            ('res_model', '=', 'purchase.order'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('sme_purchase_approval.mail_activity_data_approval').id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        return activities


    def button_approve(self, force=False,approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approver.write({'status': 'purchase'})
        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

        status_lst = self.mapped('approver_ids.status')
        approvers = len(status_lst)
        result ={}
        if status_lst.count('purchase') == approvers:
            result = super(PurchaseOrder, self).button_approve(force=force)
        return result

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            approvers = self.mapped('approver_ids').filtered(lambda approver: approver.status in ('draft','sent'))
            approvers._create_activity()
            approvers.write({'status': 'to approve'})
            # Deal with double validation process
            # if order.company_id.po_double_validation == 'one_step'\
            #         or (order.company_id.po_double_validation == 'two_step'\
            #             and order.amount_total < self.env.company.currency_id._convert(
            #                 order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
            #         or order.user_has_groups('purchase.group_purchase_manager'):
            #     order.button_approve()
            # else:
            order.write({'state': 'to approve'})
        return True


class PurchaseApprover(models.Model):
    _name = 'purchase.approver'
    _description = 'Purchase Approver'


    user_id = fields.Many2one('res.users', string="User", required=True)
    name = fields.Char(related='user_id.name')
    status = fields.Selection([
        ('draft', 'New'),
        ('sent', 'New'),
        ('to approve', 'To Approve'),
        ('purchase', 'Approved'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
       ], string="Status", default="draft", readonly=True)
    order_id = fields.Many2one('purchase.order', string="Purchase Order", ondelete='cascade')

    def button_approve(self):
        self.order_id.button_approve(self)

    def action_refuse(self):
        self.order_id.action_refuse(self)

    def action_create_activity(self):
        self.write({'status': 'to approve'})
        self._create_activity()

    def _create_activity(self):
        for approver in self:
            approver.order_id.activity_schedule(
                'sme_purchase_approval.mail_activity_data_approval',
                user_id=approver.user_id.id)

    @api.onchange('user_id')
    def _onchange_approver_ids(self):
        return {'domain': {'user_id': [('id', 'not in', self.order_id.approver_ids.mapped('user_id').ids + self.order_id.user_id.ids)]}}
