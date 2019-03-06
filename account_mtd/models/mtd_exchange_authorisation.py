# -*- coding: utf-8 -*-

import requests
import json
import logging
import werkzeug

from openerp import models, fields, api, exceptions
from datetime import datetime

_logger = logging.getLogger(__name__)


class MtdExchangeAuthorisation(models.Model):
    _name = 'mtd.exchange_authorisation'
    _description = "Exchange user authorisation step - 2 "

    @api.multi
    def exchange_user_authorisation(self, auth_code, record_id, tracker_id, company_id):

        _logger.info("(Step 2) exchange authorisation code")
        api_tracker = self.env['mtd.api_request_tracker'].search([('id', '=', tracker_id)])
        api_token = self.env['mtd.api_tokens'].search([
            ('api_id', '=', api_tracker.api_id.id),
            ('company_id', '=', company_id)
        ])

        if api_token:
            api_token.authorisation_code = auth_code
        else:
            api_token.create({
                'api_id': api_tracker.api_id.id,
                'api_name': api_tracker.api_name,
                'authorisation_code': auth_code,
                'company_id': company_id,
            })
        record = self.env[api_tracker.module_name].search([('id', '=', record_id)])
        token_location_uri = "https://test-api.service.hmrc.gov.uk/oauth/token"
        client_id = record.hmrc_configuration.client_id
        client_secret = record.hmrc_configuration.client_secret
        redirect_uri = "{}/auth-redirect".format(record.hmrc_configuration.redirect_url)

        # When exchanging the authorisation code for access token we need to sent a post request
        # passing in following parameters.
        data_user_info = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'code': auth_code
        }
        headers = {'Content-Type': 'application/json'}
        _logger.info(
            "(Step 2) exchange authorisation code - Data which will be " +
            "sent in the request:- {} \n".format(json.dumps(data_user_info)) +
            "headers which will be:- {}".format(headers)
        )
        response = requests.post(token_location_uri, data=json.dumps(data_user_info), headers=headers)
        response_token = json.loads(response.text)
        _logger.info(
            "(Step 2) exchange authorisation code - " +
            "received response of the request:- {response}, ".format(response=response) +
            "and its text:- {res_token}".format(res_token=response_token)
        )
        return self.handle_exchange_user_authorisation_response(
            response,
            token_location_uri,
            record,
            api_token,
            auth_code,
            api_tracker)

    def handle_exchange_user_authorisation_response(
            self, response=None, url=None, record=None, api_token=None, auth_code=None, api_tracker=None):
        response_token = json.loads(response.text)
        # get the record which we created when sending the request and update the closed column
        # As this determines whether we can place another request or not
        record_tracker = self.env['mtd.api_request_tracker'].search([('closed', '=', False)])
        record_tracker.closed = 'response'
        module_name = record_tracker.module_name
        record_id = record_tracker.endpoint_id
        if response.ok:
            if not api_token:
                api_token = self.env['mtd.api_tokens'].search([
                    ('authorisation_code', '=', auth_code),
                    ('company_id', '=', api_tracker.company_id)
                ])
            _logger.info(
                "(Step 2) exchange authorisation code " +
                "- api_token table id where info is stored:- {}".format(api_token)
            )
            api_token.access_token = response_token['access_token']
            api_token.refresh_token = response_token['refresh_token']
            api_token.expires_in = json.dumps(response_token['expires_in'])
            api_token.access_token_recieved_date = datetime.utcnow()
            version = self.env['{}.issue_request'.format(record._name.split('.')[0])].json_command(
                'version',
                module_name,
                record_id,
                record_tracker
            )
            return version
        else:
            error_message = self.env['mtd.display_message'].construct_error_message_to_display(
                url=url,
                code=response.status_code,
                response_token=response_token
            )
            record.response_from_hmrc = error_message
            _logger.info(
                "(Step 2) exchange authorisation code - log:- {}".format(error_message)
            )
            _logger.info(
                "(Step 2) exchange authorisation code - redirect URI :- " +
                "/web#id={id}&view_type=form&model={model}&menu_id={menu}&action={action}".format(
                    id=record.id,
                    model=module_name,
                    menu=api_tracker.menu_id,
                    action=api_tracker.action
                )
            )
            return werkzeug.utils.redirect(
                "/web#id={id}&view_type=form&model={model}&menu_id={menu}&action={action}".format(
                    id=record.id,
                    model=module_name,
                    menu=api_tracker.menu_id,
                    action=api_tracker.action
                )
            )
