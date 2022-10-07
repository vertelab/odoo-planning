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

    planned_hours = fields.Float('Planned Hours', tracking=True, compute=_set_hours, inverse=_inverse_hours, store=True)

    def action_view_activity_tasks(self):
        return {
            'view_mode': 'form',
            'res_model': self.res_model,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.res_id,
            'views': [[False, 'form']]
        }

    @api.model
    def create(self, values):
        res = super(Activities, self).create(values)

        day_plan_id = self.env['day.plan'].search([
            ('user_id', '=', res.user_id.id),
            ('date', '=', res.date_deadline)
        ], limit=1)

        if not day_plan_id:
            self.env['day.plan'].create({
                'user_id': res.user_id.id, 'date': res.date_deadline
            })
        return res
