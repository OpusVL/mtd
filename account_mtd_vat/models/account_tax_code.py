# -*- coding = utf-8 -*-
import logging

from openerp import models, fields, api, _
from openerp.osv import fields, osv, expression



class mtd_account_tax_code(osv.osv):
    _inherit = "account.tax.code"

    def move_line_domain(self, cr, uid,
            tax_code_id, entry_state_filter, date_from, date_to, company_id,
            vat_filter, as_string=False):
        """
        vat_filter: String 'True' or 'False' to filter, falsey value if we
            don't care
        entry_state_filter: 'all' or 'posted'
        """
        assert state_filter in ('all', 'posted'), "Invalid state_filter"
        wanted_journal_entry_states = \
            ('draft', 'posted') if entry_state_filter == 'all' else ('posted',)
        domain = [
            ('state', '!=', 'draft'),
            ('account_move_id.state', 'in', wanted_journal_entry_states),
            ('tax_code_id', 'child_of', tax_code_id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ]
        if vat_filter:  # TODO use 'all' for all like with state_filter
            assert vat_filter in ('True', 'False'), \
                "Invalid value {!r} for vat_filter".format(vat_filter)
            wanted_vat_value = (vat_filter == 'True')
            domain.append(('vat', '=', wanted_vat_value))
        # TODO see if action.domain in JS can cope with data structure
        #  instead of string, in which case this nasty hack isn't needed
        return repr(domain) if as_string else domain

    def _update_box_9_tax_code_scope(self, cr, uid):
        context = {}
        context['code'] = 9
        account_tax_code_9_obj = self.pool['account.tax.code'].search(cr, uid, [('code', '=', '9')])
        for rec in account_tax_code_9_obj:
            box9_rec = self.pool['account.tax.code'].browse(cr, uid, rec)
            account_tax_code_7_obj = self.pool['account.tax.code'].search(cr, uid, [('code', '=', '7'),('company_id', '=', box9_rec.company_id.id)])
            box9_rec.parent_id = account_tax_code_7_obj[0]
            box9_rec.sign = 1

        return True

    def _sum_year(self, cr, uid, ids, name, args, context=None):
        if context is None:
            context = {}
        move_state = ('posted',)
        if context.get('state', 'all') == 'all':
            move_state = ('draft', 'posted',)
        if context.get('fiscalyear_id', False):
            if len(context['fiscalyear_id']) > 1:
                fiscalyear_id = context['fiscalyear_id']
            else:
                fiscalyear_id = [context['fiscalyear_id']]
        else:
            fiscalyear_id = self.pool.get('account.fiscalyear').finds(cr, uid, exception=False)

        vat = ''
        if 'vat' in context.keys() and context['vat'] != "":
            vat = False
            if context['vat'] == 'True':
                vat = True
        date_from = None
        date_to = None
        company_id = None
        if 'date_from' in context.keys():
            date_from = context['date_from']
        if 'date_to' in context.keys():
            date_to = context['date_to']
        if 'company_id' in context.keys():
            company_id = context['company_id']

        where = ''
        where_params = ()
        if fiscalyear_id:
            pids = []
            for fy in fiscalyear_id:
                pids += map(lambda x: str(x.id), self.pool.get('account.fiscalyear').browse(cr, uid, fy).period_ids)
            if pids:
                if vat == '':
                    where = ' AND line.date >= %s AND line.date <= %s AND move.state IN %s  AND line.company_id = %s'
                    where_params = (date_from, date_to, move_state, company_id)
                else:
                    where = ' AND line.date >= %s AND line.date <= %s AND move.state IN %s AND line.vat = %s  AND line.company_id = %s'
                    where_params = (date_from, date_to, move_state, vat, company_id)

        return self._sum(
            cr,
            uid,
            ids,
            name,
            args,
            context,
            where=where,
            where_params=where_params
        )

    def _sum(self, cr, uid, ids, name, args, context, where='', where_params=()):
        parent_ids = tuple(self.search(cr, uid, [('parent_id', 'child_of', ids)]))
        if context.get('based_on', 'invoices') == 'payments':
            cr.execute('SELECT line.tax_code_id, sum(line.tax_amount) \
                    FROM account_move_line AS line, \
                        account_move AS move \
                        LEFT JOIN account_invoice invoice ON \
                            (invoice.move_id = move.id) \
                    WHERE line.tax_code_id IN %s '+where+' \
                        AND move.id = line.move_id \
                        AND ((invoice.state = \'paid\') \
                        OR (invoice.id IS NULL)) \
                        GROUP BY line.tax_code_id',
                        (parent_ids,) + where_params)
        else:
            cr.execute('SELECT line.tax_code_id, sum(line.tax_amount) \
                    FROM account_move_line AS line, \
                    account_move AS move \
                    WHERE line.tax_code_id IN %s '+where+' \
                    AND move.id = line.move_id \
                    GROUP BY line.tax_code_id',
                       (parent_ids,) + where_params)
        res = dict(cr.fetchall())
        obj_precision = self.pool.get('decimal.precision')
        res2 = {}
        for record in self.browse(cr, uid, ids, context=context):
            def _rec_get(record):
                amount = res.get(record.id) or 0.0
                for rec in record.child_ids:
                    amount += _rec_get(rec) * rec.sign
                return amount
            res2[record.id] = round(_rec_get(record), obj_precision.precision_get(cr, uid, 'Account'))

        if 'calculate_vat' in context.keys():
            if context.get('based_on', 'invoices') == 'payments':
                cr.execute('SELECT line.tax_code_id, sum(line.tax_amount) as amount, \
                        sum(line.mtd_tax_amount) as mtd_amount FROM account_move_line AS line, \
                            account_move AS move \
                            LEFT JOIN account_invoice invoice ON \
                                (invoice.move_id = move.id) \
                        WHERE line.tax_code_id IN %s ' + where + ' \
                            AND move.id = line.move_id \
                            AND ((invoice.state = \'paid\') \
                                OR (invoice.id IS NULL)) \
                                GROUP BY line.tax_code_id',
                           (parent_ids,) + where_params)
            else:
                cr.execute('SELECT line.tax_code_id, sum(line.tax_amount), \
                    sum(mtd_tax_amount) as mtd_sum  \
                    FROM account_move_line AS line, \
                    account_move as move \
                    WHERE line.tax_code_id IN %s '+where+' \
                    AND move.id = line.move_id \
                    GROUP BY line.tax_code_id',
                    (parent_ids,) + where_params)
            compare_dict = {}
            for row in cr.fetchall():

                compare_dict[row[0]]=[row[1], row[2]]
            return res2, compare_dict
        return res2

    def _sum_period(self, cr, uid, ids, name, args, context):
        if context is None:
            context = {}
        move_state = ('posted',)
        if context.get('state', False) == 'all':
            move_state = ('draft', 'posted',)
        if context.get('period_id', False):
            period_id = context['period_id']
        else:
            period_id = self.pool.get('account.period').find(cr, uid, context=context)
            if not period_id:
                return dict.fromkeys(ids, 0.0)
            period_id = [period_id[0]]
        vat = ''
        if 'vat' in context.keys() and context['vat'] != "":
            vat = False
            if context['vat'] == 'True':
                vat = True
        date_from = None
        date_to = None
        company_id = None
        if 'date_from' in context.keys():
            date_from = context['date_from']
        if 'date_to' in context.keys():
            date_to = context['date_to']
        if 'company_id' in context.keys():
            company_id = context['company_id']
        if vat == "":
            return self._sum(
                cr,
                uid,
                ids,
                name,
                args,
                context,
                where=' AND line.date >= %s AND line.date <= %s AND move.state IN %s AND line.company_id = %s',
                where_params=(date_from, date_to, move_state, company_id)
            )
        else:
            return self._sum(
                cr,
                uid,
                ids,
                name,
                args,
                context,
                where=' AND line.date >= %s AND line.date <= %s AND move.state IN %s AND line.vat = %s AND line.company_id = %s',
                where_params=(date_from, date_to, move_state, vat, company_id)
            )

    _columns = {
        'sum': fields.function(_sum_year, string="Year Sum"),
        'sum_period': fields.function(_sum_period, string="Period Sum")
    }
