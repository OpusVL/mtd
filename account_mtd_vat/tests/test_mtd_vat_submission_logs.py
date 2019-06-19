import datetime
import json

from odoo.tests import common

class GivenSimpleSubmissionLogEntry(common.TransactionCase):
    """Unit tests (for now) of bits of submission log entry code"""
    def setUp(self):
        super(GivenSimpleSubmissionLogEntry, self).setUp()
        fake_response = json.dumps(self.faked_response())
        self.logentry = (
            self.env['mtd_vat.vat_submission_logs'].create(dict(
                name='TEST LOG ENTRY',
                response_text=fake_response,
                start='2019-03-01',
                end='2019-05-31',
            ))
        )
        self.fake_now = datetime.datetime(2019, 6, 19, 9, 49, 30)

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

    def test_raw_processing_date(self):
        self.assertEqual(self.logentry.raw_processing_date,
            '2112-12-21T13:24:38')

    def test_success_message_format(self):
        result = self.env['mtd_vat.issue_request']._success_message(
            submission_log_entry=self.logentry,
            current_time=self.fake_now,
        )
        self.assertIn("Date 2019-06-19", result)
        self.assertIn("Time 09:49:30", result)
        self.assertIn("Period: 2019-03-01 - 2019-05-31", result)
        self.assertIn("Unique number: 42", result)
        self.assertIn("Payment indicator: INDIC8", result)
        self.assertIn("Charge ref number: 4224", result)
        self.assertIn("Processing date: 2112-12-21T13:24:38", result)


class GivenSubmissionLogEntryWithEmptyResponse_Tests(
        GivenSimpleSubmissionLogEntry):
    def faked_response(self):
        return dict()

    def test_expected_to_be_false_if_missing(self):
        for field in ['unique_number', 'payment_indicator', 'processing_date']:
            self.assertFalse(getattr(self.logentry, field), field)

    def test_charge_ref_number_is_humanised_missing_message(self):
        self.assertEqual(self.logentry.charge_ref_number, "No Data Found")

    def test_success_message_method_does_not_crash(self):
        # It's going to look weird and ugly with all those 'false's everywhere
        # but it should at least not crash.
        self.env['mtd_vat.issue_request']._success_message(
            submission_log_entry=self.logentry,
            current_time=self.fake_now,
        )
