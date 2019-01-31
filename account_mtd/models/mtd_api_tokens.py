from odoo import models, fields, api


class MtdApiTokens(models.Model):
    """
    This module is created to store access token, authorisation
    code and refresh_token for each api. Access token expires
    after every 4 hours which need to be refreshed using the
    refresh token. Further, the access token becomes invalid
    after 18 months of it being issued or if revoked manually
    by the user or for any other reason, at which point it
    will need to be reissued by granting authority.
    """
    _name = 'mtd.api_tokens'
    _description = "api token table"
    
    api_id = fields.Many2one(comodel_name="mtd.api", required=True)
    api_name = fields.Char(related="api_id.name")
    authorisation_code = fields.Char(required=True)
    access_token = fields.Char()
    refresh_token = fields.Char()
    expires_in = fields.Char()
    access_token_recieved_date = fields.Datetime()
