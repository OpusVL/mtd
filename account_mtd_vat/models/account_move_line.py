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

    def _sum_of_tax_amounts(self, cr, uid, ids, context=None):
        """Return sum of tax_amounts for ids, unrounded.

        You will need to use decimal precision stuff to round to 'Account'
        accuracy when you are done with any further computations you wish
        to do on the result.
        """
        if ids:
            sql = """
                SELECT SUM(tax_amount)
                FROM account_move_line
                WHERE id in %s
            """
            params = (tuple(ids),)
            cr.execute(sql, params)
            (total_tax,) = cr.fetchone()
            return total_tax
        else:
            # "in ()" in SQL not valid
            return 0.0

    _columns = {
        'vat': fields.boolean(string="VAT Posted", default=False, readonly=True),
        'vat_submission_id': fields.many2one('mtd_vat.vat_submission_logs', string='VAT Submission Period'),
        'unique_number': fields.related(
            'vat_submission_id',
            'unique_number',
            type='char',
            string="HMRC Unique Number",
            store=True,
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
            ('yes', 'Yes'),
            ('no', 'No'),
            ('all', 'All')],
            'VAT Posted',
            required=True,
            default='no'),
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

        vat = ''
        if data.vat_posted == 'yes':
            vat = 'True'
        elif data.vat_posted == 'no':
            vat = 'False'

        context = result['context']
        new_context = ast.literal_eval(context)
        new_context['company_id'] = data.company_id.id
        new_context['date_from'] = date_from
        new_context["date_to"] = data.date_to
        new_context['period_id'] = period_ids
        new_context['vat'] = vat
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
