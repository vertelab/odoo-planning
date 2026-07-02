# -*- coding: utf-8 -*-

from odoo import models, api, fields
#from dateutil.relativedelta import relativedelta
from datetime import date
import logging
_logger = logging.getLogger(__name__)


class Task(models.Model):
    _inherit = "project.task"

    def planner_wizard_object(self):
        view_id = self.env.ref('planning_day_tasks.planner_wizard').id
        action = {
                "type": "ir.actions.act_window",
                "name": "Assign date to task",
                "view_mode": "form",
                "res_model": 'planner.wizard',
                "target": "new",
                "view_id":view_id,
            }
        action["context"] = {
            'default_user_id':self.user_id.id,
            'default_planned_hours':self.planned_hours,
            'default_task':self.id
        }
        return action


class PlannerWizard(models.TransientModel):
    _name = 'planner.wizard'

    user_id = fields.Many2one('res.users', string='Assigned to')
    date = fields.Date('Date')
    planned_hours = fields.Float('Planned Hours')
    remaining_hours = fields.Float('Remaining Hours')
    task = fields.Many2one('project.task', string='Tasks')

    @api.model
    def create(self, vals):
        _logger.warning("planner.wizard's create is run.")
        res = super().create(vals)
        for rec in res:
            vals_list = {
                'user_id': rec.user_id.id,
                'date': rec.date,
                'colum_date': date.strftime(rec.date, "%Y-%m-%d")
            }

            found_record = self.env['day.plan'].search([
                ('user_id','=',rec.user_id.id),
                ('date', '=', rec.date)
                ],limit=1)

            _logger.warning(f"{found_record=}")
            _logger.warning(f"{len(found_record)=}")
            if len(found_record):
                found_record.write({'task_ids':[(4, rec.task.id)]})
            else:
                vals_list['task_ids'] = rec.task
                self.env['day.plan'].create(vals_list)
        return res