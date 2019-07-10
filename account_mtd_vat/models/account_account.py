# -*- coding = utf-8 -*-

from odoo import fields, api, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    @api.multi
    def _compute_reconcile(self):
        for account in self:
            if self._context.get('ignore_allow_reconciliation_flag_for_mtd', False):
                account.reconcile = True
            else:
                account.reconcile = account.non_mtd_reconcilable

    @api.multi
    def _set_reconcile(self):
        self.non_mtd_reconcilable = self.reconcile

    non_mtd_reconcilable = fields.Boolean('Non MTD Reconcilable')
    website_track = fields.Boolean('Tracks on Website', compute='_compute_website_track', inverse='_set_website_menu')
    reconcile = fields.Boolean(string='Allow Reconciliation',
                               compute='_compute_reconcile',
                               inverse='_set_reconcile',
                               help="Check this box if this account allows "
                                    "invoices & payments matching of journal items.")
