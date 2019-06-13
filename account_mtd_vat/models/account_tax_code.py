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

    def _move_line_ids_for_chart_of_taxes_rows(self, cr, uid, ids, context):
        return frozenset().union(*[
            self._move_line_ids_for_chart_of_taxes_row(
                cr, uid, tax_code_id, context=context)
            for tax_code_id in ids
        ])

    _columns = {
        'sum': fields.function(_sum_year, string="Year Sum"),
        'sum_period': fields.function(_sum_period, string="Period Sum")
    }
