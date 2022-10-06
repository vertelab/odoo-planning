from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
# import datetime
from datetime import date

class Task(models.Model):
    _inherit = "project.task"

    assigned_user = fields.Many2one('day.plan', string='Assigned User')

class DayPlan(models.Model):
    _name = "day.plan"

    @api.onchange('task_ids') #TODO: What happens if the task estimated time change?!
    def _compute_planned_hours(self) :
        for record in self:
            hours = 0
            for task in self.task_ids:
                hours = hours + task.planned_hours
            record.planned_hours = hours

    @api.onchange('task_ids') #TODO: What happens if the task estimated time change?!
    def _compute_remaining_hours(self) :
        for record in self:
            hours = 0
            for task in self.task_ids:
                hours = hours + task.remaining_hours
            record.remaining_hours = hours

    @api.onchange('date')
    def _compute_day(self) :
        for record in self:
            _logger.warning(f"{date.strftime(record.date, '%Y-%m-%d')=}")
            record.colum_date = date.strftime(record.date, "%Y-%m-%d")
            _logger.warning(f"{record.colum_date=}")

    user_id = fields.Many2one('res.users', string='User')
    date = fields.Date('Date')
    task_ids = fields.One2many('project.task', 'assigned_user', string='Tasks')
    planned_hours = fields.Float('Planned Hours', compute=_compute_planned_hours)
    remaining_hours = fields.Float('Remaining Hours', compute=_compute_remaining_hours)
    colum_date = fields.Char('Column Sortby Date', store=True, compute=_compute_day)
