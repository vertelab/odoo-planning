from datetime import datetime, timedelta, time
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from pytz import utc
from dateutil.relativedelta import relativedelta, MO,FR  

import logging
import pytz

#returns 'dt' as aware if naive and vice versa
def _change_awareness(dt):
   
    return dt.replace(tzinfo=None) if dt.tzname() == "UTC" else dt.replace(tzinfo=utc)
    

_logger = logging.getLogger("\033[45m"+__name__+"\033[46;30m")


class Project(models.Model):
    _inherit = "project.project"

    def action_plan_project(self):
        view_id = self.env.ref('planner_project.project_planning_wizard').id
        action = {
                "type": "ir.actions.act_window",
                "name": _("Prodject planning"),
                "view_mode": "form",
                "res_model": 'bulk.planner.slot',
                "target": "new",
                "view_id":view_id,
                "res_id":self.env["bulk.planner.slot"].create({'project_id': self.id}).id,
            }
        return action


class PlannerCePlanningSlotprojectWizard(models.TransientModel):
    _name = 'bulk.planner.slot'
    _description = 'Bulk Planning Slot'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _start_dt_list = []
    _end_dt_list = []

    def _default_start_datetime(self):
        return fields.Datetime.to_string(_change_awareness(datetime.combine((datetime.now() + relativedelta(weekday=MO(+1))), time.min)))    
    
    @api.depends('start_datetime')
    def _default_end_datetime(self):
        
        end_date_next_friday = datetime.now() + relativedelta(weekday=FR(+1))
        start_datetime = datetime.strptime(self._default_start_datetime(), '%Y-%m-%d %H:%M:%S')
        if end_date_next_friday < start_datetime:
            end_date_next_friday = datetime.now() + relativedelta(weeks=1, weekday=FR(+1))
        return fields.Datetime.to_string(_change_awareness(datetime.combine(end_date_next_friday, time.max)))
    
    
    @api.depends('employee_id')
    def _get_schema(self):
        for emp in self:
            if emp.employee_id:
                if emp.employee_id.contract_ids.filtered(lambda c: c.state == 'open'):
                    emp.contract_schema_time = emp.employee_id.sudo().contract_id.resource_calendar_id.get_work_duration_data(
                        emp.start_datetime, emp.end_datetime, compute_leaves=True)['hours']
                else:
                    emp.contract_schema_time = False
            else:
                emp.contract_schema_time = False
                
    
    contract_schema_time = fields.Float(string="Schema Time", compute='_get_schema', store=True)
    contract_ids = fields.One2many('hr.contract','employee_id', string='Employee Contracts')
    
    working_days_count = fields.Integer("Number of working days", compute='_compute_working_days_count', store=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    employee_ids = fields.Many2many('hr.employee',  string='Employees', store=True, required=True)
    start_datetime = fields.Datetime("Start Date", required=True, default=_default_start_datetime)
    end_datetime = fields.Datetime("End Date", required=True, default=_default_end_datetime)
    project_id = fields.Many2one(comodel_name="project.project", string="Project", store=True, readonly=True)
    name = fields.Char(string="Planning Name", related='project_id.name', readonly=False, store=True)
    note = fields.Text("Note")
    hours_per_week = fields.Float(string="Work time")
 
    
    @api.depends('start_datetime', 'end_datetime','employee_id.resource_calendar_id', 'employee_id')
    def _compute_working_days_count(self):
        for slot in self:
            if slot.employee_id:
                slot.working_days_count = \
                slot.employee_id._get_work_days_data(slot.start_datetime, slot.end_datetime, compute_leaves=True)['days']
            else:
                slot.working_days_count = 0

    def _get_worktimes(self, start_dt, end_dt,employee):
            
        schedule = employee.resource_calendar_id

        closest_work_end = schedule._get_closest_work_time(start_dt, match_end=True, search_range=[start_dt, end_dt])
        closest_work = schedule._get_closest_work_time(start_dt, match_end=False, search_range=[start_dt, end_dt])

        closest_work_end = closest_work_end.astimezone(pytz.utc) if closest_work_end else None
        closest_work = closest_work.astimezone(pytz.utc) if closest_work else None

        return [closest_work, closest_work_end]

    
    api.depends("employee_id","employee_ids")
    def _get_slots_from_api(self,id):
        return self.env['planner_ce.slot'].search([['employee_id', '=', int(id)]])


    def _split_times(self):
        split_time = 0
        for _ in self.employee_ids:
            split_time += 1
        return split_time
    
    
    def _handel_user_blocks_that_overlap(self,user_blocks):
        
        blocks_to_delete = []
        
        for index, _ in enumerate(user_blocks):
            
            if index != 0:
                
                if user_blocks[index - 1].start_datetime < user_blocks[index].start_datetime and (user_blocks[index - 1].end_datetime > user_blocks[index].start_datetime and user_blocks[index - 1].end_datetime <= user_blocks[index].end_datetime):
                
                    user_blocks[index].start_datetime = user_blocks[index - 1].start_datetime
                    
                    blocks_to_delete.append(user_blocks[index - 1])
                    
                elif user_blocks[index].start_datetime <= user_blocks[index - 1].start_datetime and user_blocks[index].end_datetime >= user_blocks[index - 1].end_datetime:
                    
                    blocks_to_delete.append(user_blocks[index - 1])
        
        for block in blocks_to_delete:
            
            user_blocks.remove(block)
            
        return user_blocks
    
    
    
    def _get_user_blocks(self,id):
        
        user_blocks = []
        slots = self._get_slots_from_api(id)
        
        def _sort_slots_on_time(slot):
            return slot.end_datetime
        
        
        """
        creates a dummy class in order to be 
        able to write too it and avoid 
        rewriting the whole code 
        """
        class augmentable_user_blocks_class:
            
            def __init__(self,start_datetime,end_datetime):
                
                self.start_datetime = start_datetime
                self.end_datetime = end_datetime
                
        
        for slot in slots:
            
            if slot.employee_id == id:
            
                user_blocks.append(augmentable_user_blocks_class(slot.start_datetime,slot.end_datetime))
                
        
        user_blocks.sort(key=_sort_slots_on_time)
        
        user_blocks = self._handel_user_blocks_that_overlap(user_blocks)
        
        return user_blocks     

    
    def _find_empty_spaces_inside_slots(self,user_blocks):
        
        times_to_remove = []
            
        for (st,ed) in zip(self._start_dt_list,self._end_dt_list): 
                
            time_slot = []
                
            for block in user_blocks:
                        
                if (block.end_datetime - block.start_datetime) < (ed - st):
                    
                    if (block.start_datetime >= st and block.start_datetime < ed) and (block.end_datetime <= ed and block.end_datetime > st):
                            
                        time_slot.append(block)        
                
            if len(time_slot) > 1:
                
                uniqe_slots = []
                    
                for index ,slot in enumerate(time_slot):
                    
                    if index != 0:
                            
                        if time_slot[0].start_datetime == st:  
                                
                            current_start_datetime = time_slot[0].end_datetime
                            current_end_datetime = time_slot[1].start_datetime

                            if (current_start_datetime,current_end_datetime) not in uniqe_slots:

                                uniqe_slots.append((current_start_datetime,current_end_datetime))
                        
                        elif time_slot[0].start_datetime != st:
                            
                            current_start_datetime = st
                            current_end_datetime = time_slot[0].start_datetime

                            if (current_start_datetime,current_end_datetime) not in uniqe_slots:

                                uniqe_slots.append((current_start_datetime,current_end_datetime))
                                
                        if time_slot[-1].end_datetime != ed:
                            
                            current_start_datetime = time_slot[-1].end_datetime
                            current_end_datetime = ed

                            if (current_start_datetime,current_end_datetime) not in uniqe_slots:

                                uniqe_slots.append((current_start_datetime,current_end_datetime))
                        
                        if time_slot[index-1].end_datetime != slot.start_datetime:
                            
                                
                            current_start_datetime = time_slot[index-1].end_datetime
                            current_end_datetime = slot.start_datetime
                            
                            if (current_start_datetime,current_end_datetime) not in uniqe_slots:

                                uniqe_slots.append((current_start_datetime,current_end_datetime))
                                            
                    
                    if index == (len(time_slot) - 1): 
                        
                        times_to_remove.append((st,ed))
                                
                            
                for slot in uniqe_slots:
                        
                    self._start_dt_list.append(slot[0])
                    self._end_dt_list.append(slot[1])
                            
                        
            elif len(time_slot) == 1 and (time_slot[0].end_datetime - time_slot[0].start_datetime) < (ed - st):
                
                if time_slot[0].start_datetime == st:
                    
                    self._start_dt_list.append(time_slot[0].end_datetime)
                    self._end_dt_list.append(ed)
                    times_to_remove.append((st,ed))
                
                elif time_slot[0].end_datetime == ed:
                    
                    self._start_dt_list.append(st)
                    self._end_dt_list.append(time_slot[0].start_datetime)
                    times_to_remove.append((st,ed))
                    
                else:
                    
                    self._start_dt_list.append(st)
                    self._end_dt_list.append(time_slot[0].start_datetime)
                    self._start_dt_list.append(time_slot[0].end_datetime)
                    self._end_dt_list.append(ed)
                    times_to_remove.append((st,ed))
                    
                    
        for tp in times_to_remove:
            
            self._start_dt_list.remove(tp[0])
            self._end_dt_list.remove(tp[1])
            
            
    
    def _remove_occupied_slots_from_schedule(self,user_blocks):
    
        for block in user_blocks:

            if block.start_datetime in self._start_dt_list:
                        
                self._end_dt_list.pop(self._start_dt_list.index(block.start_datetime))
                self._start_dt_list.remove(block.start_datetime)
    
    
    def _check_for_blocks_out_of_scope(self, user_blocks):
        
        time_slots_to_remove = []
        
        for (st,ed) in zip(self._start_dt_list,self._end_dt_list):  
            
            top_block_fix_time = st
            end_block_fix_time = ed
                
            for block in user_blocks:
                    
                if not (block.start_datetime >= st and block.start_datetime < ed) and (block.end_datetime <= ed and block.end_datetime > st):
                    
                    if not ((st,ed)) in time_slots_to_remove:
                    
                        time_slots_to_remove.append((st,ed))
                    
                    top_block_fix_time = block.end_datetime
                
                elif (block.start_datetime >= st and block.start_datetime < ed) and not (block.end_datetime <= ed and block.end_datetime > st):
                    
                    if not ((st,ed)) in time_slots_to_remove:
                    
                        time_slots_to_remove.append((st,ed))
                    
                    end_block_fix_time = block.start_datetime
                
                else:
                    
                    if (block.start_datetime < st and block.end_datetime > ed) or (block.start_datetime <= st and block.end_datetime > ed) or (block.start_datetime < st and block.end_datetime >= ed):
                        
                        if not ((st,ed)) in time_slots_to_remove:
                        
                            time_slots_to_remove.append((st,ed))
            
            if top_block_fix_time != st or end_block_fix_time != ed:                    
                    
                self._start_dt_list.append(top_block_fix_time)
                self._end_dt_list.append(end_block_fix_time)

        
        for slot_to_remove in time_slots_to_remove:
            
            self._start_dt_list.remove(slot_to_remove[0])
            self._end_dt_list.remove(slot_to_remove[1])
        

    
    def _populate_schedule(self,id):
    
        user_blocks = self._get_user_blocks(id)
        start_dt = _change_awareness(self.start_datetime)
        end_dt = _change_awareness(datetime.combine(self.end_datetime,datetime.max.time()))
        total_work_time = int(id._get_work_days_data(self.start_datetime, self.end_datetime, compute_leaves=True)['hours'])
        
        for _ in range(total_work_time):

            closest_work, closest_work_end = self._get_worktimes(start_dt, end_dt,id)
            
            if closest_work == None and closest_work_end == None:
                continue
                        
            if start_dt < closest_work:
                start_dt = closest_work
                
            if not (_change_awareness(closest_work_end) in self._end_dt_list):    
                                    
                self._start_dt_list.append(_change_awareness(closest_work))
                self._end_dt_list.append(_change_awareness(closest_work_end))
            
            start_dt += (closest_work_end - closest_work)
        
        
        self._check_for_blocks_out_of_scope(user_blocks)
        
        self._start_dt_list.sort()
        self._end_dt_list.sort()
        
        self._find_empty_spaces_inside_slots(user_blocks)
            
        self._start_dt_list.sort()
        self._end_dt_list.sort()
            
        self._remove_occupied_slots_from_schedule(user_blocks)
        
        
            
    def time_allocator(self):
        
        split_time = self._split_times()
        work_time = self.hours_per_week / split_time
        
        for id in self.employee_ids:
        
            positions_to_be_placed = []
            work_time_delta = timedelta(hours=work_time)
                                    
            self._start_dt_list.clear()
            self._end_dt_list.clear()
                        
            self._populate_schedule(id)            
                        
            
            for (start_dt,end_dt) in zip(self._start_dt_list,self._end_dt_list):
                            
                dif = end_dt - start_dt
                                    
                positions_to_be_placed.append(dif)
                        
            
            while len(positions_to_be_placed) != 0 and work_time_delta >= positions_to_be_placed[0]:
                
                work_time_delta -= positions_to_be_placed[0]
                
                self._create_slots(positions_to_be_placed[0],id)
                
                positions_to_be_placed.pop(0)
                
            if work_time_delta > timedelta(hours=0):
                
                self._create_slots(work_time_delta,id)
        
        
    
    def _create_slot(self, employee, start_dt_no_tz, time_to_end):
    
        vals = [{
            'project_id': self.project_id.id,
            'employee_id': employee.id,
            'note': self.note,
            'start_datetime': start_dt_no_tz,
            'end_datetime': start_dt_no_tz + time_to_end,
            'contract_schema_time': self.contract_schema_time
            }]
                
        self.env['planner_ce.slot'].create(vals)
        

    def _create_slots(self, work_time, employee):
        
        self.end_datetime = (datetime.combine(self.end_datetime, datetime.max.time()))
        
        
        if len(self._start_dt_list) == 0 and len(self._nd_dt_list) == 0:
                        
            raise UserError(_("The work time is more then the emplyee contracted time betwen start and end time or the times you have chosen dose not contain any work time, pleas change the work time."))
            
        closest_work = self._start_dt_list[0]        


        while work_time != timedelta(hours=0):

            if work_time >= timedelta(hours=2):

                self._create_slot(employee, closest_work, timedelta(hours=2))
                
                work_time -= timedelta(hours=2)    
                closest_work += timedelta(hours=2)
            
            else:
                
                self._create_slot(employee, closest_work, work_time)
                work_time = timedelta(hours=0)

        self._start_dt_list.pop(0)
        self._end_dt_list.pop(0)