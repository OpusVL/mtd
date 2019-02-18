# -*- coding: utf-8 -*-
import logging

from openerp import models, fields, api, exceptions
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class MtdVATObligationLogs(models.Model):
    _name = 'mtd_vat.vat_obligations_logs'
    _description = "Vat Obligations Logs"

    start = fields.Date()
    end = fields.Date()
    due = fields.Date()
    status = fields.Char()
    period_key = fields.Char()
    received = fields.Char()