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

{
    'name': 'Planning: CE',
    'version': '14.0.1.1.0',
    # Version ledger: 14.0 = Odoo version. 1 = Major. Non regressionable code. 2 = Minor. New features that are regressionable. 3 = Bug fixes
    'summary': '',
    'category': 'Project',
    'description': """
Using Timeline to plan the work in a team
=================================================

More information:
    """,
    #'sequence': '1',
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-planning/planning_ce',
    'images': ['static/description/banner.png'], # 560x280 px.
    'license': 'AGPL-3',
    'contributor': '',
    'maintainer': 'Vertel AB',
    'repository': 'https://github.com/vertelab/odoo-planning',
    #'depends': ['hr', 'project', 'sale', 'web_timeline', 'hr_timesheet', 'hr_contract'],
    #sale- behövs inte för den gör inget?
    #hr_timesheet - inherits och xml fält, vill vi ha kvar den? är för roler
    #hr- behövs pga employee, samankoplad med hr_contract
    #hr_contract- smankoplad med hr, funkar utan? NOPPE
    #web_timeline- behövs för visalusering och date_start/date_stop
    #project- behövs pga att vi behöver(?) projekt för att göra planering?
    'depends': ['hr', 'web_timeline', 'portal', 'hr_contract', 'hr_timesheet'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/planning_role_view.xml',
        'views/planning_slot_view.xml',
        'views/planning_report_views.xml',
        'views/hr_view.xml',
        'views/project_view.xml',
        'wizard/planning_compare_wizard_view.xml',
        #'views/bulk_planning_view.xml',
        #'wizard/planning_slot_wizard_view.xml',
       ],
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
