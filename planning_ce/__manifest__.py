# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2021- Vertel AB (<http://vertel.se>).
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Planning CE',
    'version': '13.0.1.3.0',
    'category': 'Project Timeline',
    'description': """
Using Timeline to plan the work in a team
=================================================

More information:
    """,
    'author': 'Vertel AB',
    'license': 'AGPL-3',
    'website': 'http://www.vertel.se',
    'depends': ['hr', 'project', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/planning_role_view.xml',
        'views/planning_slot_view.xml',
        'views/hr_view.xml',
        'views/project_view.xml',
       ],
    'installable': True,
}
