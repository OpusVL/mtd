# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from urllib.request import urlopen
from datetime import datetime

import requests
import os
import json
import logging

class MtdHelloWorld(models.Model):
    _name = 'mtd.hello_world'
    _description = "Hello world to test connection between Odoo and HMRC"
    
    _logger = logging.getLogger(__name__)
    
    name = fields.Char('Name', required=True)
    api_name = fields.Many2one(comodel_name="mtd.api", required=True)
    hmrc_credential = fields.Many2one(comodel_name="mtd.hmrc_credentials", required=True)
    scope = fields.Char(related="api_name.scope")
    response_from_hmrc = fields.Text(string="Response From HMRC")
    which_button_type_clicked = fields.Char(string="which_button")
    path = fields.Char(string="sandbox_url")
    
    
    @api.multi
    def action_hello_world_connect(self):
        self.which_button_type_clicked = "helloworld"
        self.path = "/hello/world"
        version = self._jason_command('version')
        
    @api.multi    
    def action_hello_application_connection(self):
        self.which_button_type_clicked = "application"
        self.path = "/hello/application"
        version = self._jason_command('version')
        
    @api.multi    
    def action_hello_user_connection(self):
        self.which_button_type_clicked = "user"
        self.path = "/hello/user"
        if not self.hmrc_credential.access_token and not self.hmrc_credential.refresh_token:
            #import pdb; pdb.set_trace()
            return self.get_user_authorisation(command = command, timeout=3)
        else:
            version = self._jason_command('version')
    
    def _jason_command(self, command, timeout=3):
        import pdb; pdb.set_trace()
        accessToken = self.hmrc_credential.access_token
        
        header_items = {"Accept": "application/vnd.hmrc.1.0+json"}
        if self.which_button_type_clicked == "application":
            header_items["authorization"] = ("Bearer "+self.hmrc_credential.server_token)
        elif self.which_button_type_clicked == "user":
            #need to first check if the user has any accessToken and refreshtoken
            #If not we need to proceed to the first and second step and then come to this step.
            header_items["authorization"] = ("Bearer "+str(accessToken))

        hmrc_connection_url = "{}{}".format(self.hmrc_credential.hmrc_url, self.path)
        self._logger.info('Url : %s', hmrc_connection_url)
        import pdb; pdb.set_trace()
        req = requests.get(hmrc_connection_url, timeout=3, headers=header_items)
        
        #import pdb; pdb.set_trace()
        if req.ok:
            test= "in the if"
            rec = self.env['mtd.hello_world'].search([('id', '=', self.id)])
            construct_text = """Date {}     Time {}
Congratulations ! The connection succeeded.
            
Connection Status Details: 
Request Sent:
{}
            
Response Received:
{}
        
        
            """.format(datetime.now().date(), datetime.now().time(), hmrc_connection_url, req.status_code, req.text)
            existing_response = rec.response_from_hmrc
            self.response_from_hmrc = construct_text if not self.response_from_hmrc else (construct_text + rec.response_from_hmrc)
            return True
            #self.response_from_hmrc =  (self.response_from_hmrc + construct_text)
#             raise exceptions.Warning("""Congratulations ! The connection succeeded. 
#             Please check the log below for details. 
#             
#             Connection Status Details: 
#             Request Sent:
#             {}
#             
#             Response Received:
#             {}
#             """.format(hmrc_connection_url, req.status_code, req.text))
            
        elif req.status_code == 401 and self.which_button_type_clicked == "user":
            self.refresh_user_authorisation()
            #import pdb; pdb.set_trace() 
            raise exceptions.Warning("Warning Warning ")
            
        else:
            test = "in the else"
            raise exceptions.Warning("""Sorry. The connection failed !
            Please check the log below for details.
            
            Connection Status Details: 
            Request Sent:
            {}
            
            Error Code:
            {}
            
            Response Received: 
            {}
            """.format(hmrc_connection_url, req.status_code, req.text))
        #import pdb; pdb.set_trace()

    def refresh_user_authorisation(self):
        ## *****************************************************
        ##WHAT WOULD HAPPEN IF THE WEBSITE INFORMATION WAS TO CHANGE IN THE FUTURE?
        ##AS THIS IS HARDCODED 
        ##******************************************************
        
        #refresh token link
        authorisation_url = "/https://test-api.service.hmrc.gov.uk/oauth/token"
        
        #Header to be passed into to get authorisation
        header_items = {"client_id":self.hmrc_credential.client_id,
                     "client_secret":self.hmrc_credential.client_secret,
                     "grant_type":"refresh_token",
                     "refresh_token":self.hmrc_credential.access_token}
    
    @api.multi
    def get_user_authorisation(self, command, timeout=3):
        
        
        client_id = self.hmrc_credential.client_id
        redirect_uri = "{}/auth-redirect".format(self.hmrc_credential.redirect_url)
        authorisation_url = ("https://test-api.service.hmrc.gov.uk/oauth/authorize?")
        state = ""
        #State is optional
        if self.hmrc_credential.state:
            #header_items["state"] = self.hmrc_credential.state
            state = "&state={}".format(self.hmrc_credential.state)
        
        authorisation_url += "response_type=code&client_id={}&scope={}{}&redirect_uri={}".format(self.hmrc_credential.client_id, self.scope, state, redirect_uri)  
        #import pdb; pdb.set_trace()
        
        #import pdb; pdb.set_trace() 
        req = requests.get(authorisation_url, timeout=3)
        
        if req.ok:
            #Update the information onto the api tracker table
            tracker_api = self.env['mtd.api_request_tracker']
            tracker_api.create({
                'user_id': self._uid,
                'api_id': self.api_name.id,
                'api_name': self.api_name.name,
                'endpoint_id': self.id,
                'request_sent': True
                })

            return {'url': authorisation_url, 'type': 'ir.actions.act_url', 'target': 'self', 'res_id': self.id}
        else:
            raise exceptions.Warning("""Sorry. The connection failed !
            Please check the log below for details.
            MY TEST
            Connection Status Details: 
            Request Sent:
            {}
            
            Error Code:
            {}
            
            Response Received: 
            {}
            """.format(authorisation_url, req.status_code, req.text))
            
    @api.multi        
    def exchange_user_authorisation(self, code, record_id):
        
        record = self.env['mtd.hello_world'].search([('id', '=', record_id)])
        token_location_uri = "https://test-api.service.hmrc.gov.uk/oauth/token"
        client_id = record.hmrc_credential.client_id
        client_secret =record.hmrc_credential.client_secret
        redirect_uri = "http://localhost:8090/auth-redirect"#{}&code={}".format('/auth/access/token', code)
        auth_code = code
        
        data_user_info = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'code': auth_code
            }
        headers = {
            'Content-Type': 'application/json',
            }
        data_json = json.dumps(data_user_info)
        req = requests.post(token_location_uri, data=json.dumps(data_user_info), headers=headers)
        import pdb; pdb.set_trace()
        if req.ok:
            response_tokens = json.load(req.text)
            """get the record which we created when sending the request and update the request_received column 
            As this determines whether we can place another request or not """
            now_datetime = datetime.now()
            time_10_mins_ago = now_datetime.timedelta(minutes=10)
            record = self.env['mtd.api_request_tracker'].search([('request_sent', '=', True), ('request_received', '=', False), ('created_date', '<=', time_10_mins_ago)])
            record.request_received
        
        
        