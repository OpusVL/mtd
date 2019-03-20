# -*- coding = utf-8 -*-
import logging
import json


from openerp.osv import fields, osv
from openerp import exceptions


class account_move_line(osv.osv):
    _inherit = "account.move.line"

    _columns ={
        'vat' : fields.boolean(string="VAT Posted", default=False, readonly=True),
        'vat_submission_id' : fields.many2one('mtd_vat.vat_submission_logs', string='VAT Submission Period'),
        'unique_number' : fields.related('vat_submission_id',
            'unique_number',
            type='char',
            string="HMRC Unique Number",
            store=True,
            readonly=True)
    }



class account_move(osv.osv):
    _inherit = "account.move"

    def button_cancel(self, cr, uid, ids, context=None):
        import pdb; pdb.set_trace()

        for line in self.browse(cr, uid, ids, context):
            for item in line.line_id:
                if item.vat:
                    raise exceptions.Warning('You cannot modify a vat posted entry of this journal.')

        result = super(account_move, self).button_cancel(cr, uid, ids, context=context)
        return result
