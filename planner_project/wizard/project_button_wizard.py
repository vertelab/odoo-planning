from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from pytz import utc

import logging
import pytz

def make_aware(dt):
    """ Return ``dt`` with an explicit timezone, together with a function to
        convert a datetime to the same (naive or aware) timezone as ``dt``.
    """
    if dt.tzinfo:
        return dt, lambda val: val.astimezone(dt.tzinfo)
    else:
        return dt.replace(tzinfo=utc), lambda val: val.astimezone(utc).replace(tzinfo=None)

_logger = logging.getLogger("\033[45m"+__name__+"\033[46;30m")


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
                "res_id":self.env["bulk.planner.slot"].create({'project_id': self.id}).id,
            }
        _logger.error(f"{self.name}")
        return action


class PlannerCePlanningSlotprojectWizard(models.TransientModel):
    _name = 'bulk.planner.slot'
    _description = 'Bulk Planning Slot'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    name = fields.Char()

    def _default_start_datetime(self):
        return fields.Datetime.to_string(datetime.combine(fields.Datetime.now(), datetime.min.time()))

    @api.depends('start_datetime')
    def _default_end_datetime(self):
        return fields.Datetime.to_string(datetime.combine(fields.Datetime.now(), datetime.max.time()))
    
    contract_schema_time = fields.Float(string="Schema Time", compute='_get_schema', store=True)
    contract_ids = fields.One2many('hr.contract','employee_id', string='Employee Contracts')

    @api.depends('employee_id')
    def _get_schema(self):
        for emp in self:
            if emp.employee_id:
                if emp.employee_id.contract_ids.filtered(lambda c: c.state == 'open'):
                    emp.contract_schema_time = emp.employee_id.sudo().contract_id.resource_calendar_id.get_work_duration_data(
                        emp.start_datetime, emp.end_datetime, compute_leaves=True)['hours']
                else:
                    emp.contract_schema_time = False
            else:
                emp.contract_schema_time = False

    working_days_count = fields.Integer("Number of working days", compute='_compute_working_days_count', store=True)
    employee_id = fields.Many2one('hr.employee', "Employee")
    employee_ids = fields.Many2many('hr.employee',  string='Employees', store=True, required=True)
    start_datetime = fields.Datetime("Start Date", required=True, default=_default_start_datetime)
    end_datetime = fields.Datetime("End Date", required=True, default=_default_end_datetime)
    project_id = fields.Many2one(comodel_name="project.project", string="Project", store=True, readonly=True)
    name = fields.Char(string="Planning Name", related='project_id.name', readonly=False, store=True)
    note = fields.Text("Note")
    hours_per_week = fields.Float(String="Work time")
    #Might be used in the futcher
    # week_selection = fields.Selection([('1', 'Week 1'), ('2', 'Week 2'), ('3', 'Week 3'), ('4', 'Week 4'), ('5', 'Week 5'), ('6', 'Week 6')], string="Week", default='1')
    
    @api.depends('start_datetime', 'end_datetime','employee_id.resource_calendar_id', 'employee_id')
    def _compute_working_days_count(self):
        for slot in self:
            if slot.employee_id:
                slot.working_days_count = \
                slot.employee_id._get_work_days_data(slot.start_datetime, slot.end_datetime, compute_leaves=True)['days']
            else:
                slot.working_days_count = 0

    def get_worktimes(self, start_dt, end_dt):
        for employee in self.employee_ids:
            schedule = employee.resource_calendar_id
       
            closest_work_end = schedule._get_closest_work_time(start_dt, match_end=True, search_range=[start_dt, end_dt])
            closest_work = schedule._get_closest_work_time(start_dt, match_end=False, search_range=[start_dt, end_dt])
            _logger.error(f"{start_dt}")
            _logger.error(f"{end_dt}")
            closest_work_end = closest_work_end.astimezone(pytz.utc) if closest_work_end else None
            closest_work = closest_work.astimezone(pytz.utc) if closest_work else None
            _logger.error(f"{closest_work}")
            _logger.error(f"{closest_work_end}")
            return [closest_work, closest_work_end]

    def split_times(self):
        split_time = 0
        for employee in self.employee_ids:
            split_time += 1
        return split_time

    def create_slots(self):
        #Devides the time the user choses betwen the employees
        split_time = self.split_times()
        work_time = self.hours_per_week / split_time
        for employee in self.employee_ids:
            delta_work_time = timedelta(hours=work_time)
            self.end_datetime = (datetime.combine(self.end_datetime, datetime.max.time()))
            if self.start_datetime and self.end_datetime and employee:
                result = employee._get_work_days_data(
                            self.start_datetime, self.end_datetime, compute_leaves=True)['hours']

                #Adds timezone
                start_dt = self.start_datetime.replace(tzinfo=utc)
                end_dt = self.end_datetime.replace(tzinfo=utc)
                time_delta = end_dt - start_dt

                if delta_work_time < timedelta(hours = work_time):
                    raise UserError(_("The work time is more then the emplyee contracted time betwen start and end time, pleas change the work time."))
                closest_work, closest_work_end = self.get_worktimes(start_dt, end_dt)

                #Might not be neded, maby trigers when the users have holiday?
                if closest_work == None and closest_work_end == None:
                    raise UserError(_("The times you have chosen dose not contain any work time, please chose new times."))

                while end_dt > closest_work:
                    if closest_work > start_dt:
                        start_dt = closest_work
                    while delta_work_time > timedelta(seconds=7200) and closest_work == start_dt or closest_work_end > start_dt + timedelta(hours=2):

                        #Takes away the timezone so it can be used in vals
                        start_dt_no_tz = start_dt.replace(tzinfo=None)

                        #7200 seconds is 2 hours, if its more then 2 hours take away
                        if delta_work_time > timedelta(seconds=7200):
                            delta_work_time -= timedelta(seconds=7200)
                        else:
                            #If it's les break out off the second while loop
                            break
                        vals = [{
                            'name': self.project_id.name,
                            'employee_id': employee.id,
                            'note': self.note,
                            'start_datetime':start_dt_no_tz,
                            'end_datetime': start_dt_no_tz + timedelta(hours=2),
                            'contract_schema_time': self.contract_schema_time
                            }]
                        self.env['planner_ce.slot'].create(vals)
                        start_dt += timedelta(hours=2)
                        time_delta = end_dt - start_dt

                        if start_dt == end_dt:
                            break
                        closest_work, closest_work_end = self.get_worktimes(start_dt, end_dt)

                    if delta_work_time <= timedelta(seconds=7200):
                        break

                    if closest_work == None or closest_work_end == None:
                        break
                    closest_work, closest_work_end = self.get_worktimes(start_dt, end_dt)
                
                #Counts out the remaining time that is 2 hours or les
                if delta_work_time >= timedelta(seconds=1):
                    closest_work, closest_work_end = self.get_worktimes(start_dt, end_dt)
                    time_to_end =  delta_work_time

                    start_dt_no_tz = start_dt.replace(tzinfo=None)
                    vals = [{
                        'name': self.project_id.name,
                        'employee_id': employee.id,
                        'note': self.note,
                        'start_datetime': start_dt_no_tz,
                        'end_datetime': start_dt_no_tz + time_to_end,
                        'contract_schema_time': self.contract_schema_time
                        }]
                    self.env['planner_ce.slot'].create(vals)
                    start_dt += delta_work_time
                    time_delta -= delta_work_time
                    delta_work_time -= delta_work_time

                    if start_dt == end_dt:
                        break
                
                #Last check then it's hopefuly done
                if delta_work_time < timedelta(seconds=0):
                    break
                closest_work, closest_work_end = self.get_worktimes(start_dt, end_dt)


