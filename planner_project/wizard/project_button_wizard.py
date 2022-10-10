from multiprocessing.resource_sharer import stop
from odoo import api, fields, models, _
import logging, inspect
from datetime import datetime, timedelta
import pytz
from pytz import utc
from odoo.exceptions import UserError

def make_aware(dt):
    """ Return ``dt`` with an explicit timezone, together with a function to
        convert a datetime to the same (naive or aware) timezone as ``dt``.
    """
    if dt.tzinfo:
        return dt, lambda val: val.astimezone(dt.tzinfo)
    else:
        return dt.replace(tzinfo=utc), lambda val: val.astimezone(utc).replace(tzinfo=None)

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG)
# _logger = logging.getLogger("\033[45m"+__name__+"\033[46;30m")
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
                # "res_id":self.env["bulk.planner.slot"].create({'project_id': self.id}).id,
                # .create({'project_id': self.id}).id,
            }
        _logger.error(f"{self.name}")
        return action
class PlannerCePlanningSlotprojectWizard(models.TransientModel):
    _name = 'bulk.planner.slot'
    _description = 'Bulk Planning Slot'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    name = fields.Char()

    def _default_start_datetime(self):
        return fields.Datetime.now()

    def _default_end_datetime(self):
        return fields.Datetime.now() + timedelta(hours=2)
    
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
    project_id = fields.Many2one(comodel_name="project.project", string="Project")
    name = fields.Char(string="Planning Name", related='project_id.name', readonly=False, store=True)
    note = fields.Text("Note")
    
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
#if        
            closest_work_end = schedule._get_closest_work_time(start_dt, match_end=True, search_range=[start_dt, end_dt])
            closest_work = schedule._get_closest_work_time(start_dt, match_end=False, search_range=[start_dt, end_dt])
            closest_work_end = closest_work_end.astimezone(pytz.utc) if closest_work_end else None
            closest_work = closest_work.astimezone(pytz.utc) if closest_work else None
            return [closest_work, closest_work_end]

    def create_slots(self):
        for employee in self.employee_ids:
            if self.start_datetime and self.end_datetime and employee:
                _logger.error(f"{self.start_datetime and self.end_datetime and employee=}")
                result = employee._get_work_days_data(
                            self.start_datetime, self.end_datetime, compute_leaves=True)['hours']
                start_dt = self.start_datetime.replace(tzinfo=utc)
                end_dt = self.end_datetime.replace(tzinfo=utc)
                time_delta = end_dt - start_dt
                _logger.error(f"{start_dt=}")
                closest_work, closest_work_end = self.get_worktimes(start_dt, end_dt)
                if closest_work == None and closest_work_end == None:
                    _logger.error("STOP")
                    raise UserError(_("The timmes you have chosen dose not contain any work timme, please chose new timmes."))
                _logger.error(f"{end_dt > closest_work=}")
                while end_dt > closest_work:
                    _logger.error(f"{closest_work > start_dt=}") #False
                    if closest_work > start_dt:
                        start_dt = closest_work
                        _logger.error(f"!!!{time_delta >= timedelta(seconds=7200) and closest_work == start_dt and closest_work_end >= start_dt + timedelta(hours=2)=}")
                        _logger.error(f"!!!time_delta = {time_delta}")
                        _logger.error(f"!!!time_delta >= timedelta(seconds=7200) = {time_delta >= timedelta(seconds=7200)}")
                        _logger.error(f"!!!closest_work = {closest_work}")
                        _logger.error(f"!!!start_dt = {start_dt}")
                        _logger.error(f"111end_dt = {end_dt}")
                        _logger.error(f"!!!closest_work == start_dt : {closest_work == start_dt}")
                        _logger.error(f"!!!closest_work_end = {closest_work_end}")
                        _logger.error(f"!!!start_dt = {start_dt}")
                        _logger.error(f"!!!closest_work_end >= start_dt + timedelta(hours=2) = {closest_work_end >= start_dt + timedelta(hours=2)}")

                    while time_delta >= timedelta(seconds=7200) and closest_work == start_dt and closest_work_end >= start_dt + timedelta(hours=2):
                        _logger.error(f"WHILE")
                        start_dt_no_tz = start_dt.replace(tzinfo=None)
                        vals = [{
                            'name': self.project_id.name,
                            'employee_id': employee.id,
                            'note': self.note,
                            'start_datetime':start_dt_no_tz,
                            'end_datetime': start_dt_no_tz + timedelta(hours=2),
                            'contract_schema_time': self.contract_schema_time
                            }]
                        self.env['planner_ce.slot'].create(vals)
                        _logger.error(f"NAME!!!{self.project_id.name=}")
                        start_dt += timedelta(hours=2)
                        time_delta = end_dt - start_dt
                        _logger.error(f":::{start_dt=}")
                        _logger.error(f":::{end_dt=}")
                        _logger.error(f"133 = {closest_work_end >= start_dt + timedelta(hours=2)}")
                        if start_dt == end_dt:
                            break
                        closest_work, closest_work_end = self.get_worktimes(start_dt, end_dt)
                        _logger.error(f"HELO1{time_delta=}")
                        _logger.error(f"HELO2{time_delta >= timedelta(seconds=1)=}")
                        _logger.error(f"HELO3{closest_work=}")
                        _logger.error(f"HELO4{start_dt=}")
                        _logger.error(f"HELO5{closest_work == start_dt=}")
                        _logger.error(f"HELO6{closest_work_end=}")
                        _logger.error(f"HELO7{start_dt + timedelta(seconds=1)}")
                    # _logger.error(f"HELO8{closest_work_end >= start_dt + timedelta(seconds=1)}")
                    # _logger.error(f"HELLOOOOO{time_delta >= timedelta(seconds=1) and closest_work == start_dt and closest_work_end >= start_dt + timedelta(seconds=1)=}")
                    if closest_work == None or closest_work_end == None:
                        _logger.error(f"WHAT????")
                        break
                    #False
                    _logger.error(f"{time_delta}")
                    _logger.error(f"{time_delta >= timedelta(seconds=1)=}")
                    _logger.error(f"HEAR {closest_work and time_delta >= timedelta(seconds=1) and closest_work == start_dt and closest_work_end >= start_dt + timedelta(seconds=1)}")
                    if closest_work and time_delta >= timedelta(seconds=1) and closest_work == start_dt and closest_work_end >= start_dt + timedelta(seconds=1):
                        time_to_end =  closest_work_end - start_dt
                        _logger.error(f"{time_to_end >  time_delta=}")
                        if time_to_end >  time_delta:
                            time_to_end = time_delta
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
                        start_dt += time_to_end
                        time_delta -= time_to_end
                        _logger.error(f"{start_dt == end_dt=}")
                        _logger.error(f"{start_dt=}")
                        _logger.error(f"{end_dt=}")
                        if start_dt == end_dt:
                            break
                        closest_work, closest_work_end = self.get_worktimes(start_dt, end_dt)
                    if time_delta <= timedelta(seconds=1):
                        break

