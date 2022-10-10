from odoo import models, fields, api, _


class Tasks(models.Model):
    _inherit = 'project.task'

    @api.depends("activity_ids")
    def _compute_activity_planned_hours(self):
        for rec in self:
            rec.activity_planned_time = sum(self.activity_ids.mapped('planned_hours'))

    activity_planned_time = fields.Float(string="Computed Activity Planned Time",
                                         compute=_compute_activity_planned_hours, store=True)


    # @api.onchange('activity_planned_time')
    # def onchange_activity_planned_time(self):
    #     print(self.activity_planned_time)
    #     self.real_activity_planned_time = self.activity_planned_time
