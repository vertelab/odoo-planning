from odoo import models, fields, api, _
from datetime import date


class Activities(models.Model):
    _inherit = 'mail.activity'

    @api.depends("res_model")
    def _set_hours(self):
        for rec in self:
            if rec.res_model == 'project.task':
                task_id = self.env[rec.res_model].browse(rec.res_id)
                rec.planned_hours = task_id.planned_hours
            else:
                rec.planned_hours = 0

    def _inverse_hours(self):
        pass

    planned_hours = fields.Float(string="Planned Hours", compute=_set_hours, inverse=_inverse_hours, store=True)

    planned_hours_test = fields.Integer(default=10)

    expected_revenue = fields.Monetary('Expected Revenue', currency_field='company_currency', tracking=True, default=10000)

    company_currency = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id,
                                       readonly=True)

    def action_view_activity_tasks(self):
        return {
            'view_mode': 'form',
            'res_model': self.res_model,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.res_id,
            'views': [[False, 'form']]
        }
