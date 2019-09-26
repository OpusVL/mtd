# -*- coding = utf-8 -*-

from odoo import models, fields, exceptions, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vat = fields.Boolean(string="VAT Posted", default=False, readonly=True)
    vat_submission_id = fields.Many2one('mtd_vat.vat_submission_logs', string='VAT Submission Period')
    unique_number = fields.Char(
        related='vat_submission_id.unique_number',
        string="HMRC Unique Number",
        store=True,
        readonly=True
    )
    date_vat_period = fields.Date(string='Date Vat Period')
