# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo SA, Open Source Management Solution, third party addon
#    Copyright (C) 2022- Vertel AB (<https://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# TODO: Fix module image!

{
    'name': 'Planning: Day Tasks',
    'version': '14.0.2.1.0',
    # Version ledger: 14.0 = Odoo version. 1 = Major. Non regressionable code. 2 = Minor. New features that are regressionable. 3 = Bug fixes
    'summary': '',
    'category': 'Administration',
    'description': """
    """,
    #'sequence': '1',
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-planning/planning_day_tasks',
    'images': ['static/description/banner.png'], # 560x280 px.
    'license': 'AGPL-3',
    'contributor': '',
    'maintainer': 'Vertel AB',
    'repository': 'https://github.com/vertelab/odoo-planning',
    'depends': ['project', 'hr', 'hr_timesheet', "calendar"],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/day_plan.xml',
        'views/activity_view.xml',
        'views/task_view.xml',
        'data/cron.xml',
        # 'wizard/planning_wizard.xml',
    ]
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
