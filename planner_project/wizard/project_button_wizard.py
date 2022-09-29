from email.policy import default
import re
from typing_extensions import Self
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

    def _get_project_name(self):
        # name_id = self.env["project.project"].browse(self.env.context.get('active_ids')).name
        self.name_id

    def _stop_date(self):
        date_today = date.today()
        date_replace = date_today + timedelta(weeks=1)
        return date_replace

    def _default_end_datetime(self):
        return datetime.now() + timedelta(hours=2)
    
    @api.depends('start_datetime', 'end_datetime', 'project_hours')
    def _compute_hours_week(self):
        for slot in self:
            fmt = '%Y-%m-%d'
            start_datetime = slot.start_datetime
            end_datetime = slot.end_datetime
            start = datetime.strptime(str (start_datetime), fmt)
            stop = datetime.strptime(str (end_datetime), fmt)
            total = stop - start
            total_int = total.days
            if slot.start_datetime and slot.end_datetime and slot.project_hours:
                slot.total_time_day = float(slot.project_hours) / float(total_int)

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

    @api.depends('start_datetime', 'end_datetime','employee_id.resource_calendar_id', 'allocated_percentage')
    def _compute_allocated_hours(self):
        for slot in self:
            if slot.start_datetime and slot.end_datetime:
                # percentage = slot.allocated_percentage / 100.0 or 1
                
                if slot.employee_id:
                    slot.allocated_hours = slot.employee_id._get_work_days_data(
                        slot.start_datetime, slot.end_datetime, compute_leaves=True)['hours'] 
                else:
                    slot.allocated_hours = 0.0

    allocated_hours = fields.Float("Allocated hours", default=0, compute='_compute_allocated_hours', store=True)
    allocated_percentage = fields.Float("Allocated Time (%)", default=100,
                                        help="Percentage of time the employee is supposed to work during the shift.")
    working_days_count = fields.Integer("Number of working days", compute='_compute_working_days_count', store=True)

    employee_id = fields.Many2one('hr.employee', "Employee",  store=True, required=True)
    employee_ids = fields.Many2many('hr.employee',  string='Employees')
    user_id = fields.Many2one('res.users', string="User", related='employee_id.user_id', store=True, readonly=True)
    # employee_id = fields.Many2one('hr.employee', "Employee",
    #                               group_expand='_read_group_employee_id', check_company=True, tracking=True)
    # start_date = fields.Date(string="Start date", default= date.today())
    # stop_date = fields.Date(string="End date", default=_stop_date)
    start_datetime = fields.Datetime("Start Date", required=True, default=datetime.now())
    end_datetime = fields.Datetime("End Date", required=True, default=_default_end_datetime)
    # project_hours = fields.Char("Amount of hours to spend on the project", store=True)
    note = fields.Text("Note")
    # total_time_day = fields.Char( store=True, compute='_compute_hours_week')
    project_id = fields.Many2one(comodel_name="project.project", default=lambda self: self._get_project_name(), readonly=True)
    # week1 = fields.Date(default =date.today() + timedelta(days=7))


    # @api.depends
    # def compute_weeks(self):
    #     week1 = self.week1 + timedelta(days=7)

    @api.depends('allocated_hours')
    def compute_slot_size(self):
        for slot in self:
            if slot.allocated_hours > 2:
                slot.split_time = slot.allocated_hours / 2


    # lambda self: self._get_project_name()
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


    @api.depends('allocated_hours', 'start_datetime', 'end_datetime')
    def _compute_slots_day(self):
        for time in self:
            int_var = 1
            while int_var <= time.split_time:
                time_bit = timedelta(hours=2)
                time.start_datetime += timedelta(hours=2)
                # time.end_datetime = timedelta(hours=1)
                time.allocated_hours -=  time_bit 
                if time.allocated_hours < time_bit:
                    rest = time.allocated_hours
                    time.start_datetime = rest
                    # time.end_datetime = rest
                int_var += 1

    @api.depends('start_datetime', 'allocated_hours', 'end_datetime')
    def compute_split_start(self):
        for start in self:
            start.start_datetime += timedelta(hours=2)
            start.allocated_hours -= 2
            start.end_datetime
            if start.allocated_hours < 2:
                min = timedelta(seconds=start.allocated_hours)*3600
                _logger.error(f"{min=}")
                start_date = str(datetime.strftime(start.start_datetime) + datetime.strftime(min,'%S' ))
                start.start_datetime = start_date
                # start_date = datetime.strftime(str(min))
                # datetime.strptime(str (end_datetime)
                start.end_datetime

    @api.model
    def create(self, vals):
        # res = self.env['planner_ce.slot'].create(values)
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
            _logger.error(f"TEST")
            if 1 > rec.split_time:
                val_id = self.env['planner_ce.slot'].create(vals_list)
            else:
                index_var = 1
                while index_var < rec.split_time:
                    rec.compute_split_start()
                    val_id = self.env['planner_ce.slot'].create(vals_list)
                    
                    index_var+=1
                    _logger.error('HELLO!!!!')
                    _logger.error(f"{index_var}")
                    _logger.error(f"{rec.split_time}")
                    _logger.error(f'{res}')
        return res


#TODO: find field project name
# find field employee_id
# find field week
# create field hours
# add field for notes

#Make a popup to add walues to all the fields

#Conekt the valuse so they turn to planer.slots in Planning CE

#Step2: Make every planer.slot to max 2 hours, if more then 2 hour they turn in to more 2 hour slots