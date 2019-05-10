# -*- coding = utf-8 -*-

import logging

from odoo.osv import osv
from odoo import fields


class mtd_account_tax_code(osv.osv):
    _inherit = "account.tax.code"

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

        where = ''
        where_params = ()
        if fiscalyear_id:
            pids = []
            for fy in fiscalyear_id:
                pids += map(lambda x: str(x.id), self.pool.get('account.fiscalyear').browse(cr, uid, fy).period_ids)
            if pids:
                if vat == '':
                    where = ' AND line.period_id IN %s AND move.state IN %s '
                    where_params = (tuple(pids), move_state)
                else:
                    where = ' AND line.period_id IN %s AND move.state IN %s AND line.vat = %s '
                    where_params = (tuple(pids), move_state, vat)

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

        mtd_sum = super(mtd_account_tax_code, self)._sum(
            cr,
            uid,
            ids,
            name,
            args,
            context,
            where=where,
            where_params=where_params
        )

        return mtd_sum

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

        if vat == "":
            return self._sum(
                cr,
                uid,
                ids,
                name,
                args,
                context,
                where=' AND line.period_id IN %s AND move.state IN %s',
                where_params=(tuple(period_id), move_state)
            )
        else:
            return self._sum(
                cr,
                uid,
                ids,
                name,
                args,
                context,
                where=' AND line.period_id IN %s AND move.state IN %s AND line.vat = %s',
                where_params=(tuple(period_id), move_state, vat)
            )

    # sum = fields.function(_sum_year, string="Year Sum"),
    # sum_period = fields.function(_sum_period, string="Period Sum")
