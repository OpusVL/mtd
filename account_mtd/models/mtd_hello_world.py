# -*- coding: utf-8 -*-

import requests
import os
import json
import logging
import werkzeug

from odoo import models, fields, api, exceptions
from urllib.request import urlopen
from datetime import datetime, timedelta
from werkzeug import utils

class MtdHelloWorld(models.Model):
    _name = 'mtd.hello_world'
    _description = "Hello world to test connection between Odoo and HMRC"
    
    _logger = logging.getLogger(__name__)
    
    name = fields.Char('Name', required=True)
    api_name = fields.Many2one(comodel_name="mtd.api", required=True)
    hmrc_credential = fields.Many2one(comodel_name="mtd.hmrc_credentials", string ='HMRC Credentials', required=True)
    scope = fields.Char(related="api_name.scope")
    response_from_hmrc = fields.Text(string="Response From HMRC")
    which_button_type_clicked = fields.Char(string="which_button")
    path = fields.Char(string="sandbox_url")
    current_record = fields.Char()
    # need a variable which will keep the record id so that when we
    
    
    @api.multi
    def action_hello_world_connection(self):
        if self.name == "Hello World":
            self.which_button_type_clicked = "helloworld"
            self.path = "/hello/world"
            version = self._json_command('version')
            self._logger.info("Connection button Clicked - endpoint name {}, Path to add at the end or redirect url:- {}".format(self.name, self.path))
        elif self.name =="Hello Application":
            self.which_button_type_clicked = "application"
            self.path = "/hello/application"
            version = self._json_command('version')
            self._logger.info("Connection button Clicked - endpoint name {}, Path to add at the end or redirect url:- {}".format(self.name, self.path))
        elif self.name == "Hello User":
            self.which_button_type_clicked = "user"
            self.path = "/hello/user"
            self._logger.info("Connection button Clicked - endpoint name {}, Path to add at the end or redirect url:- {}".format(self.name, self.path))
            #search for token record for the API
            token_record = self.env['mtd.api_tokens'].search([('api_id', '=', self.api_name.id)])
            self._logger.info("Connection button Clicked - endpoint name {}, and the api is :- {}".format(self.name, self.api_name))
            if not token_record.access_token and not token_record.refresh_token:
                self._logger.info("Connection button Clicked - endpoint name {}, No access token found and no refresh_token found from the token record table.".format(self.name))
                record = self.env['mtd.api_request_tracker'].search([('request_sent', '=', True), ('request_received', '=', False)])
                self._logger.info("Connection button Clicked - endpoint name {}, Checking to see if there already a request in process".format(self.name))
                if record:
                     raise exceptions.Warning("""An authorisation request is already in process!!!
                     Please try again later""")
                else:
                    self._logger.info("Connection button Clicked - endpoint name {}, no Pending requests".format(self.name))
                    return self.get_user_authorisation()
            else:
                self._logger.info("Connection button Clicked - endpoint name {}, We have access token and refresh token".format(self.name))
                version = self._json_command('version')
    
    def _json_command(self, command, timeout=3, record_id=None):
        #this will determine where we have come from
        #if there is no current record then we know we already had valid record to gain all the information for hello user
        self._logger.info("_json_command - has record_id been provided?:- {}".format(record_id))
        if record_id:
            self = self.env['mtd.hello_world'].search([('id', '=', record_id)])
            self._logger.info("_json_command - we need to find the record and assign it to self")
        #search the token table to see if we have access token
        token_record = self.env['mtd.api_tokens'].search([('api_id', '=', self.api_name.id)])
        access_token = token_record.access_token if token_record else ""
        refresh_token = token_record.refresh_token if token_record else ""
        
        header_items = {"Accept": "application/vnd.hmrc.1.0+json"}
        if self.which_button_type_clicked == "application":
            header_items["authorization"] = ("Bearer "+self.hmrc_credential.server_token)
        elif self.which_button_type_clicked == "user":
            #need to first check if the user has any accessToken and refreshtoken
            #If not we need to proceed to the first and second step and then come to this step.
            header_items["authorization"] = ("Bearer "+str(access_token))

        hmrc_connection_url = "{}{}".format(self.hmrc_credential.hmrc_url, self.path)
        self._logger.info("_json_command - hmrc connection url:- {}, headers:- {}".format(hmrc_connection_url, header_items))
        req = requests.get(hmrc_connection_url, timeout=3, headers=header_items)
        response_token = json.loads(req.text)
        self._logger.info("_json_command - received respponse of the request:- {}, and its text:- {}".format(req, response_token))
        if req.ok:
            test= "in the if"
            #rec = self.env['mtd.hello_world'].search([('id', '=', self.id)])
            construct_text = """Date {}     Time {}
Congratulations ! The connection succeeded.
Please check the log below for details.
            
Connection Status Details: 
Request Sent:
{}
            
Response Received:
{}
          
{}
""".format(datetime.now().date(), datetime.now().time(), hmrc_connection_url, req.status_code, response_token['message'])
            self.response_from_hmrc = construct_text
            if record_id:
                self._logger.info("_json_command - response received ok we have record id so we return werkzeug.utils.redirect".format(req, response_token))
                self._logger.info("-------Redirect is:- /web#id={}&view_type=form&model=mtd.hello_world&menu_id=72&action=86".format(record_id))
                #action_id
                action = self.env.ref('account_mtd.action_mtd_hello_world')
                #menu_id
                menu_id = self.env.ref('account_mtd.submenu_mtd_hello_world')
                return werkzeug.utils.redirect('/web#id={}&view_type=form&model=mtd.hello_world&menu_id={}&action={}'.format(record_id, menu_id, action))
            return True
            
        elif req.status_code == 401 and self.which_button_type_clicked == "user" and response_token['message'] == "Invalid Authentication information provided":
            self._logger.info("_json_command - code 401 found, is user and message was:- {} ".format(response_token['message']))
            return self.refresh_user_authorisation(token_record)
            
        else:
            construct_text = """Date {}     Time {}
Sorry. The connection failed !
Please check the log below for details.

Connection Status Details: 
Request Sent:
{}

Error Code:
{}

Response Received: 
{}
{}
            """.format(datetime.now().date(), datetime.now().time(), hmrc_connection_url, req.status_code, response_token['message'])
            self._logger.info("_json_command - other error found:- {} ".format(construct_text))
            self.response_from_hmrc = construct_text
            if record_id:
                action = self.env.ref('account_mtd.action_mtd_hello_world')
                #menu_id
                menu_id = self.env.ref('account_mtd.submenu_mtd_hello_world')
                return werkzeug.utils.redirect('/web#id={}&view_type=form&model=mtd.hello_world&menu_id={}&action={}'.format(record_id, menu_id, action))
            return True
    
    @api.multi
    def get_user_authorisation(self):
        #Update the information in the api tracker table
        self._logger.info("(Step 1) Get authorisation")
        tracker_api = self.env['mtd.api_request_tracker']
        tracker_api.create({
            'user_id': self._uid,
            'api_id': self.api_name.id,
            'api_name': self.api_name.name,
            'endpoint_id': self.id,
            'request_sent': True
            })
        
        client_id = self.hmrc_credential.client_id
        redirect_uri = "{}/auth-redirect".format(self.hmrc_credential.redirect_url)
        authorisation_url = ("https://test-api.service.hmrc.gov.uk/oauth/authorize?")
        self._logger.info("(Step 1) Get authorisation - authorisation URI used:- {}".format(authorisation_url))
        state = ""
        #State is optional
        if self.hmrc_credential.state:
            #header_items["state"] = self.hmrc_credential.state
            state = "&state={}".format(self.hmrc_credential.state)
        
        authorisation_url += "response_type=code&client_id={}&scope={}{}&redirect_uri={}".format(self.hmrc_credential.client_id, self.scope, state, redirect_uri)
        self._logger.info("(Step 1) Get authorisation - authorisation URI used to send request:- {}".format(authorisation_url))
        req = requests.get(authorisation_url, timeout=3)
        response_token = json.loads(req.text)
        self._logger.info("(Step 1) Get authorisation - received respponse of the request:- {}, and its text:- {}".format(req, response_token))
        if req.ok:
            return {'url': authorisation_url, 'type': 'ir.actions.act_url', 'target': 'self', 'res_id': self.id}
        else:
            construct_text = """Date {}     Time {}
Sorry. The connection failed !
Please check the log below for details.
MY TEST
Connection Status Details:
Request Sent:
{}

Error Code:
{}

Response Received:
{}
""".format(datetime.now().date(), datetime.now().time(), authorisation_url, req.status_code, response_token=['message'])
            self.response_from_hmrc = construct_text
            return True
            
    @api.multi        
    def exchange_user_authorisation(self, auth_code, record_id, tracker_id):
        self._logger.info("(Step 2) exchange authorization code")
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
        #self.current_record = record_id
        record = self.env['mtd.hello_world'].search([('id', '=', record_id)])
        token_location_uri = "https://test-api.service.hmrc.gov.uk/oauth/token"
        client_id = record.hmrc_credential.client_id
        client_secret =record.hmrc_credential.client_secret
        redirect_uri = "http://localhost:8090{}".format('/auth-redirect')#{}&code={}".format('/auth/access/token', code)


        data_user_info = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'code': auth_code
            }
        self._logger.info("(Step 2) exchange authorization code - Data which will be asend in the request:-  {}".format(json.dumps(data_user_info)))
        headers = {
            'Content-Type': 'application/json',
            }
        self._logger.info("(Step 2) exchange authorization code - headers which will be asend in the request:-  {}".format(headers))
        req = requests.post(token_location_uri, data=json.dumps(data_user_info), headers=headers)
        response_token = json.loads(req.text)
        self._logger.info("(Step 2) exchange authorization code - received respponse of the request:- {}, and its text:- {}".format(req, response_token))
        if req.ok:
            """get the record which we created when sending the request and update the request_received column 
            As this determines whether we can place another request or not """
            time_10_mins_ago = (datetime.now() - timedelta(minutes=10))
            format_time_10_mins_ago = time_10_mins_ago.isoformat()
            record_tracker = self.env['mtd.api_request_tracker'].search([('request_sent', '=', True), ('request_received', '=', False)])
            record_tracker.request_received = True
            if not api_token:
                api_token = self.env['mtd.api_tokens'].search([('authorisation_code', '=', auth_code)])
            self._logger.info("(Step 2) exchange authorization code - api_token table id where info is stored:- {}".format(api_token))
            api_token.access_token = response_token['access_token']
            api_token.refresh_token = response_token['refresh_token']
            api_token.expires_in = json.dumps(response_token['expires_in'])
            api_token.access_token_recieved_date = datetime.now()
            version = self._json_command('version', record_id=record_id)
            return version
        else:
            construct_text = """Date {}     Time {}
Sorry. The connection failed !
Please check the log below for details.

Connection Status Details: 
Request Sent:
{}

Error Code:
{}

Response Received: 
{}

            """.format(datetime.now().date(), datetime.now().time(), token_location_uri, req.status_code, response_token['message'])
            self._logger.info("(Step 2) exchange authorization code - log:- {}".format(construct_text))
            #action_id
            action = self.env.ref('account_mtd.action_mtd_hello_world')
            #menu_id
            menu_id = self.env.ref('account_mtd.submenu_mtd_hello_world')

            return werkzeug.utils.redirect('/web#id={}&view_type=form&model=mtd.hello_world&menu_id=72&action={}'.format(record_id, menu_id, action))

    def refresh_user_authorisation(self, token_record=None):
        api_token = self.env['mtd.api_tokens'].search([('id', '=', token_record.id)])
        hmrc_authorisation_url = "{}{}".format(self.hmrc_credential.hmrc_url, '/oauth/token')

        data_user_info = {
            'client_secret': self.hmrc_credential.client_secret,
            'client_id': self.hmrc_credential.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': api_token.refresh_token
            }
        headers = {
            'Content-Type': 'application/json',
            }
        req = requests.post(hmrc_authorisation_url, data=json.dumps(data_user_info), headers=headers)
        response_token = json.loads(req.text)
        if req.ok:
            api_token.access_token = response_token['access_token']
            api_token.refresh_token = response_token['refresh_token']
            api_token.expires_in = json.dumps(response_token['expires_in'])
            version = self._json_command('version')
            return version
        elif req.status_code == 400 and response_token['message'] == "Bad Request":
            self.get_user_authorisation()
        else:
            construct_text = """Date {}     Time {}
Sorry. The connection failed !
Please check the log below for details.

Connection Status Details:
Request Sent:
{}

Error Code:
{}

Response Received:
{}

            """.format(datetime.now().date(), datetime.now().time(), token_location_uri, req.status_code, response_token['message'])
            record.response_from_hmrc = construct_text

