# -*- coding: utf-8 -*-


import logging

from openerp import models, fields, api, exceptions


class MtdVATEndpoints(models.Model):
    _name = 'mtd_vat.vat_endpoints'
    _description = "Vat endpoints"

    _logger = logging.getLogger(__name__)

    name = fields.Char('Name', required=True, readonly=True)
    # api_id = fields.Many2one(comodel_name="mtd.api", string="Api Name", required=True)
    # hmrc_configuration = fields.Many2one(comodel_name="mtd.hmrc_configuration", string='HMRC Configuration')
    # scope = fields.Char(related="api_name.scope")
    vrn = fields.Char('VRN', required=True)
    date_from = fields.Datetime()
    date_to = fields.Datetime()
    status = fields.Char()
    accept = fields.Char()
    content_type = fields.Char('Contect-Type')
    gov_test_scenario = fields.Char('Gov-Test-Scenario')
    authorisation = fields.Char('Authorization')
    x_correlationId = fields.Char('X-CorrelationId')
    response_from_hmrc = fields.Text(string="Response From HMRC", readonly=True)
    path = fields.Char(string="sandbox_url")