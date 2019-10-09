# -*- coding = utf-8 -*-
import logging
import json
import ast
import openerp.addons.decimal_precision as dp

from openerp import models, fields, api, workflow, _
from openerp.osv import fields, osv
from openerp import exceptions
import time
from datetime import datetime


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

    # Override of the base function reconcile , removing the control for the account if is field reconciled checked or not
    def mtd_reconcile(self, cr, uid, ids, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False, context=None):
        account_obj = self.pool.get('account.account')
        move_obj = self.pool.get('account.move')
        move_rec_obj = self.pool.get('account.move.reconcile')
        partner_obj = self.pool.get('res.partner')
        currency_obj = self.pool.get('res.currency')
        lines = self.browse(cr, uid, ids, context=context)
        unrec_lines = filter(lambda x: not x['reconcile_id'], lines)
        credit = debit = 0.0
        currency = 0.0
        account_id = False
        partner_id = False
        if context is None:
            context = {}
        company_list = []
        for line in lines:
            if company_list and not line.company_id.id in company_list:
                raise osv.except_osv(_('Warning!'), _('To reconcile the entries company should be the same for all entries.'))
            company_list.append(line.company_id.id)
        for line in unrec_lines:
            if line.state != 'valid':
                raise osv.except_osv(_('Error!'),
                        _('Entry "%s" is not valid !') % line.name)
            credit += line['credit']
            debit += line['debit']
            currency += line['amount_currency'] or 0.0
            account_id = line['account_id']['id']
            partner_id = (line['partner_id'] and line['partner_id']['id']) or False
        writeoff = debit - credit

        # Ifdate_p in context => take this date
        if context.has_key('date_p') and context['date_p']:
            date=context['date_p']
        else:
            date = time.strftime('%Y-%m-%d')

        cr.execute('SELECT account_id, reconcile_id '\
                   'FROM account_move_line '\
                   'WHERE id IN %s '\
                   'GROUP BY account_id,reconcile_id',
                   (tuple(ids), ))
        r = cr.fetchall()
        #TODO: move this check to a constraint in the account_move_reconcile object
        if len(r) != 1:
            raise osv.except_osv(_('Error'), _('Entries are not of the same account or already reconciled ! '))
        if not unrec_lines:
            raise osv.except_osv(_('Error!'), _('Entry is already reconciled.'))
        account = account_obj.browse(cr, uid, account_id, context=context)
        if r[0][1] != None:
            raise osv.except_osv(_('Error!'), _('Some entries are already reconciled.'))

        if (not currency_obj.is_zero(cr, uid, account.company_id.currency_id, writeoff)) or \
           (account.currency_id and (not currency_obj.is_zero(cr, uid, account.currency_id, currency))):
            # DO NOT FORWARD PORT
            if not writeoff_acc_id:
                if writeoff > 0:
                    writeoff_acc_id = account.company_id.expense_currency_exchange_account_id.id
                else:
                    writeoff_acc_id = account.company_id.income_currency_exchange_account_id.id
            if not writeoff_acc_id:
                raise osv.except_osv(_('Warning!'), _('You have to provide an account for the write off/exchange difference entry.'))
            if writeoff > 0:
                debit = writeoff
                credit = 0.0
                self_credit = writeoff
                self_debit = 0.0
            else:
                debit = 0.0
                credit = -writeoff
                self_credit = 0.0
                self_debit = -writeoff
            # If comment exist in context, take it
            if 'comment' in context and context['comment']:
                libelle = context['comment']
            else:
                libelle = _('Write-Off')

            cur_obj = self.pool.get('res.currency')
            cur_id = False
            amount_currency_writeoff = 0.0
            if context.get('company_currency_id',False) != context.get('currency_id',False):
                cur_id = context.get('currency_id',False)
                for line in unrec_lines:
                    if line.currency_id and line.currency_id.id == context.get('currency_id',False):
                        amount_currency_writeoff += line.amount_currency
                    else:
                        tmp_amount = cur_obj.compute(cr, uid, line.account_id.company_id.currency_id.id, context.get('currency_id',False), abs(line.debit-line.credit), context={'date': line.date})
                        amount_currency_writeoff += (line.debit > 0) and tmp_amount or -tmp_amount

            writeoff_lines = [
                (0, 0, {
                    'name': libelle,
                    'debit': self_debit,
                    'credit': self_credit,
                    'account_id': account_id,
                    'date': date,
                    'partner_id': partner_id,
                    'currency_id': cur_id or (account.currency_id.id or False),
                    'amount_currency': amount_currency_writeoff and -1 * amount_currency_writeoff or (account.currency_id.id and -1 * currency or 0.0)
                }),
                (0, 0, {
                    'name': libelle,
                    'debit': debit,
                    'credit': credit,
                    'account_id': writeoff_acc_id,
                    'analytic_account_id': context.get('analytic_id', False),
                    'date': date,
                    'partner_id': partner_id,
                    'currency_id': cur_id or (account.currency_id.id or False),
                    'amount_currency': amount_currency_writeoff and amount_currency_writeoff or (account.currency_id.id and currency or 0.0)
                })
            ]
            # DO NOT FORWARD PORT
            # In some exceptional situations (partial payment from a bank statement in foreign
            # currency), a write-off can be introduced at the very last moment due to currency
            # conversion. We record it on the bank statement account move.
            if context.get('bs_move_id'):
                writeoff_move_id = context['bs_move_id']
                for l in writeoff_lines:
                    self.create(cr, uid, dict(l[2], move_id=writeoff_move_id), dict(context, novalidate=True))
                if not move_obj.validate(cr, uid, writeoff_move_id, context=context):
                    raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.'))
            else:
                writeoff_move_id = move_obj.create(cr, uid, {
                    'period_id': writeoff_period_id,
                    'journal_id': writeoff_journal_id,
                    'date':date,
                    'state': 'draft',
                    'line_id': writeoff_lines
                })

            writeoff_line_ids = self.search(cr, uid, [('move_id', '=', writeoff_move_id), ('account_id', '=', account_id)])
            if account_id == writeoff_acc_id:
                writeoff_line_ids = [writeoff_line_ids[1]]
            ids += writeoff_line_ids

        # marking the lines as reconciled does not change their validity, so there is no need
        # to revalidate their moves completely.
        reconcile_context = dict(context, novalidate=True)
        r_id = move_rec_obj.create(cr, uid, {'type': type}, context=reconcile_context)
        self.write(cr, uid, ids, {'reconcile_id': r_id, 'reconcile_partial_id': False}, context=reconcile_context)

        # the id of the move.reconcile is written in the move.line (self) by the create method above
        # because of the way the line_id are defined: (4, x, False)
        for id in ids:
            workflow.trg_trigger(uid, 'account.move.line', id, cr)

        if lines and lines[0]:
            partner_id = lines[0].partner_id and lines[0].partner_id.id or False
            if partner_id and not partner_obj.has_something_to_reconcile(cr, uid, partner_id, context=context):
                partner_obj.mark_as_reconciled(cr, uid, [partner_id], context=context)
        return r_id

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
                    "Chart of Taxes can not be generated!\nPlease create HMRC Posting Template record first \n" +
                    "HMRC Posting Tempale can be generated from 'Accounting/Configuration/Miscellaneous/HMRC " +
                    "Posting Template' "
                )
        period_from = self.pool.get('account.period').find(cr, uid, date_from, context=context)
        period_from = period_from and period_from[0] or False
        period_to = self.pool.get('account.period').find(cr, uid, data.date_to, context=context)
        period_to = period_to and period_to[0] or False
        period_ids = self.pool.get('account.period').build_ctx_periods(cr, uid, period_from, period_to)
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
        if 'name' in result:
            result['name'] = 'Chart of Taxes' + ':' \
                             + datetime.strptime(date_from, '%Y-%m-%d').strftime('%d-%m-%y') + ' - ' +\
                             datetime.strptime(data.date_to, '%Y-%m-%d').strftime('%d-%m-%y')
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
