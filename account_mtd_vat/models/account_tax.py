# -*- coding = utf-8 -*-

import logging

from odoo.osv import osv
from odoo import fields, api, models


class MtdAccountTaxCode(osv.osv):
    _inherit = "account.tax"

    vat_tax_scope = fields.Selection([
        ('ST', 'ST'),
        ('PT', 'PT'),
        ('PTR', 'PTR'),
        ('PTM', 'PTM')
    ], string="UK VAT Scope")

    def _update_vat_tax_scope(self):
        for record in self:
            if record.description == 'PT8M':
                record.vat_tax_scope = 'PTM'
            elif record.description == 'PT8R':
                record.vat_tax_scope = 'PTR'
            elif record.description.startswith('ST'):  # in ('ST0', 'ST1', 'ST11', 'ST2', 'ST4'):
                record.vat_tax_scope = 'ST'
            elif record.description.startswith('PT'):  # in ('PT0', 'PT1', 'PT11', 'PT2', 'PT5', 'PT7', 'PT8'):
                record.vat_tax_scope = 'PT'
        return True
