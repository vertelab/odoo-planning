# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)


class PlannerCePlanning(models.Model):
    _name = 'planner_ce.planner'
    #_description = 'Task Stage'
    #_order = 'name'
    #__last_update	Last Modified on	datetime​	Base Field 
    active=fields.Boolean(string='Active')
    create_date=fields.Date(string='Created on') # fields.date.add|context_today|end_of|start_of|substract|to_date|to_string|today 
    create_uid=fields.Many2one(comodel_name='Created by') # domain|context|ondelete="'set null', 'restrict', 'cascade'"|auto_join|delegate 
    display_name=fields.Char(string='Display Name', size=64, trim=True, )d 
 
    name=fields.Char(string='Name', size=64, trim=True, ) 
    plan_activity_type_ids=fields.Many2many(comodel_name='Activities',string='_') # relation|column1|column2
    write_date=fields.Date(string='Last Updated on')
    write_uid=fields.Many2one(comodel_name='Last Updated by') 

class PlannerCePlanningRole(models.Model):
    _name = 'planner_ce.role'
    color=fields.Integer(string='Color')
    create_date=fields.Date(string='Created on')
    create_uid=fields.Many2one(comodel_name='Created by') 
    display_name=fields.Char(string='Display name', size=64, trim=True, )
    employee_ids=fields.Many2many(comodel_name='Employees',string='Employees')
    sequence=fields.Integer(string='Sequence')
    write_date=fields.Date(string='Last Updated') 
    write_uid=fields.Many2one(comodel_name='Last Updated')

class PlannerCePlanningSlot(models.Model):
    _name = 'planner_ce.slot'
    #__last_update	Last Modified on	datetime	Base Field
    access_token=fields.Char(string='Security Token', size=64, trim=True, )
    allocated_hours=fields.Float(string='Allocated Hours')
    allocated_percentage=fields.Float(string='Allocated Time')
    allocation_type=fields.Selection(selection=[('planning','Planning'),('forecast','Forecast')],string='Allocation')
    allow_forecast=fields.Boolean(string='Planning')
    allow_self_unassign=fields.Boolean(string='Let Employee Unassign')
    allow_template_creation=fields.Boolean(string='Allow Template Creation')
    allow_timesheets=fields.Boolean(string='Allow timesheets')
    color=fields.Integer(string='Color')
    company_id=fields.Many2one(comodel_name='res.company')
    confirm_delete = fields.Boolean(string='Confirm Slots Deletion')
    department_id=fields.Many2one(comodel_name='hr.department')
    display_name=fields.Char(string='Display Name', size=64, trim=True, )
    effective_hours=fields.Float(string='Effective Hours')
    employee_id=fields.Many2one(comodel_name='hr.employee')
    end_datetime=fields.Date(string='End Date')
    forecast_hours=fields.Float(string='Forecast Hours')
    is_assigned_to_me=fields.Boolean(string='Is This Shift Assigned To The Current User')
    is_past=fields.Boolean(string='Is This Shift In The Past?')
    is_published=fields.Boolean(string='Is The Shift Sent')
    manager_id=fields.Many2one(comodel_name='Manager')
    # ~ name=fields.Text(string='Note')
    order_line_id=fields.Many2one(comodel_name='Sales Order Line')
    overlap_slot_count=fields.Integer(string='Overlapping Slots')
    parent_id=fields.Many2one(comodel_name='Parent Task')
    percentage_hours=fields.Float(string='Progress')
    planned_hours=fields.Float(string='Initially Planned Hours')
    previous_template_id=fields.Many2one(comodel_name='Previous Template')
    project_id=fields.Many2one(comodel_name='Project')
    publication_warning=fields.Boolean(string='Modified Since Last Publication')
    recurrency_id=fields.Boolean(string='Recurrency')
    repeat=fields.Boolean(string='Repeat')
    repeat_interval=fields.Integer(string='Repeat every')
    repeat_type=fields.Selection(selection=[('forever','Forever'),('until','Until')],string='Repeat Type')
    repeat_until=fields.Date(string='Repeat Until')
    role_id=fields.Many2one(comodel_name='Role')
