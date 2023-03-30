import logging

from datetime import datetime, timedelta, date

from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)

all_weeks = [(str(x),str(x)) for x in range(1,53)]

class CePlannerReportWizard(models.TransientModel):
    _name = 'ce_planner.report.wizard'
    
    # project = fields.Many2one("project.project", "Project")
    # employee = fields.Many2one("hr.employee", "Employee")

    def calculate_year(self):
        todays_date = date.today()
        year = todays_date.year
        return year
        
    year = fields.Integer("Year", default=calculate_year)


    start_week = fields.Selection(all_weeks,
             string='Start week', required=True, default="1")
    end_week = fields.Selection(all_weeks,
             string='End week', required=True, default="1")
	  # week = fields.Integer("Week")
    # time_planned = fields.Integer("Time planned")
    # time_spent = fields.Integer("Time spent")

    def do_something(self):

        start_date = self.monday_of_calenderweek(self.year, int(self.start_week))
        end_date = self.sunday_of_calenderweek(self.year, int(self.end_week))
        date_range = self.get_date_range(start_date, end_date)

        for employee in self.env['hr.employee'].search([]): # går igenom alla anställda

            for day in date_range:
                for line in self.env['account.analytic.line'].search([('employee_id', '=', employee.id)]):
                    if line.date == day:
                        project_employee_combo_exists = self.env['ce_planner.report'].search([
                            ('employee_id', '=', employee.id),
                            ('project_id', '=', line.project_id.id),
                            ('week', '=', day.isocalendar()[1]),
                            ])

                        if not project_employee_combo_exists:
                            ce_report = self.env['ce_planner.report'].create({
                                'employee_id': employee.id,
                                'project_id': line.project_id.id,
                                'date': day,
                                })

                beginning_end = self.get_first_last_day_of_week(day)
                for slot in self.env['planner_ce.slot'].search([('employee_id', '=', employee.id), 
                                                                ('start_datetime', '>=', beginning_end['beginning']), 
                                                                ('start_datetime', '<=', beginning_end['end'])]):  
                    
                    
                    project_employee_combo_exists = self.env['ce_planner.report'].search([
                        ('employee_id', '=', employee.id),
                        ('project_id', '=', slot.project_id.id),
                        ('week', '=', day.isocalendar()[1]),
                        ])
                    if not project_employee_combo_exists:
                        # ~ ce_report = self.env['ce_planner.report'].create({
                        self.env['ce_planner.report'].create({
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

    def monday_of_calenderweek(self, year, week):
        first = date(year, 1, 1)
        base = 1 if first.isocalendar()[1] == 1 else 8
        return first + timedelta(days=base - first.isocalendar()[2] + 7 * (week - 1))

    def sunday_of_calenderweek(self, year, week):
        first = date(year, 1, 1)
        base = 1 if first.isocalendar()[1] == 1 else 8
        return first + timedelta(days=base - first.isocalendar()[2] + 6 + 7 * (week-1))

    def get_first_last_day_of_week(self, date):
        beginning_end = {}
        start_of_week = date - timedelta(days=date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        beginning_end['beginning'] = start_of_week
        beginning_end['end'] = end_of_week

        return beginning_end
