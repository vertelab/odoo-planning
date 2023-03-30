# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class PlannerCeReport(models.Model):
    _name = "ce_planner.report"

    project_id = fields.Many2one("project.project", "Project")
    employee_id = fields.Many2one("hr.employee", "Employee")
    date = fields.Date()
    week = fields.Integer("Week", store=True, compute="_calculate_week")
    time_planned = fields.Integer("Hours Planned", store=True, compute="_calculate_time_planned")
    time_spent = fields.Integer("Hours Spent", store=True, compute="_calculate_time_spent")
    timesheet = fields.One2many(comodel_name="hr_timesheet.sheet", string="Sheet", compute="_get_timesheet")

    def _get_timesheet(self):
        self.ensure_one()
        self.timesheet = self.env["hr_timesheet.sheet"].search([
                ("date_end", ">=", self.date),
                ("date_start", "<=", self.date),
                ("employee_id", "=", self.employee_id.id),
                # ~ ("company_id", "in", [self.company_id.id, False]),
                # ~ ("state", "in", ["new", "draft"]),
            ], limit=1)


    @api.depends('project_id', 'employee_id', 'date')
    def _calculate_time_planned(self):

        for rec in self:
            beginning_end = rec.get_first_last_day_of_week()

            time_planned_slots = self.env["planner_ce.slot"].search([
                                ('project_id', '=', rec.project_id.id), 
                                ('employee_id', '=', rec.employee_id.id), 
                                ('start_datetime', '>=', beginning_end['beginning']),
                                ('end_datetime', '<=', beginning_end['end']),
                                ])

            planned_hours = 0
            for slot in time_planned_slots:
                planned_hours += slot.allocated_hours
            rec.time_planned = planned_hours


    @api.depends('project_id', 'employee_id', 'date')
    def _calculate_time_spent(self):

        for rec in self:

            beginning_end = rec.get_first_last_day_of_week()
            time_spent_lines = self.env["account.analytic.line"].search([
                                ('project_id', '=', rec.project_id.id), 
                                ('employee_id', '=', rec.employee_id.id), 
                                ('date', '>=', beginning_end['beginning']),
                                ('date', '<=', beginning_end['end']),
                                ])

            spent_hours = 0
            for line in time_spent_lines:
                spent_hours += line.unit_amount
            rec.time_spent = spent_hours


    @api.depends('date')
    def _calculate_week(self):

        for rec in self:
            current_week = rec.date.isocalendar()[1]
            rec.week = current_week

    def get_first_last_day_of_week(self):
        for rec in self:
            beginning_end = {}
            start_of_week = rec.date - timedelta(days=rec.date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            beginning_end['beginning'] = start_of_week
            beginning_end['end'] = end_of_week

            return beginning_end
