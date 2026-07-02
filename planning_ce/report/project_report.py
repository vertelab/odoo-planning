# -*- coding: utf-8 -*-


from odoo import fields, models, tools


# class ReportProjectTaskUser(models.Model):
#     _inherit = "report.project.task.user"

#     role = fields.Many2one(comodel_name="planner_ce.role",string="Planner Role", help='Role that the project memeber can have to solve this task.',readonly=True)

#     def _select(self):
#         return super(ReportProjectTaskUser,self)._select() + ",\nt.role as role"

#     def _group_by(self):
#         return super(ReportProjectTaskUser,self)._group_by() + ",\nt.role"
