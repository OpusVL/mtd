# -*- coding = utf-8 -*-
import logging
import json
import ast
import openerp.addons.decimal_precision as dp

from openerp import models, fields, api, _
from openerp.osv import fields, osv
from openerp import exceptions


class account_move_line(osv.osv):
    _inherit = "account.move.line"

    @api.one
    @api.depends('credit', 'debit', 'tax_code_id')
    def _compute_tax_base_values_for_manual_journal_items(self):
        if self.tax_code_id:
            if self.tax_code_id.code in ('1', '6', '8'):
                self.mtd_tax_amount = (self.credit - self.debit)
            elif self.tax_code_id.code in ('2', '9', '7'):
                self.mtd_tax_amount = (self.debit - self.credit)
            elif self.tax_code_id.code == '4':
                self.mtd_tax_amount = (self.debit - self.credit)
                journal_entry_obj = self.env['account.move.line'].search([('move_id', '=', self.move_id.id)])
                if journal_entry_obj:
                    for line in journal_entry_obj:
                        if line.tax_code_id.code == '2':
                            self.mtd_tax_amount = (self.credit - self.debit)
        else:
            self.mtd_tax_amount = 0.00

    def list_partners_to_reconcile(self, cr, uid, context=None, filter_domain=False):
        # Note this will ignore reconciliation_allowed_on_all_accounts in the
        # context.  If we need to not ignore it, you need to not include
        # the non_mtd_reconcilable clause from WHERE if that context is True.
        line_ids = []
        if filter_domain:
            line_ids = self.search(cr, uid, filter_domain, context=context)
        where_clause = filter_domain and "AND l.id = ANY(%s)" or ""
        cr.execute(
             """SELECT partner_id FROM (
                SELECT l.partner_id, p.last_reconciliation_date, SUM(l.debit) AS debit, SUM(l.credit) AS credit, MAX(l.create_date) AS max_date
                FROM account_move_line l
                RIGHT JOIN account_account a ON (a.id = l.account_id)
                RIGHT JOIN res_partner p ON (l.partner_id = p.id)
                    WHERE a.non_mtd_reconcilable IS TRUE
                    AND l.reconcile_id IS NULL
                    AND l.state <> 'draft'
                    %s
                    GROUP BY l.partner_id, p.last_reconciliation_date
                ) AS s
                WHERE debit > 0 AND credit > 0 AND (last_reconciliation_date IS NULL OR max_date > last_reconciliation_date)
                ORDER BY last_reconciliation_date"""
            % where_clause, (line_ids,))
        ids = [x[0] for x in cr.fetchall()]
        if not ids:
            return []

        # To apply the ir_rules
        partner_obj = self.pool.get('res.partner')
        ids = partner_obj.search(cr, uid, [('id', 'in', ids)], context=context)
        return partner_obj.name_get(cr, uid, ids, context=context)

    _columns = {
        'vat': fields.boolean(string="VAT Posted", default=False, readonly=True),
        'vat_submission_id': fields.many2one('mtd_vat.vat_submission_logs', string='VAT Submission Period'),
        'unique_number': fields.related(
            'vat_submission_id',
            'unique_number',
            type='char',
            string="HMRC Unique Number",
            readonly=True
        ),
        'mtd_tax_amount': fields.float(
            'Mtd Tax/Base Amount',
            compute="_compute_tax_base_values_for_manual_journal_items",
            digits=dp.get_precision('Account'),
            store=True
        )
    }


class account_tax_chart(osv.osv_memory):
    _inherit = "account.tax.chart"

    _columns = {
        'date_from': fields.date(string='Effective date from'),
        'date_to': fields.date(string='Effective date to'),
        'company_id': fields.many2one('res.company', 'Company'),
        'vat_posted': fields.selection([
            ('posted', 'Yes'),
            ('unposted', 'No'),
            ('all', 'All')],
            'VAT Posted',
            required=True,
            default='unposted'),
        'previous_period': fields.selection([
            ('yes', 'Yes'),
            ('no', 'No')],
            'Include Transaction of Previous period',
            required=True,
            default='no')
    }

    def account_tax_chart_open_window(self, cr, uid, ids, context=None):
        result = super(account_tax_chart, self).account_tax_chart_open_window(cr, uid, ids, context=context)
        # Get the record to access the information provided by the user
        data = self.browse(cr, uid, ids, context=context)[0]
        period_ids = [data.period_id.id]
        fiscalyear_ids = [data.period_id.fiscalyear_id.id]
        date_from = data.date_from

        if data.previous_period == 'yes':
            cutoff_date_rec = self.pool.get('mtd_vat.hmrc_posting_configuration').search(cr, uid, [
                ('name', '=', data.period_id.company_id.id)])
            if cutoff_date_rec:
                date_from = self.pool.get('mtd_vat.hmrc_posting_configuration').browse(
                    cr,
                    uid,
                    cutoff_date_rec,
                    context=context).cutoff_date
            else:
                raise exceptions.Warning(
                    "Chart of Taxes can not be generated!\nPlease create HMRC Posting Templae record first \n" +
                    "HMRC Posting Tempale can be generated from 'Accounting/Configuration/Miscellaneous/HMRC " +
                    "Posting Template' "
                )
            fiscalyear_ids = []
            for period in period_ids:
                fiscalyear_id = self.pool.get('account.period').browse(cr, uid, period).fiscalyear_id.id
                if fiscalyear_id not in fiscalyear_ids:
                    fiscalyear_ids.append(fiscalyear_id)

        context = result['context']
        new_context = ast.literal_eval(context)
        new_context['company_id'] = data.company_id.id
        new_context['date_from'] = date_from
        new_context["date_to"] = data.date_to
        new_context['period_id'] = period_ids
        new_context['vat'] = data.vat_posted
        new_context['fiscalyear_id'] = fiscalyear_ids
        result['context'] = new_context

        return result


class account_move(osv.osv):
    _inherit = "account.move"

    def button_cancel(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context):
            for item in line.line_id:
                if item.vat:
                    raise exceptions.Warning('You cannot modify a vat posted entry of this journal.')

        result = super(account_move, self).button_cancel(cr, uid, ids, context=context)
        return result
