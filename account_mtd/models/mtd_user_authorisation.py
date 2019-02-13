# -*- coding: utf-8 -*-

import requests
import json
import logging
import werkzeug
import urllib

from odoo import models, fields, api, exceptions
from urllib.parse import urlparse

_logger = logging.getLogger(__name__)


class MtdUserAuthorisation(models.Model):
    _name = 'mtd.user_authorisation'
    _description = "Get user authorisation setp one of user authentication"

    @api.multi
    def get_user_authorisation(self, module_name=None, record=None):

        tracker_api = self.create_tracker_record(module_name, record)
        redirect_uri = "{}/auth-redirect".format(record.hmrc_configuration.redirect_url)
        state = ""
        # State is optional
        if record.hmrc_configuration.state:
            state = "&state={}".format(record.hmrc_configuration.state)
        # scope needs to be percent encoded
        scope = urllib.parse.quote_plus(record.scope)
        authorisation_url_prefix = "https://test-api.service.hmrc.gov.uk/oauth/authorize?"
        _logger.info("(Step 1) Get authorisation - authorisation URI used:- {}".format(authorisation_url_prefix))
        authorisation_url = (
            "{url}response_type=code&client_id={client_id}&scope={scope}{state}&redirect_uri={redirect}".format(
                url=authorisation_url_prefix,
                client_id=record.hmrc_configuration.client_id,
                scope=scope,
                state=state,
                redirect=redirect_uri
            )
        )
        _logger.info(
            "(Step 1) Get authorisation - authorisation URI " +
            "used to send request:- {url}".format(url=authorisation_url)
        )
        response = requests.get(authorisation_url, timeout=3)
        # response_token = json.loads(req.text)
        _logger.info(
            "(Step 1) Get authorisation - received response of the request:- {response}".format(response=response)
        )
        return self.handle_user_authorisation_response(response, authorisation_url, tracker_api, record)

    def handle_user_authorisation_response(self, response=None, url=None, tracker=None, record=None):
        if response.ok:
            return {'url': url, 'type': 'ir.actions.act_url', 'target': 'self', 'res_id': record.id}
        else:
            response_token = json.loads(response.text)
            error_message = self.env['mtd.display_message'].consturct_error_message_to_display(
                url=url,
                code=response.status_code,
                message=response_token['error_description'],
                error=response_token['error']
            )
            record.response_from_hmrc = error_message
            # close the request so a new request can be made.
            tracker.closed = 'response'

            return werkzeug.utils.redirect(
                '/web#id={id}&view_type=form&model=mtd.hello_world&menu_id={menu}&action={action}'.format(
                    id=record.id,
                    menu=tracker.menu_id,
                    action=tracker.action
                )
            )

    def create_tracker_record(self, module_name=None, record=None):
        # get the action id and menu id and store it in the tracker table
        # if we get an error on authorisation or while exchanging tokens we need to use these to redirect.
        action = self.env.ref('account_mtd.action_mtd_{}'.format(module_name.split('.')[1]))
        menu_id = self.env.ref('account_mtd.submenu_mtd_{}'.format(module_name.split('.')[1]))

        # Update the information in the api tracker table
        _logger.info("(Step 1) Get authorisation")
        tracker_api = self.env['mtd.api_request_tracker']
        tracker_api = tracker_api.create({
            'user_id': record._uid,
            'api_id': record.api_id.id,
            'api_name': record.api_id.name,
            'endpoint_id': record.id,
            'request_sent': True,
            'action': action.id,
            'menu_id': menu_id.id,
            'module_name': module_name,
        })
        return tracker_api