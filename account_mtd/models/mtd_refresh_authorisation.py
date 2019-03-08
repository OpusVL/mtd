# -*- coding: utf-8 -*-

import requests
import json
import logging

from openerp import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class MtdRefreshAuthorisation(models.Model):
    _name = 'mtd.refresh_authorisation'
    _description = "Refreshing user authorisation  step - 4"

    @api.multi
    def refresh_user_authorisation(self, record=None, token_record=None):

        api_token = self.env['mtd.api_tokens'].search([
            ('id', '=', token_record.id),
            ('company_id', '=', record.company_id.id)
        ])
        hmrc_authorisation_url = "{}/oauth/token".format(record.hmrc_configuration.hmrc_url)
        _logger.info(
            "(Step 4) refresh_user_authorisation - hmrc authorisation url:- {}".format(hmrc_authorisation_url) +
            "token_record:- {}".format(token_record)
        )

        data_user_info = {
            'client_secret': record.hmrc_configuration.client_secret,
            'client_id': record.hmrc_configuration.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': api_token.refresh_token
        }
        headers = {
            'Content-Type': 'application/json',
        }
        _logger.info(
            "(Step 4) refresh_user_authorisation - data to send in request:- {}".format(data_user_info) +
            "headers to send in request:- {}".format(headers)
        )
        response = requests.post(hmrc_authorisation_url, data=json.dumps(data_user_info), headers=headers)
        return self.handle_refresh_response(response, record, token_record, hmrc_authorisation_url)

    def handle_refresh_response(self, response=None, record=None, api_token=None, url=None,):
        response_token = json.loads(response.text)
        _logger.info(
            "(Step 4) refresh_user_authorisation - received response of the " +
            "request:- {resp}, and its text:- {resp_token}".format(resp=response, resp_token=response_token)
        )
        resp_message = ''
        resp_error = ''
        if 'error_description' in response_token.keys():
            resp_message = response_token['error_description']
        elif 'message' in response_token.keys():
            resp_message = response_token['message']
        if 'error' in response_token.keys():
            resp_error = response_token['error']

        if response.ok:
            api_token.access_token = response_token['access_token']
            api_token.refresh_token = response_token['refresh_token']
            api_token.expires_in = json.dumps(response_token['expires_in'])
            version = self.env['{}.issue_request'.format(record._name.split('.')[0])].json_command(
                'version',
                record._name,
                record.id
            )
            return version
        elif response.status_code == 400: # and resp_message == "Bad Request":
            _logger.info(
                "(Step 4) refresh_user_authorisation - error 400, obtaining new access code and refresh token"
            )
            return self.env['mtd.user_authorisation'].get_user_authorisation(record._name, record)
        else:
            error_message = self.env['mtd.display_message'].construct_error_message_to_display(
                url=url,
                code=response.status_code,
                response_token=response_token
            )

            _logger.info(
                "(Step 4) refresh_user_authorisation - other error:- {}".format(error_message)
            )
            record.response_from_hmrc = error_message
            return True
