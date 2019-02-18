# -*- coding: utf-8 -*-
import logging

from openerp import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class MtdVATLiabilitiesLogs(models.Model):
    _name = 'mtd_vat.vat_liabilities_logs'
    _description = "Vat liabilities Logs"

    from_date = fields.Date()
    to_date = fields.Date()
    type =fields.Char()
    due = fields.Date()
    outstanding_amount = fields.Char()
    original_amount = fields.Char()