# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = "hr.employee"

    # default_planning_role_id = fields.Many2one('planner_ce.role', string="Planning Role")
    planning_role_ids = fields.Many2many('planner_ce.role', string="Planning Role IDS")

    def action_view_planning(self):
        return {
            'name': _('Schedule by Employee'),
            'type': 'ir.actions.act_window',
            'res_model': 'planner_ce.slot',
            'views': [(False, 'calendar'), (False, 'tree'), (False, 'form')],
            'view_mode': 'calendar,tree,form',
            'view_id': False,
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
                'search_default_group_by_employee': True,
                'planning_expand_employee': True,
            },
        }
