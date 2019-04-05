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
