from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class HrExpense(models.Model):
    _inherit = "hr.expense"

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'To Approve'),
        ('approved', 'Approved'),
        ('done', 'Paid'),
        ('refused', 'Refused')
    ], compute='_compute_state', string='Status', copy=False, index=True, readonly=True, store=True,
        help="Status of the expense.")


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'To Approve'),
        ('approve', 'Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('cancel', 'Refused')
    ], string='Status', index=True, readonly=True, tracking=True, copy=False, default='draft', required=True,
        help='Expense Report State')
    approver_ids = fields.One2many('hr.expense.approver', 'sheet_id', string="Approvers")
    user_status = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'To Approve'),
        ('approve', 'Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('cancel', 'Refused')], compute="_compute_user_status")

    @api.depends('approver_ids.status')
    def _compute_user_status(self):
        for sheet in self:
            sheet.user_status = sheet.approver_ids.filtered(lambda approver: approver.user_id == self.env.user).status

    def action_submit_sheet(self):
        self.write({'state': 'submit'})
        approvers = self.mapped('approver_ids').filtered(lambda approver: approver.status in ('draft', 'sent'))
        if approvers:
            approvers._create_activity()
            approvers.write({'status': 'submit'})
        else:
            self.activity_update()

    def _get_user_approval_activities(self, user):
        domain = [
            ('res_model', '=', 'hr.expense.sheet'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('sme_expense_approval.mail_activity_data_expense_approval').id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        return activities


    def approve_expense_sheets(self,approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        if self.approver_ids:
            approver.write({'status': 'approve'})
            self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

            status_lst = self.mapped('approver_ids.status')
            approvers = len(status_lst)
            result = {}
            if status_lst.count('approve') == approvers:
                responsible_id = self.user_id.id or self.env.user.id
                self.write({'state': 'approve', 'user_id': responsible_id})
            return result
        else:
            if not self.user_has_groups('hr_expense.group_hr_expense_team_approver'):
                raise UserError(_("Only Managers and HR Officers can approve expenses"))
            elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
                current_managers = self.employee_id.expense_manager_id | self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id

                if self.employee_id.user_id == self.env.user:
                    raise UserError(_("You cannot approve your own expenses"))

                if not self.env.user in current_managers and not self.user_has_groups('hr_expense.group_hr_expense_user') and self.employee_id.expense_manager_id != self.env.user:
                    raise UserError(_("You can only approve your department expenses"))

            responsible_id = self.user_id.id or self.env.user.id
            self.write({'state': 'approve', 'user_id': responsible_id})
            self.activity_update()

    def refuse_sheet(self, reason,approver= None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        if approver:
            approver.write({'status': 'cancel'})
            self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()
            status_lst = self.mapped('approver_ids.status')
            approvers = len(status_lst)
            if status_lst.count('cancel') == approvers:
                self.write({'state': 'cancel'})

        else:
            if not self.user_has_groups('hr_expense.group_hr_expense_team_approver'):
                raise UserError(_("Only Managers and HR Officers can approve expenses"))
            elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
                current_managers = self.employee_id.expense_manager_id | self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id
                if self.employee_id.user_id == self.env.user:
                    raise UserError(_("You cannot refuse your own expenses"))
                if not self.env.user in current_managers and not self.user_has_groups('hr_expense.group_hr_expense_user') and self.employee_id.expense_manager_id != self.env.user:
                    raise UserError(_("You can only refuse your department expenses"))
            self.write({'state': 'cancel'})
            self.activity_update()

        for sheet in self:
            sheet.message_post_with_view('hr_expense.hr_expense_template_refuse_reason',
                                         values={'reason': reason, 'is_sheet': True, 'name': self.name})


class HrExpenseApprover(models.Model):
    _name = 'hr.expense.approver'
    _description = 'Expense Approver'

    user_id = fields.Many2one('res.users', string="User", required=True)
    name = fields.Char(related='user_id.name')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'To Approve'),
        ('approve', 'Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('cancel', 'Refused')
    ], string="Status", default="draft", readonly=True)
    sheet_id = fields.Many2one('hr.expense.sheet', string="Expense Sheet", ondelete='cascade')

    def button_approve(self):
        self.sheet_id.button_approve(self)

    def action_refuse(self):
        self.sheet_id.action_refuse(self)

    def action_create_activity(self):
        self.write({'status': 'submit'})
        self._create_activity()

    def _create_activity(self):
        for approver in self:
            approver.sheet_id.activity_schedule(
                'sme_expense_approval.mail_activity_data_expense_approval',
                user_id=approver.user_id.id)

    @api.onchange('user_id')
    def _onchange_approver_ids(self):
        return {'domain': {'user_id': [
            ('id', 'not in', self.sheet_id.approver_ids.mapped('user_id').ids + self.sheet_id.user_id.ids)]}}
