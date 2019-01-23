import base64
from odoo import http
from datetime import datetime, timedelta
from werkzeug.utils import redirect


class Authorize(http.Controller):
    
    @http.route('/auth-redirect', type='http', methods=['GET'])
    def get_user_authorization(self, **args):
        
        # to determine which API the authorization code has been received for.
        api_tracker = http.request.env['mtd.api_request_tracker'].search([
            ('request_sent', '=', True),
            ('response_received', '=', False)
        ])
        if len(api_tracker) > 1:
            # We should never be in position in the first place as when the tokens are requested we are checking to see
            # whether there is already a request in process if so then we have to wait 
            # to work out which record we need to use, make sure the record was created within the last 10 mins
            pass
            now_datetime = datetime.now()
            time_10_mins_ago = now_datetime - timedelta(minutes=10)
            time_10_mins_ago = (datetime.now() - timedelta(minutes=10))
            format_time_10_mins_ago = time_10_mins_ago.isoformat()

#             for record in api_tracker:
#                 if

            ################################################
            # 
            # TO DO - should never be in this postion but if for any
            # reason user is in this position we need to fix this 
            #
            ################################################
            pass 
        else:
            # search for the method which we need to invoke to get to exchange the authorisation code with access token
            return (http.request.env['mtd.hello_world'].exchange_user_authorisation(
                args.get('code'),
                api_tracker.endpoint_id,
                api_tracker.id)
            )
        return True
