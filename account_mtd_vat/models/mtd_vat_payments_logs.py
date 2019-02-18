# -*- coding: utf-8 -*-
import logging

from openerp import models, fields

_logger = logging.getLogger(__name__)


class MtdVATPaymentsLogs(models.Model):
    _name = 'mtd_vat.vat_payments_logs'
    _description = "Vat Payments Logs"

    start = fields.Date()
    end = fields.Date()
    amount = fields.Date()
    received = fields.Char()