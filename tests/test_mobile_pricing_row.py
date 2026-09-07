import sys
import unittest
from decimal import Decimal
from pathlib import Path

APPLICATION_ROOT = Path(__file__).resolve().parent.parent

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(0, str(APPLICATION_ROOT))

from app.models.mobile_pricing_row import MobilePricingRow


class TestMobilePricingRow(unittest.TestCase):

    def test_creates_mobile_pricing_row(self) -> None:
        row = MobilePricingRow(
            country="Test Country",
            iso2="TC",

            baseline_sms_outbound_price=Decimal("0.0100"),
            baseline_sms_inbound_price=Decimal("0.0200"),
            baseline_voice_outbound_price=Decimal("0.0300"),
            baseline_voice_inbound_price=Decimal("0.0400"),

            enterprise_sms_outbound_price=Decimal("0.0090"),
            enterprise_sms_inbound_price=Decimal("0.0180"),
            enterprise_voice_outbound_price=Decimal("0.0270"),
            enterprise_voice_inbound_price=Decimal("0.0360")
        )

        self.assertEqual(row.country, "Test Country")
        self.assertEqual(row.iso2, "TC")

        self.assertEqual(
            row.baseline_sms_outbound_price,
            Decimal("0.0100")
        )

        self.assertEqual(
            row.baseline_sms_inbound_price,
            Decimal("0.0200")
        )

        self.assertEqual(
            row.baseline_voice_outbound_price,
            Decimal("0.0300")
        )

        self.assertEqual(
            row.baseline_voice_inbound_price,
            Decimal("0.0400")
        )

        self.assertEqual(
            row.enterprise_sms_outbound_price,
            Decimal("0.0090")
        )

        self.assertEqual(
            row.enterprise_sms_inbound_price,
            Decimal("0.0180")
        )

        self.assertEqual(
            row.enterprise_voice_outbound_price,
            Decimal("0.0270")
        )

        self.assertEqual(
            row.enterprise_voice_inbound_price,
            Decimal("0.0360")
        )

    def test_mobile_pricing_row_is_immutable(self) -> None:
        row = MobilePricingRow(
            country="Test Country",
            iso2="TC",

            baseline_sms_outbound_price=Decimal("0.0100"),
            baseline_sms_inbound_price=Decimal("0.0200"),
            baseline_voice_outbound_price=Decimal("0.0300"),
            baseline_voice_inbound_price=Decimal("0.0400"),

            enterprise_sms_outbound_price=Decimal("0.0090"),
            enterprise_sms_inbound_price=Decimal("0.0180"),
            enterprise_voice_outbound_price=Decimal("0.0270"),
            enterprise_voice_inbound_price=Decimal("0.0360")
        )

        with self.assertRaises(Exception):
            row.iso2 = "XX"


if __name__ == "__main__":
    unittest.main()