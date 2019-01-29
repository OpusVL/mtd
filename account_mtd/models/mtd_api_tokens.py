from odoo import models, fields, api

##############################################################
#
# This module is created to store access token, authorisation
# code and refresh_token for each api. Access token expires
# after every 4 hours which need to be refreshed using the
# refresh token. Further, the access token becomes invalid
# after 18 months of it being issued or if revoked manually
# by the user or for any other reason, at which point it
# will need to be reissued by granting authority.
#
##############################################################

class MtdApiTokens(models.Model):
    _name = 'mtd.api_tokens'
    _description = "api token table"
    
    api_id = fields.Char('API Id', required=True)
    api_name = fields.Char('API Name', required=True)
    authorisation_code = fields.Char('Authorisation Code', required=True)
    access_token = fields.Char('Access Token')
    refresh_token = fields.Char('Refresh Token')
    expires_in = fields.Char('Expires In')
    access_token_recieved_date = fields.Datetime()
