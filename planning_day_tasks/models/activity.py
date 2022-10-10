from odoo import models, fields, api, _
from datetime import date


class Activities(models.Model):
    _inherit = 'mail.activity'

    @api.depends("res_model")
    def _set_hours(self):
        for rec in self:
            if rec.res_model == 'project.task':
                task_id = self.env[rec.res_model].browse(rec.res_id)
                rec.planned_hours = task_id.planned_hours
            else:
                rec.planned_hours = 0

    def _inverse_hours(self):
        pass

    planned_hours = fields.Float('Planned Hours', tracking=True, compute=_set_hours, inverse=_inverse_hours, store=True)

    def action_view_activity_tasks(self):
        return {
            'view_mode': 'form',
            'res_model': self.res_model,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.res_id,
            'views': [[False, 'form']]
        }

    @api.depends("res_model")
    def _compute_user(self):
        for rec in self:
            if rec.res_model == 'project.task':
                task_id = self.env[rec.res_model].browse(rec.res_id)
                rec.task_user_id = task_id.user_id
            else:
                rec.task_user_id = self.env.user

    def _inverse_user(self):
        for rec in self:
            rec.task_user_id = self.env.user

    task_user_id = fields.Many2one(
        'res.users', 'Task Assigned to',
        compute=_compute_user, inverse=_inverse_user,
        index=True, required=True)

    @api.onchange('task_user_id')
    def onchange_user_task(self):
        if self.task_user_id:
            self.user_id = self.task_user_id.id
            self.summary = self.task_id.name

    @api.model
    def create(self, values):
        res = super(Activities, self).create(values)
        res.recalculate_planned_hours_for_task()
        day_plan_id = self.env['day.plan'].search([
            ('user_id', '=', res.user_id.id),
            ('date', '=', res.date_deadline)
        ], limit=1)

        if not day_plan_id:
            self.env['day.plan'].create({
                'user_id': res.user_id.id, 'date': res.date_deadline
            })
        return res

    def write(self, values):
        res = super(Activities, self).write(values)
        self.recalculate_planned_hours_for_task()
        return res

    @api.depends('user_id')
    def _get_recent_activities(self):
        for rec in self:
            if rec.user_id:
                activity_ids = self.env['mail.activity'].search([
                    ('user_id', '=', rec.user_id.id),
                    ('res_model', '=', 'project.task'),
                    ])
                if activity_ids:
                    rec.recent_user_activity_ids = activity_ids.ids
                else:
                    rec.recent_user_activity_ids = False
            else:
                rec.recent_user_activity_ids = False

    recent_user_activity_ids = fields.Many2many("mail.activity", string="Recent Activities",
                                                compute=_get_recent_activities)

    @api.depends('planned_hours')
    def recalculate_planned_hours_for_task(self):
        for rec in self:
            rec.task_id._compute_activity_planned_hours()

    @api.onchange('activity_type_id')
    def _onchange_activity_type_id(self):
        if self.activity_type_id:
            if self.activity_type_id.summary and self.res_model != 'project.task':
                self.summary = self.activity_type_id.summary
            elif self.res_model != 'project.task':
                self.summary = self.task_id.name
            self.date_deadline = self._calculate_date_deadline(self.activity_type_id)
            if self.res_model == 'project.task':
                self.user_id = self.task_user_id.id
            else:
                self.user_id = self.activity_type_id.default_user_id or self.env.user
            if self.activity_type_id.default_description:
                self.note = self.activity_type_id.default_description

    task_id = fields.Many2one("project.task", string="Task", compute="_compute_task")

    def _compute_task(self):
        for rec in self:
            if rec.res_model == "project.task":
                rec.task_id = self.env[rec.res_model].browse(rec.res_id).id
            else:
                rec.task_id = False
