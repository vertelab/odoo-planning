# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)


class ProjectCePlan(models.Model):
    #_name = 'project.task.tasktype'
    #_description = 'Task Stage'
    #_order = 'name'
    #__last_update	Last Modified on	datetime​	Base Field 
active	Active	boolean​	Base Field 
create_date	Created on	datetime ​	Base Field 
create_uid	Created by	many2one​	Base Field 
display_name	Display Name	char	​	Base Field 
id	ID	integer​	Base Field 
name	Name	char		Base Field 
plan_activity_type_ids	Activities	many2many​	Base Field 
write_date	Last Updated on	datetime​	Base Field
write_uid	Last Updated by	many2one Base Field

class ProjectCePlanningRole(models.Model):
  __last_update	Last Modified on	datetime	Base Field
color	Color	integer	Base Field
create_date	Created on	datetime	Base Field
create_uid	Created by	many2one	Base Field
display_name	Display Name	char		Base Field
employee_ids	Employees	many2many	Base Field
id	ID	integer	Base Field
name	Name	char		Base Field
sequence	Sequence	integer	Base Field
write_date	Last Updated on	datetime	Base Field
write_uid	Last Updated by	many2one	Base Field

class ProjectCePlanningShift(models.Model):
  __last_update	Last Modified on	datetime	Base Field
access_token	Security Token	char	Base Field
allocated_hours	Allocated Hours	float	Base Field
allocated_percentage	Allocated Time (%)	float		Base Field
allocation_type	Allocation Type	selection		Base Field
allow_forecast	Planning	boolean		Base Field
allow_self_unassign	Let Employee Unassign Themselves	boolean	Base Field
allow_template_creation	Allow Template Creation	boolean Base Field
allow_timesheets	Allow timesheets	boolean	Base Field
color	Color	integer	Base Field
company_id	Company	many2one		Base Field
confirm_delete	Confirm Slots Deletion	boolean	Base Field
create_date	Created on	datetime	Base Field
create_uid	Created by	many2one	Base Field
department_id	Department	many2one	Base Field
display_name	Display Name	char		Base Field
effective_hours	Effective Hours	float		Base Field
employee_id	Employee	many2one	Base Field
end_datetime	End Date	datetime	Base Field
forecast_hours	Forecast Hours	float		Base Field
id	ID	integer		Base Field
is_assigned_to_me	Is This Shift Assigned To The Current User	boolean	Base Field
is_past	Is This Shift In The Past?	boolean	Base Field
is_published	Is The Shift Sent	boolean	Base Field
manager_id	Manager	many2one		Base Field
name	Note	text		Base Field
order_line_id	Sales Order Line	many2one	Base Field
overlap_slot_count	Overlapping Slots	integer		Base Field
parent_id	Parent Task	many2one		Base Field
percentage_hours	Progress	float		Base Field
planned_hours	Initially Planned Hours	float		Base Field
previous_template_id	Previous Template	many2one		Base Field
project_id	Project	many2one		Base Field
publication_warning	Modified Since Last Publication	boolean	Base Field
recurrency_id	Recurrency	many2one	Base Field
repeat	Repeat	boolean		Base Field
repeat_interval	Repeat every	integer	Base Field
repeat_type	Repeat Type	selection		Base Field
repeat_until	Repeat Until	date		Base Field
role_id	Role	many2one		Base Field
