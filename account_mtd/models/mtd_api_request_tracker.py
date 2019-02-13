from odoo import models, fields, api


class MtdApiRequestTracker(models.Model):
    """
    This module is created to keep track of any pending requests
    for access token. If one request is in process we can not
    send a request for a new one. This also contains information
    regarding where the request was sent from so when redirected
    back to Odoo we redirect user back to where they started from
    """
    _name = 'mtd.api_request_tracker'
    _description = "authorisation request table"

    user_id = fields.Integer(required=True)
    api_id = fields.Many2one(comodel_name="mtd.api", required=True)
    api_name = fields.Char(related="api_id.name")
    endpoint_id = fields.Char(required=True)
    request_sent = fields.Boolean(required=True)
    closed = fields.Selection([
        ('timed_out', 'Request timed out'),
        ('response', 'Response received'),
        ('more_than_one', 'More than one open tracker found'),
        ('error', 'There was an error')

    ], string='Tracker Closed')
    action = fields.Char(required=True)
    menu_id = fields.Char(required=True)
    module_name = fields.Char(required=True)
