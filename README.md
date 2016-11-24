# account\_invoice\_delivery\_address

Add delivery address field to Invoices.

Note this exposes it in the UI, and makes it available, but does not add it to the printouts.

The technical name of the field is `partner_shipping_id` on model `account.invoice`.

# account\_invoice\_delivery\_address\_sale

Copy delivery address when creating an invoice from a Sale Order.

Installed automatically if `account_invoice_delivery_address` and `sale` are installed together.

# account\_invoice\_delivery\_address\_stock

Copy delivery address when creating an invoice from a Delivery Order.

Installed automatically if `account_invoice_delivery_address` and `stock` are installed together.

# Copyright and License

Copyright (C) 2016 OpusVL

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

If you require assistance, support, or further development of this
software, please contact OpusVL using the details below:

* Telephone: +44 (0)1788 298 410
* Email: community@opusvl.com
* Web: http://opusvl.com
