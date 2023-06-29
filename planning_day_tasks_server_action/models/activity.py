from collections import defaultdict
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import logging
import pytz

from odoo import api, exceptions, fields, models, _
from odoo.osv import expression

from odoo.tools.misc import clean_context
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG

_logger = logging.getLogger(__name__)

    
class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'
    
    planned_hours = fields.Float('Planned Hours')
    
    
    def _run_action_next_activity(self, eval_context=None):
        if not self.activity_type_id or not self._context.get('active_id') or self._is_recompute():
            return False

        records = self.env[self.model_name].browse(self._context.get('active_ids', self._context.get('active_id')))

        vals = {
            'summary': self.activity_summary or '',
            'note': self.activity_note or '',
            'activity_type_id': self.activity_type_id.id,
        }
        if self.activity_date_deadline_range > 0:
            vals['date_deadline'] = fields.Date.context_today(self) + relativedelta(**{
                self.activity_date_deadline_range_type: self.activity_date_deadline_range})
        for record in records:
            user = False
            if self.activity_user_type == 'specific':
                user = self.activity_user_id
            elif self.activity_user_type == 'generic' and self.activity_user_field_name in record:
                user = record[self.activity_user_field_name]
            if user:
                vals['user_id'] = user.id
            if self.planned_hours:
                vals['planned_hours'] = self.planned_hours
            record.activity_schedule(**vals)
        return False

