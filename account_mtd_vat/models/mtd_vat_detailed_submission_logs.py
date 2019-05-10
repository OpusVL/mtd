# -*- coding = utf-8 -*-

import logging

from odoo import models, fields, api, exceptions
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class MtdVATDetailedSubmissionLogs(models.Model):

    _name = 'mtd_vat.vat_detailed_submission_logs'
    _description = "Vat Detailed Submission Log"

    statement_id = fields.Many2one('account.bank.statement', string='Statement', readonly=True)
    create_date = fields.Date(string='Creation date', readonly=True)
    company_id = fields.Many2one('res.company', string="Company", readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    date_maturity = fields.Date('Due date', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    reconcile_partial_id = fields.Many2one('account.move.reconcile', string='Partial Reconcile', readonly=True)
    blocked = fields.Boolean(string='No Follow-up', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', readonly=True)
    create_uid = fields.Char(readonly=True)
    credit = fields.Float(readonly=True)
    centralisation = fields.Char(readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)
    reconcile_id = fields.Many2one('account.move.reconcile', string='Reconcile', readonly=True)
    tax_code_id = fields.Many2one('account.tax.code', string='Tax Account', readonly=True)
    state = fields.Char(readonly=True)
    debit = fields.Float(readonly=True)
    ref = fields.Char(string='Reference', readonly=True)
    account_id = fields.Many2one('account.account', string='Account', readonly=True)
    period_id = fields.Many2one('account.period', string='Period', readonly=True)
    write_date = fields.Datetime(readonly=True)
    date_created = fields.Datetime(readonly=True)
    date = fields.Date(string='Effective date', readonly=True)
    write_uid = fields.Char(readonly=True)
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    reconcile_ref = fields.Char(readonly=True)
    name = fields.Char('Name', readonly=True)
    tax_amount = fields.Float(string='Tax/Base Amount', readonly=True)
    account_tax_id = fields.Many2one('account.tax', string='Tax', readonly=True)
    product_uom_id = fields.Many2one('product.uom', string='Unit of Measure', readonly=True)
    amount_currency = fields.Float(readonly=True)
    quantity = fields.Float(digits=(16, 2), readonly=True)

    unique_number = fields.Char(string='HMRC Unique No', readonly=True)
    account_move_line_id = fields.Many2one('account.move.line', readonly=True)
    md5_integrity_value = fields.Char(string="Checksum", readonly=True)
