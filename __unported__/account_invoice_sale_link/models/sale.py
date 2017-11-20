# -*- coding: utf-8 -*-

##############################################################################
#
# Link to sales order from invoice
# Copyright (C) 2017 OpusVL (<http://opusvl.com/>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    created_invoice_ids = fields.One2many(
        comodel_name='account.invoice',
        inverse_name='source_sale_order_id',
        readonly=True,
    )


    @api.model
    def _prepare_invoice(self, order, lines):
        res = super(SaleOrder, self)._prepare_invoice(order, lines)
        res.update({'source_sale_order_id': order.id})
        return res




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
