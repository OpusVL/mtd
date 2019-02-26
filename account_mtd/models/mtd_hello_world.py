# -*- coding: utf-8 -*-

import logging

from openerp import models, fields, api, exceptions
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class MtdHelloWorld(models.Model):
    _name = 'mtd.hello_world'
    _description = "Hello world to test connection between Odoo and HMRC"
    
    name = fields.Char(required=True, readonly=True)
    api_id = fields.Many2one(comodel_name="mtd.api", string="Api Name", required=True)
    hmrc_configuration = fields.Many2one(comodel_name="mtd.hmrc_configuration", string="HMRC Configuration")
    scope = fields.Char(related="api_id.scope")
    response_from_hmrc = fields.Text(string="Response From HMRC", readonly=True)
    endpoint_name = fields.Char(string="which_button")
    path = fields.Char(string="sandbox_url")

    @api.multi
    def action_hello_world_connection(self):
        if not self.hmrc_configuration:
            raise exceptions.Warning("Please select HMRC configuration before continuing!")
        # making sure that the endpoint is what we have used in the data file as the name can be changed anytime.
        endpoint_record = self.env['ir.model.data'].search([
            ('res_id', '=', self.id), ('model', '=', 'mtd.hello_world')
        ])

        request_handler = {
            "mtd_hello_world_endpoint": "_handle_mtd_hello_world_endpoint",
            "mtd_hello_application_endpoint": "_handle_mtd_hello_application_endpoint",
            "mtd_hello_user_endpoint": "_handle_mtd_hello_user_endpoint",
        }
        handler_name = request_handler.get(endpoint_record.name)
        if handler_name:
            handle_request = getattr(self, handler_name)()
            return handle_request
        else:
            raise exceptions.Warning("Could not connect to HMRC! \nThis is not a valid HMRC service connection")

    def _handle_mtd_hello_world_endpoint(self):
        self.endpoint_name = "helloworld"
        self.path = "/hello/world"
        version = self.env['mtd.issue_request'].json_command('version', self._name, self.id)
        _logger.info(self.connection_button_clicked_log_message())
        return version

    def _handle_mtd_hello_application_endpoint(self):
        self.endpoint_name = "application"
        self.path = "/hello/application"
        version = self.env['mtd.issue_request'].json_command('version', self._name, self.id)
        _logger.info(self.connection_button_clicked_log_message())
        return version

    def _handle_mtd_hello_user_endpoint(self):
        self.endpoint_name = "user"
        self.path = "/hello/user"
        _logger.info(self.connection_button_clicked_log_message())
        # search for token record for the API
        token_record = self.env['mtd.api_tokens'].search([('api_id', '=', self.api_id.id)])
        _logger.info(
            "Connection button Clicked - endpoint name {name}, and the api is :- {api_id} ".format(
                name=self.name,
                api_id=self.api_id
            )
        )
        if token_record.access_token and token_record.refresh_token:
            _logger.info(
                "Connection button Clicked - endpoint name {name}, ".format(name=self.name) +
                "We have access token and refresh token"
            )
            version = self.env['mtd.issue_request'].json_command('version', self._name, self.id)
            return version
        else:
            _logger.info(
                "Connection button Clicked - endpoint name {name}, No access token ".format(name=self.name) +
                "found and no refresh_token found from the token record table."
            )
            authorisation_tracker = self.env['mtd.api_request_tracker'].search([('closed', '=', False)])
            _logger.info(
                "Connection button Clicked - endpoint name {name}, ".format(name=self.name) +
                "Checking to see if a request is in process"
            )
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
