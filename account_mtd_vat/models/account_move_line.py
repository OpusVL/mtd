# -*- coding = utf-8 -*-

from odoo import models, fields, exceptions, api, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # The below function is not being used. We may need to remove it in future
    def list_partners_to_reconcile(self, filter_domain=False):
        # Note this will ignore reconciliation_allowed_on_all_accounts in the
        # context.  If we need to not ignore it, you need to not include
        # the not_reconcilable_by_user clause from WHERE if that context is True.
        line_ids = []
        if filter_domain:
            line_ids = self.search(filter_domain)
        where_clause = filter_domain and "AND l.id = ANY(%s)" or ""
        self.env.cr.execute(
            """SELECT partner_id FROM (
               SELECT l.partner_id, p.last_reconciliation_date, SUM(l.debit) AS debit, SUM(l.credit) AS credit, MAX(l.create_date) AS max_date
               FROM account_move_line l
               RIGHT JOIN account_account a ON (a.id = l.account_id)
               RIGHT JOIN res_partner p ON (l.partner_id = p.id)
                   WHERE a.reconcile IS TRUE
                   AND l.reconcile_id IS NULL
                   AND l.state <> 'draft'
                   %s
                   GROUP BY l.partner_id, p.last_reconciliation_date
               ) AS s
               WHERE debit > 0 AND credit > 0 AND (last_reconciliation_date IS NULL OR max_date > last_reconciliation_date)
               ORDER BY last_reconciliation_date"""
            % where_clause, (line_ids,))
        ids = [x[0] for x in self.env.cr.fetchall()]
        if not ids:
            return []

        # To apply the ir_rules
        partner_obj = self.env['res.partner']
        partners = partner_obj.search([('id', 'in', ids)])
        return partners.name_get()

    vat = fields.Boolean(string="VAT Posted", default=False, readonly=True)
    vat_submission_id = fields.Many2one('mtd_vat.vat_submission_logs', string='VAT Submission Period')
    unique_number = fields.Char(
        related='vat_submission_id.unique_number',
        string="HMRC Unique Number",
        readonly=True
    )

    # Creating a copy of base reconcile function renamed mtd_reconcile ,
    # removing the reconcile flag control for tax reconcile
    @api.multi
    def mtd_reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        # Empty self can happen if the user tries to reconcile entries which are already reconciled.
        # The calling method might have filtered out reconciled lines.
        if not self:
            return True

        # Perform all checks on lines
        company_ids = set()
        all_accounts = []
        partners = set()
        for line in self:
            company_ids.add(line.company_id.id)
            all_accounts.append(line.account_id)
            if (line.account_id.internal_type in ('receivable', 'payable')):
                partners.add(line.partner_id.id)
            if line.reconciled:
                raise UserError(_('You are trying to reconcile some entries that are already reconciled!'))
        if len(company_ids) > 1:
            raise UserError(_('To reconcile the entries company should be the same for all entries!'))
        if len(set(all_accounts)) > 1:
            raise UserError(_('Entries are not of the same account!'))
        if all_accounts[0].internal_type == 'liquidity':
            raise UserError(_('The account %s (%s) is a liquidity account !') % (
                all_accounts[0].name, all_accounts[0].code))

        # reconcile everything that can be
        remaining_moves = self.auto_reconcile_lines()

        # if writeoff_acc_id specified, then create write-off move with value the remaining amount from move in self
        if writeoff_acc_id and writeoff_journal_id and remaining_moves:
            all_aml_share_same_currency = all([x.currency_id == self[0].currency_id for x in self])
            writeoff_vals = {
                'account_id': writeoff_acc_id.id,
                'journal_id': writeoff_journal_id.id
            }
            if not all_aml_share_same_currency:
                writeoff_vals['amount_currency'] = False
            writeoff_to_reconcile = remaining_moves._create_writeoff(writeoff_vals)
            # add writeoff line to reconcile algo and finish the reconciliation
            remaining_moves = (remaining_moves + writeoff_to_reconcile).auto_reconcile_lines()
            return writeoff_to_reconcile
        return True
