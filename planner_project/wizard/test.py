from email.policy import default
from math import ldexp
import re
from sqlite3 import enable_callback_tracebacks
from unicodedata import name
from odoo import api, fields, models, _
import logging
from datetime import timedelta, timezone, date, datetime, tzinfo
from odoo.http import request
import pytz
# import datetime


_logger = logging.getLogger(__name__)

class Project(models.Model):
    _inherit = "project.project"


    def action_plan_project(self):
        view_id = self.env.ref('planner_project.project_planning_wizard').id
        action = {
                "type": "ir.actions.act_window",
                "name": _("Prodject planning"),
                "view_mode": "form",
                "res_model": 'bulk.planner.slot',
                "target": "new",
                "view_id":view_id,
                # "res_id":self.env["bulk.planner.slot"].create({'project_id': self.id}).id,
                # .create({'project_id': self.id}).id,
            }
        return action

    original_name = fields.One2many(comodel_name="bulk.planner.slot", inverse_name="name_id")

class PlannerCePlanningSlotprojectWizard(models.TransientModel):
    _name = 'bulk.planner.slot'
    _description = 'Bulk Planning Slot'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    name = fields.Char()


    def _default_end_datetime(self):
        return datetime.now() + timedelta(hours=2)

    contract_schema_time = fields.Float(string="Schema Time", compute='_get_schema', store=True)
    contract_ids = fields.One2many('hr.contract','employee_id', string='Employee Contracts')

    @api.depends('employee_id')
    def _get_schema(self):
        for emp in self:
            if emp.employee_id:
                dt_start_date = fields.Datetime.from_string(emp.start_datetime)
                dt_end_date = fields.Datetime.from_string(emp.end_datetime)
                if emp.employee_id.contract_ids.filtered(lambda c: c.state == 'open'):
                    emp.contract_schema_time = emp.employee_id.sudo().contract_id.resource_calendar_id.get_work_duration_data(
                        dt_start_date, dt_end_date, compute_leaves=True)['hours']
                else:
                    emp.contract_schema_time = False
            else:
                emp.contract_schema_time = False

    # @api.depends('allocated_hours', 'end_datetime')
    # def _compute_end_times(self):
    #     # self._compute_allocated_hours()
    #     for rec in self:
    #         if rec.allocated_hours > 0:
    #             rec.end_datetime += timedelta(hours=rec.allocated_hours)
    #             # return rec.end_datetime

    allocated_hours = fields.Float("Allocated hours", default=0, compute='_compute_allocated_hours', store=True)
    allocated_percentage = fields.Float("Allocated Time (%)", default=100,
                                        help="Percentage of time the employee is supposed to work during the shift.")
    working_days_count = fields.Integer("Number of working days", compute='_compute_working_days_count', store=True)

    employee_id = fields.Many2one('hr.employee', "Employee",  store=True, required=True)
    user_id = fields.Many2one('res.users', string="User", related='employee_id.user_id', store=True, readonly=True)

    start_datetime = fields.Datetime("Start Date", required=True, default=datetime.now())
    end_datetime = fields.Datetime("End Date", required=True, default=_default_end_datetime)
    note = fields.Text("Note")
    project_id = fields.Many2one(comodel_name="project.project", default=lambda self: self._get_project_name(), readonly=True)
    
    @api.depends('start_datetime')
    def count_weeks(self):
        for rec in self:
            week_selection = "test"
            # week1 = rec.week_selection.filtered(lambda week: week == 'Week 1')
            week1 = rec.start_datetime + timedelta(days=7)

            # week2 = rec.week_selection.filtered(lambda week: week == 'Week 2')
            week2 = rec.start_datetime + timedelta(days=14)

            # week3 = rec.week_selection.filtered(lambda week: week == 'Week 3')
            week3 = rec.start_datetime + timedelta(days=21)

            # week4 = rec.week_selection.filtered(lambda week: week == 'Week 4')
            week4 = rec.start_datetime + timedelta(days=28)

            # week5 = rec.week_selection.filtered(lambda week: week == 'Week 5')
            week5 = rec.start_datetime + timedelta(days=35)

            # week6 = rec.week_selection.filtered(lambda week: week == 'Week 6')
            week6 = rec.start_datetime + timedelta(days=42)

            week_selection == fields.Selection([(week1, 'Week 1'), (week2, 'Week 2'), (week3, 'Week 3'), (week4, 'Week 4'), (week5, 'Week 5'), (week6, 'Week 6')], string="Week", default=week1)
        return week_selection

    # test = fields.Datetime(compute='count_weeks')

    @api.depends('allocated_hours')
    def compute_slot_size(self):
        for slot in self:
            if slot.allocated_hours > 2:
                slot.split_time = slot.allocated_hours / 2


    split_time = fields.Float(compute=compute_slot_size, store=True, string="Amount off slots")

    name_id = fields.Many2one(comodel_name="project.project")

    @api.depends('start_datetime', 'end_datetime','employee_id.resource_calendar_id', 'employee_id')
    def _compute_working_days_count(self):
        for slot in self:
            if slot.employee_id:
                slot.working_days_count = \
                slot.employee_id._get_work_days_data(slot.start_datetime, slot.end_datetime, compute_leaves=True)['days']
            else:
                slot.working_days_count = 0

    @api.depends('start_datetime', 'end_datetime','employee_id.resource_calendar_id', 'allocated_percentage')
    def _compute_allocated_hours(self):
        for slot in self:
            if slot.start_datetime and slot.end_datetime:
                percentage = slot.allocated_percentage / 100.0 or 1
                
                if slot.employee_id:
                    slot.allocated_hours = slot.employee_id._get_work_days_data(
                        slot.start_datetime, slot.end_datetime, compute_leaves=True)['hours'] * percentage
                else:
                    slot.allocated_hours = 0.0

    @api.depends('allocated_hours', 'start_datetime', 'end_datetime')
    def _compute_slots_day(self):
        for time in self:
            int_var = 1
            while int_var <= time.split_time:
                time_bit = timedelta(hours=2)
                time.start_datetime += timedelta(hours=2)
                time.allocated_hours -=  time_bit 
                if time.allocated_hours < time_bit:
                    rest = time.allocated_hours
                    time.start_datetime = rest
                int_var += 1

    @api.depends('start_datetime')
    def compute_split_start(self):
        for start in self:
            start.start_datetime += timedelta(hours=2)
            start.allocated_hours -= 2
            start.end_datetime
            if start.allocated_hours < 2:
                min = timedelta(seconds=start.allocated_hours)*3600
                _logger.error(f"{min=}")
                start_date = str(datetime.strftime(start.start_datetime) + datetime.strftime(min))
                start.start_datetime = start_date

                start.end_datetime

    @api.model
    def create(self, vals):

        res = super().create(vals)
        for rec in res:
            vals_list = {
                'employee_id': rec.employee_id.id,
                'note': rec.note,
                'start_datetime':rec.start_datetime,
                'end_datetime':rec.end_datetime,
                'allocated_hours':rec.allocated_hours,
                'allocated_percentage':rec.allocated_percentage,
                'contract_schema_time': rec.contract_schema_time
            }
            index_var = 1
            while index_var <= rec.split_time:
                val_id = self.env['planner_ce.slot'].create(vals_list)
                
                index_var+=1
                _logger.error('HELLO!!!!')
                _logger.error(f"{index_var}")
                _logger.error(f"{rec.split_time}")
        return val_id






        projektet
        anstäld
        employee_id = fields.Many2one('hr.employee', "Employee",  store=True, required=True)
        vecka
        week_selection = fields.Selection([('week1', 'Week 1'), ('2', 'Week 2'), ('3', 'Week 3'), ('4', 'Week 4'), ('5', 'Week 5'), ('6', 'Week 6')], string="Week")
        timmar
