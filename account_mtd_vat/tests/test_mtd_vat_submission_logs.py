import json

from openerp.tests import common

class GivenSimpleSubmissionLogEntry(common.TransactionCase):
    def setUp(self):
        super(GivenSimpleSubmissionLogEntry, self).setUp()
        fake_response = json.dumps(self.faked_response())
        self.logentry = (
            self.env['mtd_vat.vat_submission_logs'].create(dict(
                name='TEST LOG ENTRY',
                response_text=fake_response,
            ))
        )

    def faked_response(self):
        self.skipTest("ABSTRACT: faked_response()")


class GivenSubmissionLogEntryWithFullResponse_Tests(
        GivenSimpleSubmissionLogEntry):
    def faked_response(self):
        return {
            'formBundleNumber': '42',
            'paymentIndicator': 'INDIC8',
            'processingDate': '2112-12-21T13:24:38',
            'chargeRefNumber': '4224',
        }

    def test_unique_number(self):
        self.assertEqual(self.logentry.unique_number, '42')

    def test_payment_indicator(self):
        self.assertEqual(self.logentry.payment_indicator, 'INDIC8')

    def test_processing_date(self):
        self.assertEqual(self.logentry.processing_date, '2112-12-21 13:24:38')

    def test_charge_ref_number(self):
        self.assertEqual(self.logentry.charge_ref_number, '4224'),


class GivenSubmissionLogEntryWithEmptyResponse_Tests(
        GivenSimpleSubmissionLogEntry):
    def faked_response(self):
        return dict()

    def test_expected_to_be_false_if_missing(self):
        for field in ['unique_number', 'payment_indicator', 'processing_date']:
            self.assertFalse(getattr(self.logentry, field), field)

    def test_charge_ref_number_is_humanised_missing_message(self):
        self.assertEqual(self.logentry.charge_ref_number, "No Data Found")
