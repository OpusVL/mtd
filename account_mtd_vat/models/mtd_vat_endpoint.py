# -*- coding: utf-8 -*-
import logging

from openerp import models, fields, api, exceptions
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class MtdVATEndpoints(models.Model):
    _name = 'mtd_vat.vat_endpoints'
    _description = "Vat endpoints"

    name = fields.Char('Name', required=True) # , readonly=True)
    api_id = fields.Many2one(comodel_name="mtd.api", string="Api Name", required=True)
    hmrc_configuration = fields.Many2one(comodel_name="mtd.hmrc_configuration", string='HMRC Configuration')
    scope = fields.Char(related="api_id.scope")
    vrn = fields.Char('VRN')
    date_from = fields.Date()
    date_to = fields.Date()
    status = fields.Char()
    gov_test_scenario = fields.Char('Gov-Test-Scenario')
    x_correlationId = fields.Char('X-CorrelationId')
    response_from_hmrc = fields.Text(string="Response From HMRC", readonly=True)
    path = fields.Char(string="sandbox_url")
    endpoint_name = fields.Char(string="which_button")

    @api.multi
    def action_vat_connection(self):
        if not self.hmrc_configuration:
            raise exceptions.Warning("Please select HMRC configuration before continuing!")
        elif not self.vrn:
            raise exceptions.Warning("Please enter the VRN")

        #return self._handle_vat_obligations_endpoint()
        import pdb; pdb.set_trace()
        if self.name == "VAT Liabilitites":
            return self._handle_vat_liabilities_endpoint()
        elif self.name == "VAT Obligations":
            return self._handle_vat_obligations_endpoint()
        elif self.name == "VAT Payments":
            return self._handle_vat_payments_endpoint()
        ##################################################################################
        # NEED TO WORK ON THIS AS CURRENTLY THERE ARE NO DATA RECORDS CREATED AUTOMATICALLY
        ##################################################################################

        # endpoint_record = self.env['ir.model.data'].search([
        #     ('res_id', '=', self.id), ('model', '=', 'mtd_vat.vat_endpoints')
        # ])

        # request_handler = {
        #     "mtd_vat_obligations_endpoint": "_handle_vat_obligations_endpoint",
        #     "mtd_vat_returns_endpoint": "_handle_vat_returns_endpoint",
        #     "mtd_vat_returns_periodkey_endpoint": "_handle_vat_returns_periodkey_endpoint",
        #     "mtd_vat_liabilities_endpoint": "_handle_vat_liabilities_endpoint",
        #     "mtd_vat_payments_endpoint": "_handle_vat_payments_endpoint",
        # }
        #
        # handler_name = request_handler.get(endpoint_record.name)
        # if handler_name:
        #     handle_request = getattr(self, handler_name)()
        #     return handle_request
        # else:
        #     raise exceptions.Warning("Could not connect to HMRC! \nThis is not a valid HMRC service connection")

    def _handle_vat_obligations_endpoint(self):
        self.path = "/organisations/vat/{vrn}/obligations".format(vrn=self.vrn)
        self.endpoint_name = "vat-obligation"
        _logger.info(self.connection_button_clicked_log_message())

        return self.process_connection()

    def _handle_vat_liabilities_endpoint(self):
        self.path = "/organisations/vat/{vrn}/liabilities".format(vrn=self.vrn)
        self.endpoint_name = "vat-liabilities"

        return self.process_connection()

    def _handle_vat_payments_endpoint(self):
        self.path = "/organisations/vat/{vrn}/payments".format(vrn=self.vrn)
        self.endpoint_name = "vat-payments"

        return self.process_connection()

    def process_connection(self):
        # search for token
        token_record = self.env['mtd.api_tokens'].search([('api_id', '=', self.api_id.id)])
        _logger.info(
            "Vat Obligation - endpoint name {name}, and the api is :- {api_id} ".format(
                name=self.name,
                api_id=self.api_id
            )
        )
        if token_record.access_token and token_record.refresh_token:
            _logger.info(
                "Connection button Clicked - endpoint name {name}, ".format(name=self.name) +
                "We have access token and refresh token"
            )
            version = self.env['mtd_vat.issue_request'].json_command('version', self._name, self.id)
            return version
        else:
            _logger.info(
                "Vat Obligation - endpoint name {name}, ".format(name=self.name) +
                "We have no access token and refresh token found"
            )
            authorisation_tracker = self.env['mtd.api_request_tracker'].search([
                ('api_id', '=', self.api_id.id),
                ('closed', '=', False)
            ])
        create_date = fields.Datetime.from_string(authorisation_tracker.create_date)
        time_10_mins_ago = (datetime.utcnow() - timedelta(minutes=10))
        if authorisation_tracker:
            authorised_code_expired = create_date <= time_10_mins_ago
            if authorised_code_expired:
                # we can place a new request and close this request.
                authorisation_tracker.closed = 'timed_out'
                _logger.info(
                    "Connection button Clicked - endpoint name {name}, no Pending requests".format(name=self.name)
                )
                return self.env['mtd.user_authorisation'].get_user_authorisation(self._name, self)
            else:
                # The request made was within 10 mins so the user has to wait.
                raise exceptions.Warning(
                    "An authorisation request is already in process!!!\n " +
                    "Please try again later"
                )
        else:
            return self.env['mtd.user_authorisation'].get_user_authorisation(self._name, self)

    def connection_button_clicked_log_message(self):
        return "Connection button Clicked - endpoint name {name}, redirect URL:- {redirect}, Path url:- {path}".format(
                name=self.name,
                redirect=self.hmrc_configuration.redirect_url,
                path=self.path
            )
