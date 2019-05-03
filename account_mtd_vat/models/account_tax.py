# -*- coding = utf-8 -*-
import logging


from odoo.osv import osv
from odoo import fields


class MtdAccountTaxCode(osv.osv):
    _inherit = "account.tax"

    vat_tax_scope = fields.Selection([
        ('ST', 'ST'),
        ('PT', 'PT'),
        ('PTR', 'PTR'),
        ('PTM', 'PTM'
                '')
    ], string="UK VAT Scope")
