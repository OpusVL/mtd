import base64
import logging
from odoo import http, exceptions
from datetime import datetime, timedelta
from werkzeug.utils import redirect


class Authorize(http.Controller):
    _logger = logging.getLogger(__name__)
    
    @http.route('/auth-redirect', type='http', methods=['GET'])
    def get_user_authorization(self, **args):
        
        # to determine which API the authorization code has been received for.
        api_tracker = http.request.env['mtd.api_request_tracker'].search([('closed', '=', False)])
        if len(api_tracker) != 1:
            # user should never be in a state where they found no tracker record.
            # They can be in a position where they may find more than one record,
            # in either case we need to then get user to reconnect
            self._logger.info(
                "Found either none or more than one pending tracker request. " +
                "\nShould never find none, something seriously has gone wrong if found none."+
                "\nWe can have more than one if there was an initial request and authorisation it was never completed."+
                "\nIf in this state we need to reset the tracker and get user to create a new connection " +
                "\napi_tracer = {}".format(api_tracker))
            for record in api_tracker:
                record.response_received = True
            werkzeug.utils.redirect('/web')
            raise exceptions.Warning(
                "No connection request made Please try to connect again!"
            )
            # This should then return to the home page
        else:
            # search for the method which we need to invoke to get to exchange the authorisation code with access token
            return (http.request.env['mtd.hello_world'].exchange_user_authorisation(
                args.get('code'),
                api_tracker.endpoint_id,
                api_tracker.id)
            )
        return True
