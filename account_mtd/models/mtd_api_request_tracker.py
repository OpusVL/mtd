from odoo import models, fields, api

################################################################
#
# This module is created to keep track of any pending requests
# for access token. If one request is in process we can not
# send a request for a new one. This also contains information
# regarding where the request was sent from so when redirected
# back to Odoo we redirect user back to where they started from
#
#################################################################

class MtdApiRequestTracker(models.Model):
    _name = 'mtd.api_request_tracker'
    _description = "authorisation request table"

    user_id = fields.Integer('User Id', required=True)
    api_id = fields.Integer('API Id', required=True)
    api_name = fields.Char('API Name', required=True)
    endpoint_id = fields.Char('Endpoint Id', required=True)
    request_sent = fields.Boolean('Request Sent', required=True)
    closed = fields.Selection([
        ('timed_out', 'Request timed out'),
        ('response', 'Response received'),
    ], string='Tracker Closed')
    action = fields.Char('action', required=True)
    menu_id = fields.Char('menu Id', required=True)
