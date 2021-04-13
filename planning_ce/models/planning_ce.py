# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import logging
import pytz
import uuid

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time

_logger = logging.getLogger(__name__)

class PlannerCePlanning(models.Model):
    _name = 'planner_ce.planner'
    #_description = 'Task Stage'
    #_order = 'name'
    #__last_update	Last Modified on	datetime​	Base Field 
    active = fields.Boolean(string='Active')
    create_date = fields.Date(string='Created on') # fields.date.add|context_today|end_of|start_of|substract|to_date|to_string|today
    # create_uid = fields.Many2one(comodel_name='Created by') # domain|context|ondelete="'set null', 'restrict', 'cascade'"|auto_join|delegate
    display_name = fields.Char(string='Display Name', size=64, trim=True, )
 
    name = fields.Char(string='Name', size=64, trim=True, )
    # plan_activity_type_ids = fields.Many2many(comodel_name='Activities',string='_') # relation|column1|column2
    # write_date = fields.Date(string='Last Updated on')
    # write_uid = fields.Many2one(comodel_name='Last Updated by')


class PlannerCePlanningRole(models.Model):
    _name = 'planner_ce.role'

    name = fields.Char('Name', required=True)
    color = fields.Integer("Color", default=0)
    date_start = fields.Date(string="Date Start")
    date_stop = fields.Date(string="Date Stop")
    # create_date = fields.Date(string='Created on')
    # create_uid = fields.Many2one(comodel_name='Created by')
    # display_name = fields.Char(string='Display name', size=64, trim=True, )
    # employee_ids = fields.Many2many(comodel_name='Employees', string='Employees')
    # sequence = fields.Integer(string='Sequence')
    # write_date = fields.Date(string='Last Updated')
    # write_uid = fields.Many2one(comodel_name='Last Updated')


class PlannerCePlanningSlot(models.Model):
    _name = 'planner_ce.slot'
    _description = 'Planning Shift'
    _order = 'start_datetime,id desc'
    _rec_name = 'name'
    _check_company_auto = True

    def _default_employee_id(self):
        return self.env.user.employee_id

    def _default_start_datetime(self):
        return fields.Datetime.to_string(datetime.combine(fields.Datetime.now(), datetime.min.time()))

    def _default_end_datetime(self):
        return fields.Datetime.to_string(datetime.combine(fields.Datetime.now(), datetime.max.time()))

    name = fields.Text('Note')
    employee_id = fields.Many2one('hr.employee', "Employee", default=_default_employee_id,
                                  group_expand='_read_group_employee_id', check_company=True)
    user_id = fields.Many2one('res.users', string="User", related='employee_id.user_id', store=True, readonly=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    role_id = fields.Many2one('planner_ce.role', string="Role")
    color = fields.Integer("Color", related='role_id.color')
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
    # template_creation = fields.Boolean("Save as a Template", default=False, store=False,
    #                                    inverse='_inverse_template_creation')
    # template_autocomplete_ids = fields.Many2many('planning.slot.template', store=False,
    #                                              compute='_compute_template_autocomplete_ids')
    # template_id = fields.Many2one('planning.slot.template', string='Planning Templates', store=False)

    # Recurring (`repeat_` fields are none stored, only used for UI purpose)
    # recurrency_id = fields.Many2one('planning.recurrency', readonly=True, index=True, ondelete="set null", copy=False)

    repeat = fields.Boolean("Repeat")
    repeat_interval = fields.Integer(string='Repeat every')
    repeat_type = fields.Selection(selection=[('forever', 'Forever'), ('until', 'Until')], string='Repeat Type')
    repeat_until = fields.Date(string='Repeat Until')

    # repeat = fields.Boolean("Repeat", compute='_compute_repeat', inverse='_inverse_repeat')
    # repeat_interval = fields.Integer("Repeat every", default=1, compute='_compute_repeat', inverse='_inverse_repeat')
    # repeat_type = fields.Selection([('forever', 'Forever'), ('until', 'Until')], string='Repeat Type',
    #                                default='forever', compute='_compute_repeat', inverse='_inverse_repeat')
    # repeat_until = fields.Date("Repeat Until", compute='_compute_repeat', inverse='_inverse_repeat',
    #                            help="If set, the recurrence stop at that date. Otherwise, the recurrence is applied indefinitely.")

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

