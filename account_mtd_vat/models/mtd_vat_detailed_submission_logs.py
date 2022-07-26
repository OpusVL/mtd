# -*- coding = utf-8 -*-

import logging

from odoo import models, fields, api, exceptions
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class MtdVATDetailedSubmissionLogs(models.Model):

    _name = 'mtd_vat.vat_detailed_submission_logs'
    _description = "Vat Detailed Submission Log"

    account_move_line_id = fields.Many2one('account.move.line', readonly=True)
    account_id = fields.Many2one('account.account', string='Account', readonly=True)
    account_internal_type = fields.Selection(related='account_move_line_id.account_internal_type',
                                             string="Internal Type", store=True, readonly=True)
    account_root_id = fields.Many2one(related='account_move_line_id.account_root_id',
                                      string="Account Root", store=True, readonly=True)
    amount_currency = fields.Float(readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', readonly=True)
    blocked = fields.Boolean(string='No Follow-up', readonly=True)
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True,
                                          related='account_move_line_id.company_currency_id')
    company_id = fields.Many2one('res.company', string="Company", readonly=True)
    country_id = fields.Many2one(comodel_name='res.country', related="move_id.partner_id.country_id")
    create_date = fields.Date(string='Creation date', readonly=True)
    create_uid = fields.Char(readonly=True)
    credit = fields.Float(readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    date = fields.Date(string='Effective date', readonly=True)
    date_maturity = fields.Date('Due date', readonly=True)
    date_vat_period = fields.Date(string='Date Vat Period')
    debit = fields.Float(readonly=True)
    discount = fields.Float(string='Discount (%)', digits='Discount', readonly=True)
    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note'),
    ], related='account_move_line_id.display_type', readonly=True)
    full_reconcile_id = fields.Many2one('account.full.reconcile', string="Matching #", readonly=True,
                                        related='account_move_line_id.full_reconcile_id')
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    move_name = fields.Char(string='Number', related='account_move_line_id.move_name', store=True, readonly=True)
    name = fields.Char('Name', readonly=True)
    parent_state = fields.Selection(related='account_move_line_id.parent_state', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)
    quantity = fields.Float(digits=(16, 2), readonly=True)
    ref = fields.Char(readonly=True)
    sequence = fields.Integer(readonly=True)
    tax_audit = fields.Char(string="Tax Audit String", readonly=True)
    tax_base_amount = fields.Monetary(string="Base Amount", store=True, readonly=True,
                                      currency_field='company_currency_id')
    tax_exigible = fields.Boolean(string='Appears in VAT report', default=True, readonly=True,)
    tax_line_id = fields.Many2one('account.tax', string='Originator Tax', store=True, readonly=True)
    tax_group_id = fields.Many2one(related='tax_line_id.tax_group_id', string='Originator tax group',
                                   readonly=True, store=True)
    tax_repartition_line_id = fields.Many2one(comodel_name='account.tax.repartition.line',
                                              string="Originator Tax Repartition Line", readonly=True)
    unique_number = fields.Char(string='HMRC Unique No', readonly=True)
    md5_integrity_value = fields.Char(string="Checksum", readonly=True)

