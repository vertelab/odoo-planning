# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import logging
import pytz
import uuid

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from functools import partial

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = "project.task"

    role = fields.Many2one(comodel_name="planner_ce.role",string="Planner Role", help='Role that the project memeber can have to solve this task.')


class PlannerCePlanning(models.Model):
    _name = 'planner_ce.planner'
    _description = 'Planner'

    active = fields.Boolean(string='Active')
    create_date = fields.Date(string='Created on')
    display_name = fields.Char(string='Display Name', size=64, trim=True, )
 
    name = fields.Char(string='Name', size=64, trim=True, )


class PlannerCePlanningRole(models.Model):
    _name = 'planner_ce.role'
    _description = 'Planner Role'

    name = fields.Char('Name', required=True)
    color = fields.Integer("Color", default=0)


class PlannerCePlanningSlot(models.Model):
    _name = 'planner_ce.slot'
    _description = 'Planning Slot'
    _order = 'start_datetime,id desc'
    _inherit = ['portal.mixin', 'mail.thread.cc', 'mail.activity.mixin', 'rating.mixin']
    _rec_name = 'name'
    _check_company_auto = True

    def _default_employee_id(self):
        return self.env.user.employee_id

    def _default_start_datetime(self):
        return fields.Datetime.to_string(datetime.combine(fields.Datetime.now(), datetime.min.time()))

    def _default_end_datetime(self):
        return fields.Datetime.to_string(datetime.combine(fields.Datetime.now(), datetime.max.time()))

    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('requested', 'Requested'),
                                        ('confirmed', 'Confirmed'),
                                        ('denied', 'Denied'),
                                        ('cancel', 'Cancel')], string='State', default='draft', tracking=True)
    name = fields.Char(string="Planning Name", related='project_id.name', readonly=False, store=True)
    note = fields.Text('Note')
    employee_id = fields.Many2one('hr.employee', "Employee", default=_default_employee_id,
                                  group_expand='_read_group_employee_id', check_company=True, tracking=True)
    project_id = fields.Many2one(
        'project.project', string="Project", store=True,
        readonly=False, copy=True, check_company=True,
        domain="[('company_id', '=', company_id)]")
    # task_id = fields.Many2one(
    #     'project.task', string="Task", store=True, readonly=False,
    #     copy=True, check_company=True,
    #     domain="[('company_id', '=', company_id),""('project_id', '=?', project_id)]")

    user_id = fields.Many2one('res.users', string="User", related='employee_id.user_id', store=True, readonly=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    # role_id = fields.Many2one('planner_ce.role', string="Role")
    # color = fields.Integer("Color", related='role_id.color')
    was_copied = fields.Boolean("This shift was copied from previous week", default=False, readonly=True)

    start_datetime = fields.Datetime("Start Date", required=True, default=_default_start_datetime)
    end_datetime = fields.Datetime("End Date", required=True, default=_default_end_datetime)

    # UI fields and warnings
    allow_self_unassign = fields.Boolean('Let employee unassign themselves')
    is_assigned_to_me = fields.Boolean('Is this shift assigned to the current user',
                                       compute='_compute_is_assigned_to_me')
    overlap_slot_count = fields.Integer('Overlapping slots', compute='_compute_overlap_slot_count')

    # time allocation
    allocation_type = fields.Selection([
        ('planning', 'Planning'),
        ('forecast', 'Forecast')
    ], compute='_compute_allocation_type')
    allocated_hours = fields.Float("Allocated hours", default=0, compute='_compute_allocated_hours', store=True)
    allocated_percentage = fields.Float("Allocated Time (%)", default=100,
                                        help="Percentage of time the employee is supposed to work during the shift.")
    working_days_count = fields.Integer("Number of working days", compute='_compute_working_days_count', store=True)

    # publication and sending
    is_published = fields.Boolean("Is the shift sent", default=False, readonly=True,
                                  help="If checked, this means the planning entry has been sent to the employee. "
                                       "Modifying the planning entry will mark it as not sent.")
    publication_warning = fields.Boolean("Modified since last publication", default=False, readonly=True,
                                         help="If checked, it means that the shift contains has changed since its "
                                              "last publish.", copy=False)

    # template dummy fields (only for UI purpose)
    template_creation = fields.Boolean("Save as a Template", default=False, store=False)

    # repeat = fields.Boolean("Repeat")
    repeat_interval = fields.Integer(string='Repeat every')
    repeat_type = fields.Selection(selection=[('forever', 'Forever'), ('until', 'Until')], string='Repeat Type')
    repeat_until = fields.Date(string='Repeat Until')

    contract_schema_time = fields.Float(string="Schema Time", compute='_get_schema', store=True)

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

    _sql_constraints = [
        ('check_start_date_lower_end_date', 'CHECK(end_datetime > start_datetime)', 'Shift end date should be greater than its start date'),
        ('check_allocated_hours_positive', 'CHECK(allocated_hours >= 0)', 'You cannot have negative shift'),
    ]

    @api.depends('user_id')
    def _compute_is_assigned_to_me(self):
        for slot in self:
            slot.is_assigned_to_me = slot.user_id == self.env.user

    def _read_group_employee_id(self, employees, domain, order):
        if self._context.get('planning_expand_employee'):
            return self.env['planner_ce.slot'].search([('create_date', '>', datetime.now() - timedelta(days=30))]).mapped('employee_id')
        return employees

    @api.depends('start_datetime', 'end_datetime', 'employee_id')
    def _compute_overlap_slot_count(self):
        if self.ids:
            self.flush(['start_datetime', 'end_datetime', 'employee_id'])
            query = """
                SELECT S1.id,count(*) FROM
                    planner_ce_slot S1, planner_ce_slot S2
                WHERE
                    S1.start_datetime < S2.end_datetime and S1.end_datetime > S2.start_datetime and S1.id <> S2.id and S1.employee_id = S2.employee_id
                GROUP BY S1.id;
            """
            self.env.cr.execute(query, (tuple(self.ids),))
            overlap_mapping = dict(self.env.cr.fetchall())
            for slot in self:
                slot.overlap_slot_count = overlap_mapping.get(slot.id, 0)
        else:
            self.overlap_slot_count = 0

    @api.depends('start_datetime', 'end_datetime')
    def _compute_allocation_type(self):
        for slot in self:
            if slot.start_datetime and slot.end_datetime and (slot.end_datetime - slot.start_datetime).total_seconds() / 3600.0 < 24:
                slot.allocation_type = 'planning'
            else:
                slot.allocation_type = 'forecast'

    @api.depends('start_datetime', 'end_datetime', 'employee_id.resource_calendar_id', 'allocated_percentage')
    def _compute_allocated_hours(self):
        for slot in self:
            if slot.start_datetime and slot.end_datetime:
                percentage = slot.allocated_percentage / 100.0 or 1
                if slot.allocation_type == 'planning' and slot.start_datetime and slot.end_datetime:
                    slot.allocated_hours = (slot.end_datetime - slot.start_datetime).total_seconds() * percentage / 3600.0
                else:
                    if slot.employee_id:
                        slot.allocated_hours = slot.employee_id._get_work_days_data(
                            slot.start_datetime, slot.end_datetime, compute_leaves=True)['hours'] * percentage
                    else:
                        slot.allocated_hours = 0.0

    @api.depends('start_datetime', 'end_datetime', 'employee_id')
    def _compute_working_days_count(self):
        for slot in self:
            if slot.employee_id:
                slot.working_days_count = \
                slot.employee_id._get_work_days_data(slot.start_datetime, slot.end_datetime, compute_leaves=True)['days']
            else:
                slot.working_days_count = 0

    def action_request(self):
        self.state = 'requested'

    def action_confirm(self):
        self.state = 'confirmed'

    def action_denied(self):
        self.state = 'denied'

    def action_cancel(self):
        self.state = 'cancel'

    # @api.constrains('task_id', 'project_id')
    # def _check_task_in_project(self):
    #     for forecast in self:
    #         if forecast.task_id and (forecast.task_id not in forecast.project_id.tasks):
    #             raise ValidationError(_("Your task is not in the selected project."))

    def action_see_overlapping_slots(self):
        pass

    def action_send(self):
        pass

    def action_publish(self):
        pass

    def action_self_assign(self):
        pass

    def action_self_unassign(self):
        pass


class PlannerCePlanningSlot(models.Model):
    _name = 'bulk.planner_ce.slot.wizard'
    _description = 'Bulk Planning Slot Wizard'

    project_id = fields.Many2one('project.project', string="Project")

    planning_ids = fields.One2many("bulk.planner_ce.slot", "wizard_id", string="Plan Slot")

    def action_plan(self):
        for item in self.planning_ids:
            self.env['planner_ce.slot'].create({
                'name': self.project_id.name,
                'project_id': self.project_id.id,
                'employee_id': item.employee_id.id,
                'start_datetime': item.start_datetime,
                'end_datetime': item.end_datetime,
                'allocated_percentage': item.allocated_percentage,
                'allocated_hours': item.allocated_hours,
            })




class PlannerCePlanningSlot(models.Model):
    _name = 'bulk.planner_ce.slot'
    _description = 'Bulk Planning Slot'

    @api.depends('week_selection', 'start_datetime')
    def _compute_end_date(self):
        for plan in self:
            if plan.week_selection and plan.start_datetime:
                plan.end_datetime = plan.start_datetime + timedelta(weeks=int(plan.week_selection))
            else:
                plan.end_datetime = False
    
    def _inverse_end_date(self):
        for plan in self:
            plan.end_datetime = plan.start_datetime

    employee_id = fields.Many2one('hr.employee', "Employee", required=True)
    start_datetime = fields.Datetime("Start Date", required=True)
    end_datetime = fields.Datetime("End Date", required=True, compute=_compute_end_date, inverse=_inverse_end_date)
    allocated_percentage = fields.Float("Allocated Time (%)", default=100,
                                        help="Percentage of time the employee is supposed to work during the shift.")
    allocated_hours = fields.Float("Allocated hours", default=0, compute='_compute_allocated_hours', store=True)
    wizard_id = fields.Many2one('bulk.planner_ce.slot.wizard', string="Planning Wizard")
    week_selection = fields.Selection([('1', 'Week 1'), ('2', 'Week 2'), ('3', 'Week 3'), ('4', 'Week 4'), ('5', 'Week 5'), ('6', 'Week 6')], string="Week")




    @api.depends('start_datetime', 'end_datetime', 'employee_id.resource_calendar_id', 'allocated_percentage')
    def _compute_allocated_hours(self):
        for slot in self:
            if slot.start_datetime and slot.end_datetime:
                percentage = slot.allocated_percentage / 100.0 or 1
                
                if slot.employee_id:
                    slot.allocated_hours = slot.employee_id._get_work_days_data(
                        slot.start_datetime, slot.end_datetime, compute_leaves=True)['hours'] * percentage
                else:
                    slot.allocated_hours = 0.0
