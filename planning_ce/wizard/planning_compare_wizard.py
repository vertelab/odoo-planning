import logging
import datetime

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class CePlannerReportWizard(models.TransientModel):
    _name = 'ce_planner.report.wizard'
    
    # project = fields.Many2one("project.project", "Project")
    # employee = fields.Many2one("hr.employee", "Employee")
    date_start = fields.Date("Date start")
    date_end = fields.Date("Date end")
	# week = fields.Integer("Week")
    # time_planned = fields.Integer("Time planned")
    # time_spent = fields.Integer("Time spent")

    def do_something(self):
        date_range = self.get_date_range(self.date_start, self.date_end)
        for day in date_range:
            for employee in self.env['hr.employee'].search([]):
                for line in self.env['account.analytic.line'].search([('employee_id', '=', employee.id)]):
                    if line.date == day:
                        self.env['ce_planner.report'].create({
                            'employee_id': employee.id,
                            'project_id': line.project_id.id,
                            'date': line.date
                        })
        # return {'type': 'ir.actions.act_window_close'}
        
    def get_date_range(self, date_1, date_2):
        date_range = []
        while date_1 <= date_2: 
            date_range.append(date_1) 
            date_1 += datetime.timedelta(days=1) 
        return date_range