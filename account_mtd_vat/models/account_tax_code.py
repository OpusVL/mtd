# -*- coding = utf-8 -*-
import logging

from openerp import models, fields, api, _, exceptions
from openerp.osv import fields, osv, expression

LOG = logging.getLogger(__name__)

class mtd_account_tax_code(osv.osv):
    _inherit = "account.tax.code"

    def move_line_domain_for_chart_of_taxes_row(self, cr, uid, tax_code_id,
            context):
        """
        tax_code_id: int
        context: must contain at least keys:
          date_to: string in format %Y-%m-%d
          date_from: string in format %Y-%m-%d
          company_id: int
          vat: 'all', 'posted' or 'unposted'
          state: 'all' or 'posted' (required journal entry states)
        """
        # This method is and should remain a pure function on tax_code_id and
        # context.
        # We accept cr, uid purely to make the javascript openerp.Model call
        # happy

        def param_or_user_error(ctx, key):
            try:
                return ctx[key]
            except KeyError:
                headline = "Missing parameters for chart of taxes."
                LOG.exception("%s  See exception." % (headline,))
                raise exceptions.Warning(
                    "%s\n"
                    "This is usually caused by refreshing the webpage from a"
                    " previous chart of taxes report." % (headline,)
                )

        entry_state_filter = param_or_user_error(context, 'state')
        assert entry_state_filter in ('all', 'posted'), "Invalid state_filter"
        wanted_journal_entry_states = \
            ('draft', 'posted') if entry_state_filter == 'all' \
                else ('posted',)
        domain = [
            ('state', '!=', 'draft'),
            ('move_id.state', 'in', wanted_journal_entry_states),
            ('tax_code_id', 'child_of', tax_code_id),
            ('company_id', '=', param_or_user_error(context, 'company_id')),
            ('date', '>=', param_or_user_error(context, 'date_from')),
            ('date', '<=', param_or_user_error(context, 'date_to')),
        ]
        vat_clauses = {
            'posted': [('vat', '=', True)],
            'unposted': [('vat', '=', False)],
            'all': [],
        }
        vat_filter = param_or_user_error(context, 'vat')
        domain += vat_clauses[vat_filter]
        return domain

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
        # TODO does this need same treatment as _sum_period?
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
            # TODO split this out as it's not going to work on new scheme (
            #  probably)
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
        # TODO missing test
        # The algorithm from Odoo core might be slightly more efficient,
        # but owing to bug O1851 I'm trading a little speed for detail/sum
        # parity.
        # In practice, the chart of taxes is only going to be quite small
        # so repeating something reasonably quick 8 times probably isn't an
        # issue.
        move_line_ids = self._move_line_ids_for_chart_of_taxes_rows(
                cr, uid, ids, context)
        if move_line_ids:
            return self._sum(cr, uid, ids, name, args, context,
                where='AND line.id IN %s',
                where_params=(tuple(move_line_ids),),
            )
        else:
            # "IN ()" invalid in SQL
            all_zeros = {id_: 0.0 for id_ in ids}
            return all_zeros

    def _move_line_ids_for_chart_of_taxes_row(self, cr, uid, tax_code_id, context):
        move_line_domain = self.move_line_domain_for_chart_of_taxes_row(
            cr, uid, tax_code_id=tax_code_id, context=context,
        )
        move_line_obj = self.pool['account.move.line']
        move_line_ids = move_line_obj.search(
            cr, uid, move_line_domain, context=context)
        return move_line_ids


    _columns = {
        'sum': fields.function(_sum_year, string="Year Sum"),
        'sum_period': fields.function(_sum_period, string="Period Sum")
    }
