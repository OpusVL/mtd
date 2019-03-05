# -*- coding = utf-8 -*-
import logging


from openerp.osv import fields, osv

class account_move_line(osv.osv):
    _inherit = "account.move.line"

    _columns ={
        'vat' : fields.boolean(string="VAT", default=False, readonly=True)
    }