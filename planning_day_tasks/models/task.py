from odoo import models, fields, api, _


class Tasks(models.Model):
    _inherit = 'project.task'

    @api.depends("activity_ids")
    def _compute_activity_planned_hours(self):
        for rec in self:
            rec.activity_planned_time = sum(self.activity_ids.mapped('planned_hours'))

    activity_planned_time = fields.Float(string="Computed Activity Planned Time",
                                         compute=_compute_activity_planned_hours, store=True)

    def write(self, vals):
        res = super(Tasks, self).write(vals)
        if vals.get("user_id"):
            self.activity_ids.filtered(lambda activity: activity.user_id != self.user_id).unlink()
        return res

    @api.onchange('stage_id')
    def clean_activities(self):
        if self.stage_id.is_closed and self.activity_ids:
            self.activity_ids.write({'active': False})

