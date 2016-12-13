# -*- coding: utf-8 -*-

##############################################################################
#
# Extensible Account Entries Analysis Report
# Copyright (C) 2016 OpusVL (<http://opusvl.com/>)
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

from openerp import tools
from openerp import models, fields, api

class AccountEntriesReport(models.Model):
    _inherit = 'account.entries.report'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_entries_report')
        cr.execute(self._view_definition())

    def _view_definition(self):
        select_part = self._view_definition_select()
        view_definition = """
            create or replace view account_entries_report as (
            select {select}
            from
                account_move_line l
                left join account_account a on (l.account_id = a.id)
                left join account_move am on (am.id=l.move_id)
                left join account_period p on (am.period_id=p.id)
                where l.state != 'draft'
            )
        """.format(select=self._view_definition_select())
        return view_definition

    def _view_definition_select(self):
        """Return all the stuff that comes inside the "SELECT" part of the view definition query.

        Typically an extension will call this version with super(), and then append a comma followed by more column
        definitions.
        """
        # If core Odoo's version changes, update upstream_part to suit.
        upstream_part = """
                l.id as id,
                am.date as date,
                l.date_maturity as date_maturity,
                l.date_created as date_created,
                am.ref as ref,
                am.state as move_state,
                l.state as move_line_state,
                l.reconcile_id as reconcile_id,
                l.partner_id as partner_id,
                l.product_id as product_id,
                l.product_uom_id as product_uom_id,
                am.company_id as company_id,
                am.journal_id as journal_id,
                p.fiscalyear_id as fiscalyear_id,
                am.period_id as period_id,
                l.account_id as account_id,
                l.analytic_account_id as analytic_account_id,
                a.type as type,
                a.user_type as user_type,
                1 as nbr,
                l.quantity as quantity,
                l.currency_id as currency_id,
                l.amount_currency as amount_currency,
                l.debit as debit,
                l.credit as credit,
                coalesce(l.debit, 0.0) - coalesce(l.credit, 0.0) as balance"""
        return upstream_part
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
