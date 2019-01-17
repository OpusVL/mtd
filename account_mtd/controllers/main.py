import base64
from odoo import http
from datetime import datetime

class Authorize(http.Controller):
    
    @http.route('/auth-redirect', type='http', methods=['GET'])
    def get_user_authorization(self, **args):
        
        import pdb; pdb.set_trace()
        api_tracker = http.request.env['mtd.api_request_tracker'].search([('request_sent', '=', True),('request_received', '=', False)])
        if len(api_tracker) > 1:
            """We should never be in position in the first place as when the tokens are requested we are checking to see
            whether there is already a request in process if so then we have to wait"""
            #Work out which record we need to use make sure the record was created within last 10 mins
            now_datetime = datetime.now()
            time_10_mins_ago = now_datetime.timedelta(minutes=10)
            
            pass 
        else:
            api_tracker.request_received = False
            auth_code = args.get('code')
            api_token = http.request.env['mtd.api_tokens'].search([('api_id', '=', api_tracker.api_id)])
            if api_token:
                api_token.authorisation_code = auth_code
            else:
                api_token.create({
                    'api_id': api_tracker.api_id,
                    'api_name': api_tracker.api_name,
                    'authorisation_code': auth_code
                    })
            """now search for the method which we need to invoke to get to exchange the authorisation code with access token"""
            return http.request.env['mtd.hello_world'].exchange_user_authorisation(auth_code, api_tracker.endpoint_id)
            #return self.exchange_token(auth_code, api_tracker.endpoint_id)
        
        return True
    
    @http.route('/exchange/user/token', type='json', method=["POST"])
    def exchange_token(self, code, record_id):
        
        import pdb; pdb.set_trace()
        record = http.request.env['mtd.hello_world'].search([('id', '=', record_id)])
        token_location_uri = "https://test-api.service.hmrc.gov.uk/oauth/token"
        client_id = record.hmrc_credential.client_id
        client_secret = record.hmrc_credential.client_secret
        reirect_uri = "http://localhost:8090{}&code={}".format('/auth/access/token', code)
        auth_code = code 
        
        token_location_uri += "&client_secret={}&client_id={}&grant_type=authorization_code&redirect_uri={}".format(client_id,client_secret,reirect_uri)
        
        pass
