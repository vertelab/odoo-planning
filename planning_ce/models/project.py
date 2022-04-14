# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

# ~ import logging
# ~ _logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = "project.task"

    role = fields.Many2one(comodel_name="planner_ce.role", string="Planner Role",
                           help='Role that the project memeber can have to solve this task.')
    
    @api.model
    def _read_group_role(self, role, domain, order):
        """ Always display all roles in task kanban view """
        raise UserError('role %s' % role)
        return role.search([], order=order)
