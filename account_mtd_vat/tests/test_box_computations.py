import unittest

from openerp.addons.account_mtd_vat import hmrc_vat as H

class GivenKnownBoxNumbers(unittest.TestCase):
    def setUp(self):
        super(GivenKnownBoxNumbers, self).setUp()
        self.known_boxes = {
            H.Box.VAT_DUE_SALES: 60,
            H.Box.VAT_DUE_ACQUISITIONS: 52.50,
            H.Box.VAT_RECLAIMED_ON_INPUTS: 1582.50,
            H.Box.TOTAL_VALUE_SALES: 600,
            H.Box.TOTAL_VALUE_PURCHASES: 8100,
            H.Box.TOTAL_VALUE_GOODS_SUPPLIED: 300,
            H.Box.TOTAL_VALUE_ACQUISITIONS: 450,
        }

class GivenComputedBoxes_Tests(GivenKnownBoxNumbers):
    def setUp(self):
        super(GivenComputedBoxes_Tests, self).setUp()
        self.computed_boxes = H.Box.compute_all(self.known_boxes)

    def test_different_dictionary_returned(self):
        self.assertIsNot(self.computed_boxes, self.known_boxes)

    def assertComputedBoxEquals(self, boxcode, expected):
        self.assertEqual(
            self.computed_boxes[boxcode], expected, "Box {!r}".format(boxcode))

    def test_previously_known_values(self):
        self.assertComputedBoxEquals(H.Box.VAT_DUE_SALES, 60)
        self.assertComputedBoxEquals(H.Box.VAT_DUE_SALES, 60)
        self.assertComputedBoxEquals(H.Box.VAT_DUE_ACQUISITIONS, 52.50)
        self.assertComputedBoxEquals(H.Box.VAT_RECLAIMED_ON_INPUTS, 1582.50)
        self.assertComputedBoxEquals(H.Box.TOTAL_VALUE_SALES, 600)
        self.assertComputedBoxEquals(H.Box.TOTAL_VALUE_PURCHASES, 8100)
        self.assertComputedBoxEquals(H.Box.TOTAL_VALUE_GOODS_SUPPLIED, 300)
        self.assertComputedBoxEquals(H.Box.TOTAL_VALUE_ACQUISITIONS, 450)

    def test_vat_due_computation(self):
        self.assertComputedBoxEquals(H.Box.TOTAL_VAT_DUE, 112.50)

    def test_net_vat_due_computation(self):
        # Should be positive because HMRC demand that
        self.assertComputedBoxEquals(H.Box.NET_VAT_DUE, 1470.00)
