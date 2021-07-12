# -*- coding: utf-8 -*-

##############################################################################
#
# Making Tax Digital for VAT
# Copyright (C) 2019 OpusVL (<http://opusvl.com/>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'UK HMRC MTD - Connector',
    'version': '0.8',
    'author': 'OpusVL',
    'website': 'https://opusvl.com/',
    'summary': 'This module enables Odoo Community and Enterprise to establish an authenticated connection to the HMRC’s Making Tax Digital platform.',
    'category': 'accounting',
    'description': 'HMRC now require VAT submissions to be made via their on-line automated service for all UK VAT registered businesses. The purpose of this module is to securely connect to HMRC and provide the HMRC connection required for Making Tax Digital. ',
    'images': ['static/description/MTD-Connector.png'
    ],
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'data/api_scope.xml',
        'views/res_company_view.xml',
        'views/webclient_templates.xml',
        'views/mtd_menu.xml',
        'views/hmrc_configuration_view.xml',
        'views/hello_world_view.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'test': [
    ],
    'application': True,
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
