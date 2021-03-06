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
    'name': 'UK HMRC MTD - VAT',
    'version': '0.16',
    'author': 'OpusVL',
    'website': 'https://opusvl.com/',
    'summary': 'This module enables the collation and transmission of VAT data from Odoo to HMRC in line with Making Tax Digital requirements. From your sales and purchases in Odoo, your VAT liability is automatically calculated and submitted to HMRC.',
    'category': 'accounting',
    'description': 'The purpose of this module is to allow Odoo accounting to be used seamlessly in the UK alongside the changes by HMRC in their policy on VAT submission requirements. From April 2019, all UK VAT registered businesses must submit their VAT returns electronically.',
    'images': ['static/description/MTD-Cover-Image.png'],
    'depends': [
        'base',
        'account_mtd',
        'account',
    ],
    'data': [
        'data/account_tax_code_scope.xml',
        'data/vat_api_scope.xml',

        'security/groups.xml',
        'security/ir.model.access.csv',
        # 'security/user_access_rules.xml',
        'views/account_move_line_view.xml',
        'views/account_tax_code_view.xml',
        'views/mtd_vat_endpoint_view.xml',
        'views/mtd_vat_menu.xml',
        'views/mtd_vat_obligation_logs_list_view.xml',
        'views/mtd_vat_submission_logs_view.xml',
        'views/mtd_vat_detailed_submission_logs_view.xml',
        'views/hmrc_posting_configuration_view.xml',
        'views/res_company_view.xml',
        'views/webclient_templates.xml'

    ],
    'demo': [
        'demo/account_invoice.xml',
    ],
    'test': [
    ],
    'application': True,
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'price': 550,
    'currency': 'EUR'

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
