# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class MtdVATObligationLogs(models.Model):
    _name = 'mtd_vat.vat_obligations_logs'
    _description = "Vat Obligation Log"

    name = fields.Char(string="Period")
    start = fields.Date()
    end = fields.Date()
    due = fields.Date()
    status = fields.Char()
    period_key = fields.Char()
    received = fields.Char()
    company_id = fields.Many2one('res.company', string="Company", readonly=True)
    vrn = fields.Char(string="VAT Number")
    have_sent_submission_successfully = fields.Boolean(
        help="Whether Odoo thinks the submission has been sent"
        # In face of at least the sandbox API failing to return the right
        # status after submission
    )

    @api.multi
    def is_fulfilled(self):
        return self.status == 'F'
