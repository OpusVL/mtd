# -*- coding = utf-8 -*-
import logging


from openerp.osv import fields, osv

class account_move_line(osv.osv):
    _inherit = "account.move.line"

    _columns ={
        'vat' : fields.boolean(string="VAT Posted", default=False, readonly=True),
        'vat_submission_id' : fields.many2one('mtd_vat.vat_submission_logs', readonly=True),
        'unique_number' : fields.related('vat_submission_id',
            'unique_number',
            type='char',
            string="HMRC Unique Number",
            store=True,
            readonly=True)
    }