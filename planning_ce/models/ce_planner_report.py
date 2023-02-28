# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class PlannerCeReport(models.Model):
	_name = "ce_planner.report"

	project_id = fields.Many2one("project.project", "Project")
	employee_id = fields.Many2one("hr.employee", "Employee")
	date = fields.Date()
	# week = fields.Integer("Week")
	time_planned = fields.Integer("Time Planned", store=True, compute="_calculate_time_planned")
	time_spent = fields.Integer("Time Spent", store=True, compute="_calculate_time_spent")

	def _calculate_time_planned(self):
		time_planned_slots = self.env["planner_ce.slot"].search([
							# ('project_id', '=', self.project.id), 
						    # ('employee_id', '=', self.employee.id), 
							('start_datetime', '>=', self.date_start),
							('end_datetime', '<=', self.date_end)])

		planned_hours = 0
		for slot in time_planned_slots:
			planned_hours += slot.allocated_hours
		
		self.time_planned = planned_hours

	def _calculate_time_spent(self):
		time_spent_lines = self.env["account.analytic.line"].search([
							# ('project_id', '=', self.project.id), 
						    # ('employee_id', '=', self.employee.id), 
							('date', '>=', self.date_start),
							('date', '<=', self.date_end)])
		
		spent_hours = 0
		for line in time_spent_lines:
			spent_hours += line.unit_amount
		
		self.time_spent = spent_hours
