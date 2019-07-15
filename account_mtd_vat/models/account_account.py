# -*- coding = utf-8 -*-

from odoo import fields, api, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    @api.multi
    def _compute_reconcile(self):
        for account in self:
            if self._context.get('reconciliation_allowed_on_all_accounts', False):
                account.reconcile = True
            else:
                account.reconcile = account.not_reconcilable_by_user

    @api.multi
    def _set_reconcile(self):
        self.not_reconcilable_by_user = self.reconcile

    not_reconcilable_by_user = fields.Boolean('Not reconcilable by user')
    reconcile = fields.Boolean(string='Allow Reconciliation',
                               compute='_compute_reconcile',
                               inverse='_set_reconcile',
                               help="Check this box if this account allows "
                                    "invoices & payments matching of journal items.")
