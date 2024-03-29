from odoo import api, fields, models, _
import logging
from datetime import date

_logger = logging.getLogger(__name__)


class Task(models.Model):
    _inherit = "project.task"

    assigned_user = fields.Many2one('day.plan', string='Assigned User')


class DayPlan(models.Model):
    _name = "day.plan"
    _description = "Daily Planner"
    _rec_name = 'date'
    _order = 'user_id, date'

    @api.depends('activity_ids')  # TODO: What happens if the activity_ids is updated!
    def _compute_planned_hours(self):
        for record in self:
            if record.activity_ids:
                record.planned_hours = sum(record.activity_ids.mapped('planned_hours'))
            else:
                record.planned_hours = 0

    user_id = fields.Many2one('res.users', string='User')
    date = fields.Date('Date')
    task_ids = fields.One2many('project.task', 'assigned_user', string='Tasks')
    planned_hours = fields.Float('Planned Hours', compute=_compute_planned_hours)

    @api.depends('user_id', 'date')
    def _set_activity_users(self):
        for rec in self:
            if rec.user_id and rec.date:
                activity_ids = self.env['mail.activity'].search([
                    ('user_id', '=', rec.user_id.id),
                    ('res_model', '=', 'project.task'),
                    ('date_deadline', '=', rec.date)])
                if activity_ids:
                    rec.activity_ids = activity_ids.ids
                else:
                    rec.activity_ids = False
            else:
                rec.activity_ids = False

    activity_ids = fields.Many2many('mail.activity', 'daily_planner_activity_rel', string='Mail Activity',
                                    readonly=True, compute=_set_activity_users)

    @api.depends('date')
    def _set_week_day(self):
        for rec in self:
            if rec.date:
                rec.date_weekday = rec.date.strftime('%A')
            else:
                rec.date_weekday = False

    date_weekday = fields.Char('Week Day', compute=_set_week_day)
