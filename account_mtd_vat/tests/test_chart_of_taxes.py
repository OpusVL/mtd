from openerp.tests import common

class ChartOfTaxesDomainTests(common.TransactionCase):
    def test_domain_for_O1851_example(self):
        result = (
            self.env['account.tax.code']
            .with_context(
                state='all',
                date_from='2018-12-01',
                date_to='2019-02-28',
                company_id=1,
                vat='unposted',
            )
            .move_line_domain_for_chart_of_taxes_row(tax_code_id=8)
        )
        expected_domain = [
            ('date', '>=', '2018-12-01'),
            ('date', '<=', '2019-02-28'),
            ('move_id.state', 'in', ('draft', 'posted')),
            ('tax_code_id', 'child_of', 8),
            ('company_id', '=', 1),
            ('vat', '=', False),
            ('state', '!=', 'draft'),
        ]
        self.assertItemsEqual(
            # assertItemsEqual will not work if we ever want '|', '!' or '&'
            #  operators, as order will then matter.
            sorted(result), sorted(expected_domain)
        )
