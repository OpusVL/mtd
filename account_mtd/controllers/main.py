import base64
import logging
from odoo import http, exceptions
from datetime import datetime, timedelta
from werkzeug.utils import redirect

_logger = logging.getLogger(__name__)


class Authorize(http.Controller):
    
    @http.route('/auth-redirect', type='http', methods=['GET'])
    def get_user_authorization(self, **args):
        # to determine which API the authorization code has been received for.
        api_trackers = http.request.env['mtd.api_request_tracker'].search([('closed', '=', False)])
        if len(api_trackers) != 1:
            # user should never be in a state where they found no tracker record.
            # They can be in a position where they may find more than one record,
            # in either case we need to then get user to reconnect
            _logger.info(
                "Found either none or more than one pending tracker request. " +
                "\nShould never find none, something seriously has gone wrong if found none." +
                "\nWe can have more than one if there was a request sent, and authorisation it was never completed." +
                "\nIf in this state we need to reset the tracker and get user to create a new connection " +
                "\napi_tracer = {}".format(api_trackers))
            for record in api_trackers:
                record.closed = 'more_than_one'
            werkzeug.utils.redirect('/web')
            raise exceptions.Warning(
                "No connection request made Please try to connect again!"
            )
            # This should then return to the home page
        else:
            # search for the method which we need to invoke to get to exchange the authorisation code with access token
            return (http.request.env['mtd.exchange_authorisation'].exchange_user_authorisation(
                args.get('code'),
                api_trackers.endpoint_id,
                api_trackers.id)
            )
        return True
