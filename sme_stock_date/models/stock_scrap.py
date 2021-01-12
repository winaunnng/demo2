# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,exceptions, _



class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    date_done = fields.Datetime('Date', readonly=False)

    # new constrains
    @api.constrains('date_done')
    def _check_validity_date_done(self):
        for scrap in self:
            if scrap.date_done > fields.Datetime.now() :
                raise exceptions.ValidationError(_('"Date" must be earlier than the current date.'))

    # inherit original function , myh@smeintellect.com
    def do_scrap(self):
        self._check_company()
        for scrap in self:
            scrap.name = self.env['ir.sequence'].next_by_code('stock.scrap') or _('New')
            move = self.env['stock.move'].create(scrap._prepare_move_values())
            # master: replace context by cancel_backorder
            move.with_context(is_scrap=True,force_period_date=scrap.date_done)._action_done() # add new context 'force_period_date' by myh@smeintellect.com
            scrap.write({'move_id': move.id, 'state': 'done'})
            # scrap.date_done = fields.Datetime.now() # block by myh@smeintellect.com
        return True