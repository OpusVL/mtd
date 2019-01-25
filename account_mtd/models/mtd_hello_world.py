# -*- coding: utf-8 -*-

import requests
import json
import logging
import werkzeug
import urllib

from odoo import models, fields, api, exceptions
from datetime import datetime, timedelta


class MtdHelloWorld(models.Model):
    _name = 'mtd.hello_world'
    _description = "Hello world to test connection between Odoo and HMRC"
    
    _logger = logging.getLogger(__name__)
    
    name = fields.Char('Name', required=True, readonly=True)
    api_name = fields.Many2one(comodel_name="mtd.api", required=True)
    hmrc_configuration = fields.Many2one(comodel_name="mtd.hmrc_configuration", string='HMRC Configuration')
    scope = fields.Char(related="api_name.scope")
    response_from_hmrc = fields.Text(string="Response From HMRC", readonly=True)
    which_button_type_clicked = fields.Char(string="which_button")
    path = fields.Char(string="sandbox_url")
    current_record = fields.Char()
    # need a variable which will keep the record id so that when we
    
    @api.multi
    def action_hello_world_connection(self):
        if not self.hmrc_configuration:
            raise exceptions.Warning("Please select hmrc configuration before continuing!")
        # making sure that the endpoint is what we have used in the data file as the name can be changed anytime.
        endpoint_record = self.env['ir.model.data'].search([('res_id','=',self.id), ('model', '=', 'mtd.hello_world')])

        if endpoint_record.name == "mtd_hello_world_endpoint":
            self.which_button_type_clicked = "helloworld"
            self.path = "/hello/world"
            version = self._json_command('version')
            self._logger.info(
                "Connection button Clicked - endpoint name {}, ".format(self.name) +
                "redirect URL:- {}, Path url:- {}".format(self.hmrc_configuration.redirect_url, self.path)
            )
        elif endpoint_record.name == "mtd_hello_application_endpoint":
            self.which_button_type_clicked = "application"
            self.path = "/hello/application"
            version = self._json_command('version')
            self._logger.info(
                "Connection button Clicked - endpoint name {},".format(self.name) +
                "redirect URL:- {}, Path url:- {}".format(self.hmrc_configuration.redirect_url, self.path)
            )
        elif endpoint_record.name == "mtd_hello_user_endpoint":
            self.which_button_type_clicked = "user"
            self.path = "/hello/user"
            self._logger.info(
                "Connection button Clicked - endpoint name {}, ".format(self.name) +
                "redirect URL:- {}, Path url:- {}".format(self.hmrc_configuration.redirect_url, self.path)
            )
            # search for token record for the API
            token_record = self.env['mtd.api_tokens'].search([('api_id', '=', self.api_name.id)])
            self._logger.info(
                "Connection button Clicked - endpoint name {} , ".format(self.name) +
                "and the api is :- {} ".format(self.api_name)
            )
            if not token_record.access_token and not token_record.refresh_token:
                self._logger.info(
                    "Connection button Clicked - endpoint name {0}, No access token ".format(self.name) +
                    "found and no refresh_token found from the token record table."
                )
                api_tracker = self.env['mtd.api_request_tracker'].search([
                    ('request_sent', '=', True),
                    ('response_received', '=', False)
                ])
                self._logger.info(
                    "Connection button Clicked - endpoint name {}, ".format(self.name) +
                    "Checking to see if a request is in process"
                )
                time_10_mins_ago = (datetime.now() - timedelta(minutes=10))
                format_time_10_mins_ago = time_10_mins_ago.strftime('%Y-%m-%d- %H:%M:%S')
                if api_tracker:
                    if format_time_10_mins_ago >= api_tracker.create_date:
                        # this means that time is more than 10 minutes a go so we can place a new request
                        # and close this request.
                        api_tracker.response_received = True
                        self._logger.info(
                            "Connection button Clicked - endpoint name {}, ".format(self.name) +
                            "no Pending requests"
                        )
                        return self.get_user_authorisation()
                    else:
                        # The request made was within 10 mins so the user has to wait.
                        raise exceptions.Warning(
                            "An authorisation request is already in process!!!\n " +
                            "Please try again later"
                        )
                else:
                    return self.get_user_authorisation()
            else:
                self._logger.info(
                    "Connection button Clicked - endpoint name {}, ".format(self.name) +
                    "We have access token and refresh token"
                )
                version = self._json_command('version')
                return version
        else:
            raise exceptions.Warning("Could not connect to HMRC! \nThis is not a valid end point")
    
    def _json_command(self, command, timeout=3, record_id=None):
        # this will determine where we have come from
        # if there is no record_id then we know we already had valid record to gain all the information for hello user
        self._logger.info(
            "_json_command - has record_id been provided?:- {}".format(record_id)
        )
        if record_id:
            self = self.env['mtd.hello_world'].search([('id', '=', record_id)])
            self._logger.info(
                "_json_command - we need to find the record and assign it to self"
            )
        # search the token table to see if we have access token
        token_record = self.env['mtd.api_tokens'].search([('api_id', '=', self.api_name.id)])
        access_token = token_record.access_token if token_record else ""
        # may not newed next line of code will need to look into this further while testing.
        # refresh_token = token_record.refresh_token if token_record else ""
        
        header_items = {"Accept": "application/vnd.hmrc.1.0+json"}
        if self.which_button_type_clicked == "application":
            header_items["authorization"] = ("Bearer "+self.hmrc_configuration.server_token)
        elif self.which_button_type_clicked == "user":
            # need to first check if the user has any accessToken and refreshtoken
            # If not we need to proceed to the first and second step and then come to this step.
            header_items["authorization"] = ("Bearer "+str(access_token))

        hmrc_connection_url = "{}{}".format(self.hmrc_configuration.hmrc_url, self.path)
        self._logger.info(
            "_json_command - hmrc connection url:- {}, ".format(hmrc_connection_url) +
            "headers:- {}".format(header_items)
        )
        req = requests.get(hmrc_connection_url, timeout=3, headers=header_items)
        response_token = json.loads(req.text)
        self._logger.info(
            "_json_command - received respponse of the request:- {}, ".format(req) +
            "and its text:- {}".format(response_token)
        )
        if req.ok:
            construct_text = (
                    "Date {}     Time {} \n".format(datetime.now().date(), datetime.now().time()) +
                    "Congratulations ! The connection succeeded. \n" +
                    "Please check the log below for details. \n\n" +
                    "Connection Status Details: \n" +
                    "Request Sent: \n{} \n\n".format(hmrc_connection_url) +
                    "Response Received: \n{}".format(response_token['message'])
            )
            self.response_from_hmrc = construct_text
            if record_id:
                self._logger.info(
                    "_json_command - response received ok we have record id so we " +
                    "return werkzeug.utils.redirect "
                )
                # action_id
                action = self.env.ref('account_mtd.action_mtd_hello_world')
                # menu_id
                menu_id = self.env.ref('account_mtd.submenu_mtd_hello_world')
                self._logger.info(
                    "-------Redirect is:- " +
                    "/web#id={}&view_type=form&model=mtd.hello_world&".format(record_id) +
                    "menu_id={}&action={}".format(menu_id.id, action.id)
                )
                return werkzeug.utils.redirect(
                    '/web#id={}&view_type=form&model=mtd.hello_world&'.format(record_id) +
                    'menu_id={}&action={}'.format(menu_id.id, action.id)
                )
            return True
            
        elif (req.status_code == 401 and
              self.which_button_type_clicked == "user" and
              response_token['message'] == "Invalid Authentication information provided"):
            self._logger.info(
                "_json_command - code 401 found, user button clicked,  " +
                "and message was:- {} ".format(response_token['message'])
            )
            return self.refresh_user_authorisation(token_record)
            
        else:
            construct_text = (
                "Date {}     Time {} \n".format(datetime.now().date(), datetime.now().time()) +
                "Sorry. The connection failed ! \n" +
                "Please check the log below for details. \n\n" +
                "Connection Status Details: \n" +
                "Request Sent: \n{} \n\n".format(hmrc_connection_url) +
                "Error Code:\n{} \n\n".format(req.status_code) +
                "Response Received: \n{}\n{}".format(response_token['error'], response_token['error_description'])
            )
            self._logger.info("_json_command - other error found:- {} ".format(construct_text))
            self.response_from_hmrc = construct_text
            if record_id:
                action = self.env.ref('account_mtd.action_mtd_hello_world')
                menu_id = self.env.ref('account_mtd.submenu_mtd_hello_world')
                return werkzeug.utils.redirect(
                    '/web#id={}&view_type=form&model=mtd.hello_world'.format(record_id) +
                    '&menu_id={}&action={}'.format(menu_id.id, action.id)
                )
            return True
    
    @api.multi
    def get_user_authorisation(self):
        # get the action id and menu id and store it in the tracker table
        # if we get an error on authorisation or while exchanging tokens we need to use these to redirect.
        action = self.env.ref('account_mtd.action_mtd_hello_world')
        menu_id = self.env.ref('account_mtd.submenu_mtd_hello_world')

        # Update the information in the api tracker table
        self._logger.info("(Step 1) Get authorisation")
        tracker_api = self.env['mtd.api_request_tracker']
        tracker_api = tracker_api.create({
            'user_id': self._uid,
            'api_id': self.api_name.id,
            'api_name': self.api_name.name,
            'endpoint_id': self.id,
            'request_sent': True,
            'action': action.id,
            'menu_id': menu_id.id,
            })

        redirect_uri = "{}/auth-redirect".format(self.hmrc_configuration.redirect_url)
        authorisation_url = "https://test-api.service.hmrc.gov.uk/oauth/authorize?"
        self._logger.info("(Step 1) Get authorisation - authorisation URI used:- {}".format(authorisation_url))
        state = ""
        # State is optional
        if self.hmrc_configuration.state:
            state = "&state={}".format(self.hmrc_configuration.state)
        # scope needs to be percent encoded
        scope = urllib.parse.quote_plus(self.scope)

        authorisation_url += (
            "response_type=code&client_id={}&scope={}".format(self.hmrc_configuration.client_id, scope) +
            "{}&redirect_uri={}".format(state, redirect_uri)
        )
        self._logger.info(
            "(Step 1) Get authorisation - authorisation URI " +
            "used to send request:- {}".format(authorisation_url)
        )
        req = requests.get(authorisation_url, timeout=3)
        # response_token = json.loads(req.text)
        self._logger.info(
            "(Step 1) Get authorisation - received response of the request:- {}".format(req)
        )
        if req.ok:
            return {'url': authorisation_url, 'type': 'ir.actions.act_url', 'target': 'self', 'res_id': self.id}
        else:
            response_token = json.loads(req.text)
            construct_text = (
                    "Date {}     Time {} \n".format(datetime.now().date(), datetime.now().time()) +
                    "Sorry. The connection failed ! \n" +
                    "Please check the log below for details. \n\n" +
                    "Connection Status Details: \n" +
                    "Request Sent: \n{} \n\n".format(authorisation_url) +
                    "Error Code:\n{} \n\n".format(req.status_code) +
                    "Response Received: \n{}\n{}".format(response_token['error'], response_token['error_description'])
            )
            self.response_from_hmrc = construct_text
            # We need to set the response received in tracker to be True 
            # even if we receive negetive response.
            tracker_api.response_received = True

            return werkzeug.utils.redirect(
                '/web#id={}&view_type=form&model=mtd.hello_world'.format(self.id) +
                '&menu_id={}&action={}'.format(tracker_api.menu_id, tracker_api.action))
            
    @api.multi        
    def exchange_user_authorisation(self, auth_code, record_id, tracker_id):
        self._logger.info("(Step 2) exchange authorisation code")
        api_tracker = self.env['mtd.api_request_tracker'].search([('id', '=', tracker_id)])
        api_token = self.env['mtd.api_tokens'].search([('api_id', '=', api_tracker.api_id)])

        if api_token:
            api_token.authorisation_code = auth_code
        else:
            api_token.create({
                'api_id': api_tracker.api_id,
                'api_name': api_tracker.api_name,
                'authorisation_code': auth_code
                })
        # self.current_record = record_id
        record = self.env['mtd.hello_world'].search([('id', '=', record_id)])
        token_location_uri = "https://test-api.service.hmrc.gov.uk/oauth/token"
        client_id = record.hmrc_configuration.client_id
        client_secret = record.hmrc_configuration.client_secret
        redirect_uri = "{}/auth-redirect".format(record.hmrc_configuration.redirect_url)

        data_user_info = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'code': auth_code
            }
        self._logger.info(
            "(Step 2) exchange authorisation code - Data which will be " +
            "sent in the request:-  {}".format(json.dumps(data_user_info))
        )
        headers = {
            'Content-Type': 'application/json',
            }
        self._logger.info(
            "(Step 2) exchange authorisation code - headers which will be "
            "sent in the request:-  {}".format(headers)
        )
        req = requests.post(token_location_uri, data=json.dumps(data_user_info), headers=headers)
        response_token = json.loads(req.text)
        self._logger.info(
            "(Step 2) exchange authorisation code - received " 
            "response of the request:- {}, and its text:- {}".format(req, response_token)
        )
        if req.ok:
            # get the record which we created when sending the request and update the response_received column
            # As this determines whether we can place another request or not
            record_tracker = self.env['mtd.api_request_tracker'].search([
                ('request_sent', '=', True),
                ('response_received', '=', False)
            ])
            record_tracker.response_received = True
            if not api_token:
                api_token = self.env['mtd.api_tokens'].search([('authorisation_code', '=', auth_code)])
            self._logger.info(
                "(Step 2) exchange authorisation code - api_token table id where info is stored:- {}".format(api_token)
            )
            api_token.access_token = response_token['access_token']
            api_token.refresh_token = response_token['refresh_token']
            api_token.expires_in = json.dumps(response_token['expires_in'])
            api_token.access_token_recieved_date = datetime.now()
            version = self._json_command('version', record_id=record_id)
            return version
        else:
            construct_text = (
                    "Date {}     Time {} \n".format(datetime.now().date(), datetime.now().time()) +
                    "Sorry. The connection failed ! \n" +
                    "Please check the log below for details. \n\n" +
                    "Connection Status Details: \n" +
                    "Request Sent: \n{} \n\n".format(token_location_uri) +
                    "Error Code:\n{} \n\n".format(req.status_code) +
                    "Response Received: \n{}\n{}".format(response_token['error'], response_token['error_description'])
            )
            self._logger.info(
                "(Step 2) exchange authorisation code - log:- {}".format(construct_text)
            )
            action = self.env.ref('account_mtd.action_mtd_hello_world')
            menu_id = self.env.ref('account_mtd.submenu_mtd_hello_world')
            self._logger.info(
                "(Step 2) exchange authorisation code - redirect URI :- " +
                "/web#id={}&view_type=form&model=mtd.hello_world".format(record_id) +
                "&menu_id=72&action={}".format(api_tracker.menu_id, api_tracker.action)
            )
            return werkzeug.utils.redirect(
                '/web#id={}&view_type=form&model=mtd.hello_world&'.format(record_id) +
                'menu_id=72&action={}'.format(api_tracker.menu_id, api_tracker.action)
            )

    def refresh_user_authorisation(self, token_record=None):
        self._logger.info("(Step 4) refresh_user_authorisation - token_record:- {}".format(token_record))
        api_token = self.env['mtd.api_tokens'].search([('id', '=', token_record.id)])
        hmrc_authorisation_url = "{}{}".format(self.hmrc_configuration.hmrc_url, '/oauth/token')
        self._logger.info(
            "(Step 4) refresh_user_authorisation - hmrc authorisation url:- {}".format(hmrc_authorisation_url)
        )

        data_user_info = {
            'client_secret': self.hmrc_configuration.client_secret,
            'client_id': self.hmrc_configuration.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': api_token.refresh_token
            }
        headers = {
            'Content-Type': 'application/json',
            }
        self._logger.info(
            "(Step 4) refresh_user_authorisation - data to send in request:- {}".format(data_user_info)
        )
        self._logger.info(
            "(Step 4) refresh_user_authorisation - headers to send in request:- {}".format(headers)
        )
        req = requests.post(hmrc_authorisation_url, data=json.dumps(data_user_info), headers=headers)
        response_token = json.loads(req.text)
        self._logger.info(
            "(Step 4) refresh_user_authorisation - received response " +
            "of the request:- {}, and its text:- {}".format(req, response_token)
        )
        if req.ok:
            api_token.access_token = response_token['access_token']
            api_token.refresh_token = response_token['refresh_token']
            api_token.expires_in = json.dumps(response_token['expires_in'])
            version = self._json_command('version')
            return version
        elif req.status_code == 400 and response_token['message'] == "Bad Request":
            self._logger.info(
                "(Step 4) refresh_user_authorisation - error 400, Need to obtain new access code and refresh token"
            )
            self.get_user_authorisation()
        else:
            construct_text = (
                    "Date {}     Time {} \n".format(datetime.now().date(), datetime.now().time()) +
                    "Sorry. The connection failed ! \n" +
                    "Please check the log below for details. \n\n" +
                    "Connection Status Details: \n" +
                    "Request Sent: \n{} \n\n".format(hmrc_authorisation_url) +
                    "Error Code:\n{} \n\n".format(req.status_code) +
                    "Response Received: \n{}".format(response_token['message'])
            )

            self._logger.info(
                "(Step 4) refresh_user_authorisation - other error:- {}".format(construct_text)
            )
            self.response_from_hmrc = construct_text
            return True
