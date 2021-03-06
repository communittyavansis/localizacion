# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
# Copyright (c) 2013 Interconsulting S.A. e Innovatecsa SAS.  (http://interconsulting.com.co).
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
{
    'name': 'Planeacion Nómina Colombiana',
    'version': '1.0',
    'author': ' Interconsulting S.A - Innovatecsa SAS.',
    'category': 'Generic Modules/Human Resources',
    'depends': ['hr_payroll'],
    'demo': [],
    'description': """
Módulo de planeacion de nómina para la localización colombiana empresas de vigilancia
    """,
    'data': [
       'hr_payroll_co_planning_view.xml', 
       'warning.xml',
    ],
    'auto_install': False,
    'installable': True,
    'images': ['./vigilante.jpg'],

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
