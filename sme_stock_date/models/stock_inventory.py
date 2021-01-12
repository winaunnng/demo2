# -*- coding: utf-8 -*-
from odoo import api, fields, models,exceptions, _

class Inventory(models.Model):
    _inherit = "stock.inventory"

    date = fields.Datetime(
        'Inventory Date',
        readonly=False, required=True,
        default=fields.Datetime.now,
        help="If the inventory adjustment is not validated, date at which the theoritical quantities have been checked.\n"
             "If the inventory adjustment is validated, date at which the inventory adjustment has been validated.")

    # new constrains
    @api.constrains('date')
    def _check_validity_date(self):
        for inv in self:
            if inv.date > fields.Datetime.now() :
                raise exceptions.ValidationError(_('"Inventory Date" must be earlier than the current date.'))


    # inherit original function
    def _action_start(self):
        """ Confirms the Inventory Adjustment and generates its inventory lines
        if its state is draft and don't have already inventory lines (can happen
        with demo data or tests).
        """
        for inventory in self:
            if inventory.state != 'draft':
                continue
            vals = {
                'state': 'confirm',
                # 'date': fields.Datetime.now() # block by myh@smeintellect.com
            }
            if not inventory.line_ids and not inventory.start_empty:
                self.env['stock.inventory.line'].create(inventory._get_inventory_lines_values())
            inventory.write(vals)