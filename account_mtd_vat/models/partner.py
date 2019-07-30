from operator import itemgetter
import time

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp import api


class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Partner'

    def has_something_to_reconcile(self, cr, uid, partner_id, context=None):
        '''
        at least a debit, a credit and a line older than the last reconciliation date of the partner
        '''
        cr.execute('''
            SELECT l.partner_id, SUM(l.debit) AS debit, SUM(l.credit) AS credit
            FROM account_move_line l
            RIGHT JOIN account_account a ON (a.id = l.account_id)
            RIGHT JOIN res_partner p ON (l.partner_id = p.id)
            WHERE a.is_reconcilable_by_user IS TRUE
            AND p.id = %s
            AND l.reconcile_id IS NULL
            AND (p.last_reconciliation_date IS NULL OR l.date > p.last_reconciliation_date)
            AND l.state <> 'draft'
            GROUP BY l.partner_id''', (partner_id,))
        res = cr.dictfetchone()
        if res:
            return bool(res['debit'] and res['credit'])
        return False
