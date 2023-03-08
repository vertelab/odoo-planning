import logging
from datetime import datetime, timedelta

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class CePlannerReportWizard(models.TransientModel):
    _name = 'ce_planner.report.wizard'
    
    # project = fields.Many2one("project.project", "Project")
    # employee = fields.Many2one("hr.employee", "Employee")
    date_start = fields.Date("Date Start")
    date_end = fields.Date("Date End")
	# week = fields.Integer("Week")
    # time_planned = fields.Integer("Time planned")
    # time_spent = fields.Integer("Time spent")

    def do_something(self):
        date_range = self.get_date_range(self.date_start, self.date_end)
        for employee in self.env['hr.employee'].search([]):
            for day in date_range:
                for line in self.env['account.analytic.line'].search([('employee_id', '=', employee.id)]):
                    if line.date == day:
                        project_employee_combo_exists = self.env['ce_planner.report'].search([
                            ('employee_id', '=', employee.id),
                            ('project_id', '=', line.project_id.id),
                            ('week', '=', day.isocalendar()[1]),
                            ])

                        if len(project_employee_combo_exists) == 0:
                            ce_report = self.env['ce_planner.report'].create({
                                'employee_id': employee.id,
                                'project_id': line.project_id.id,
                                'date': day,
                                })
                _logger.warning(f"{employee.name} {employee.id} {day}")
                beginning_end = self.get_first_last_day_of_week(day)
                for slot in self.env['planner_ce.slot'].search([('employee_id', '=', employee.id), 
                                                                ('start_datetime', '>=', beginning_end['beginning']), 
                                                                ('start_datetime', '<=', beginning_end['end'])]):  
                    
                    
                    project_employee_combo_exists = self.env['ce_planner.report'].search([
                        ('employee_id', '=', employee.id),
                        ('project_id', '=', slot.project_id.id),
                        ('week', '=', day.isocalendar()[1]),
                        ])
                    if len(project_employee_combo_exists) == 0:
                        ce_report = self.env['ce_planner.report'].create({
                            'employee_id': employee.id,
                            'project_id': slot.project_id.id,
                            'date': day,
                        })
            # return {'type': 'ir.actions.act_window_close'}
        

    #if date_1 and date_2 arent monday to friday, maybe stick those missing dates into date_range?
    def get_date_range(self, date_1, date_2):
        date_range = []
        while date_1 <= date_2: 
            date_range.append(date_1) 
            date_1 += timedelta(days=1) 
        return date_range
    

    def get_first_last_day_of_week(self, date):
        beginning_end = {}
        start_of_week = date - timedelta(days=date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        beginning_end['beginning'] = start_of_week
        beginning_end['end'] = end_of_week

        return beginning_end