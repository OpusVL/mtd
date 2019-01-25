from odoo import models, fields, api


class MtdApiRequestTracker(models.Model):
    _name = 'mtd.api_request_tracker'
    _description = "authorisation request table"

    user_id = fields.Integer('User Id', required=True)
    api_id = fields.Integer('API Id', required=True)
    api_name = fields.Char('API Name', required=True)
    endpoint_id = fields.Char('Endpoint Id', required=True)
    request_sent = fields.Boolean('Request Sent', required=True)
    response_received = fields.Boolean('Response Received')
    action = fields.Char('action', required=True)
    menu_id = fields.Char('menu Id', required=True)
