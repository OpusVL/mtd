# -*- coding = utf-8 -*-

from odoo import fields, api, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    @api.multi
    def _compute_reconcile(self):
        for account in self:
            if self._context.get('_reconciliation_allowed_on_all_accounts', False):
                account.reconcile = True
            else:
                account.reconcile = account.not_reconcilable_by_user

    @api.multi
    def _set_reconcile(self):
        self.isnt_reconcilable_by_user = self.reconcile

    not_reconcilable_by_user = fields.Boolean('Not reconcilable by user')
    website_track = fields.Boolean('Tracks on Website', compute='_compute_website_track', inverse='_set_website_menu')
    reconcile = fields.Boolean(string='Allow Reconciliation',
                               compute='_compute_reconcile',
                               inverse='_set_reconcile',
                               help="Check this box if this account allows "
                                    "invoices & payments matching of journal items.")
