# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo SA, Open Source Management Solution, third party addon
#    Copyright (C) 2022- Vertel Sverige AB (<https://vertel.se>).
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
    'name': 'Planning: For Projects',
    'version': '18.0.1.1.1',
    # Version ledger: 14.0 = Odoo version. 1 = Major. Non regressionable code. 2 = Minor. New features that are regressionable. 3 = Bug fixes
    'summary': "Adds project planning to the planner.",
    'category': 'Project',
    'description': '''
For Projects
============

    More information:
    Make sure that the working schedule have the correct timezone

    Features:

        - Guided Wizards: Step-by-step dialogs for data entry.
        - UI Integration: Extends 4 view(s) in the Odoo interface.
    ''',
    #'sequence': '1',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-planning/planner_project',
    'images': ['static/description/icon_vertel.png'], # 560x280 px.
    'license': 'AGPL-3',
    'contributor': '',
    'maintainer': 'Vertel Sverige AB',
    'repository': 'https://github.com/vertelab/odoo-planning',
    'depends': ['project','planning_ce',],
    'data': [
        # 'views/project_view.xml',
        #'views/planning_slot_view.xml',
        #'views/bulk_planning_view.xml',
        'security/ir.model.access.csv',
        'wizard/project_button_wizard.xml',
        'views/project_planning.xml',
    ],
    'auto_install': False,
}
