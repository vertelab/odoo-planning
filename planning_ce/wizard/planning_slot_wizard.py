from odoo import models, fields, api, _


class SlotWizard(models.Model):
    _name = 'planner_ce.slot.wizard'

    def action_set_request(self):
        active_ids = self._context.get('active_ids')
        for _rec in active_ids:
            record_id = self.env[self._context.get('active_model')].search([('id', '=', _rec)])
            record_id.state = 'requested'
