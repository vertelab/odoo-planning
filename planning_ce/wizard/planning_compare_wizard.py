import logging
from datetime import date, timedelta
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)
import calendar


class CePlannerReportWizard(models.TransientModel):
    _name = 'ce_planner.report.wizard'
    
    date_start = fields.Date("Date Start")
    date_end = fields.Date("Date End")

    def create_reports(self):
        
        #--entire month is selected if fields are left empty, required=True might be better on the fields..?
        if self.date_start is False or self.date_end is False:
            today = date.today()
            last_day = calendar.monthrange(today.year, today.month)
            self.date_start = date(today.year, today.month, 1)
            self.date_end = date(today.year, today.month, last_day[1])

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
    

    def get_first_last_day_of_week(self, date):
        beginning_end = {}
        start_of_week = date - timedelta(days=date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        beginning_end['beginning'] = start_of_week
        beginning_end['end'] = end_of_week

        return beginning_end
