# -*- coding = utf-8 -*-

from odoo import models, fields, exceptions, api, _
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vat = fields.Boolean(string="VAT Posted", default=False, readonly=True)
    vat_submission_id = fields.Many2one('mtd_vat.vat_submission_logs', string='VAT Submission Period')
    unique_number = fields.Char(
        related='vat_submission_id.unique_number',
        string="HMRC Unique Number",
        readonly=True
    )
    date_vat_period = fields.Date(string='Date Vat Period')

    # Creating a dublicate function of def reconcile function in base modules (account module),
    # removing the _check_reconcile_validity validation
    def mtd_reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        # Empty self can happen if the user tries to reconcile entries which are already reconciled.
        # The calling method might have filtered out reconciled lines.
        if not self:
            return False
        #reconcile everything that can be
        remaining_moves = self.auto_reconcile_lines()

        writeoff_to_reconcile = self.env['account.move.line']
        #if writeoff_acc_id specified, then create write-off move with value the remaining amount from move in self
        if writeoff_acc_id and writeoff_journal_id and remaining_moves:
            all_aml_share_same_currency = all([x.currency_id == self[0].currency_id for x in self])
            writeoff_vals = {
                'account_id': writeoff_acc_id.id,
                'journal_id': writeoff_journal_id.id
            }
            if not all_aml_share_same_currency:
                writeoff_vals['amount_currency'] = False
            writeoff_to_reconcile = remaining_moves._create_writeoff([writeoff_vals])
            #add writeoff line to reconcile algorithm and finish the reconciliation
            remaining_moves = (remaining_moves + writeoff_to_reconcile).auto_reconcile_lines()
        # Check if reconciliation is total or needs an exchange rate entry to be created
        (self + writeoff_to_reconcile).check_full_reconcile()
        return True

