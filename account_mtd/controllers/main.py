import base64
from odoo import http
from datetime import datetime
from werkzeug.utils import redirect

class Authorize(http.Controller):
    
    @http.route('/auth-redirect', type='http', methods=['GET'])
    def get_user_authorization(self, **args):
        
        # to determine which API the authorization code has been received for.
        api_tracker = http.request.env['mtd.api_request_tracker'].search([('request_sent', '=', True),('request_received', '=', False)])
        if len(api_tracker) > 1:
            """We should never be in position in the first place as when the tokens are requested we are checking to see
            whether there is already a request in process if so then we have to wait"""
            # Work out which record we need to use make sure the record was created within last 10 mins
            now_datetime = datetime.now()
            time_10_mins_ago = now_datetime.timedelta(minutes=10)
            
            pass 
        else:
            """search for the method which we need to invoke to get to exchange the authorisation code with access token"""
            return http.request.env['mtd.hello_world'].exchange_user_authorisation(args.get('code'), api_tracker.endpoint_id, api_tracker.id)
            # return self.exchange_token(auth_code, api_tracker.endpoint_id)
        
        return True
