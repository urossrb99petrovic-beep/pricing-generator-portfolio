import sys
import unittest
from decimal import Decimal
from pathlib import Path

APPLICATION_ROOT = Path(__file__).resolve().parent.parent

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(0, str(APPLICATION_ROOT))

from app.models.voice_pricing_row import VoicePricingRow


class TestVoicePricingRow(unittest.TestCase):

    def test_creates_voice_pricing_row_with_outbound_prices(self) -> None:
        row = VoicePricingRow(
            country="Test Country",
            iso2="TC",
            baseline_mobile_price=Decimal("0.1000"),
            baseline_landline_price=Decimal("0.0800"),
            enterprise_mobile_price=Decimal("0.0900"),
            enterprise_landline_price=Decimal("0.0700")
        )

        self.assertEqual(row.country, "Test Country")
        self.assertEqual(row.iso2, "TC")

        self.assertEqual(
            row.baseline_mobile_price,
            Decimal("0.1000")
        )

        self.assertEqual(
            row.baseline_landline_price,
            Decimal("0.0800")
        )

        self.assertEqual(
            row.enterprise_mobile_price,
            Decimal("0.0900")
        )

        self.assertEqual(
            row.enterprise_landline_price,
            Decimal("0.0700")
        )

        self.assertIsNone(row.baseline_inbound_price)
        self.assertIsNone(row.enterprise_inbound_price)
        self.assertIsNone(row.number_type)

    def test_creates_voice_pricing_row_with_inbound_prices(self) -> None:
        row = VoicePricingRow(
            country="Test Country",
            iso2="TC",
            baseline_mobile_price=Decimal("0.1000"),
            baseline_landline_price=Decimal("0.0800"),
            enterprise_mobile_price=Decimal("0.0900"),
            enterprise_landline_price=Decimal("0.0700"),
            baseline_inbound_price=Decimal("0.0500"),
            enterprise_inbound_price=Decimal("0.0400")
        )

        self.assertEqual(
            row.baseline_inbound_price,
            Decimal("0.0500")
        )

        self.assertEqual(
            row.enterprise_inbound_price,
            Decimal("0.0400")
        )

    def test_creates_voice_pricing_row_with_number_type(self) -> None:
        row = VoicePricingRow(
            country="Test Country",
            iso2="TC",
            baseline_mobile_price=Decimal("0.1000"),
            baseline_landline_price=Decimal("0.0800"),
            enterprise_mobile_price=Decimal("0.0900"),
            enterprise_landline_price=Decimal("0.0700"),
            number_type="Global Mobile Numbers"
        )

        self.assertEqual(
            row.number_type,
            "Global Mobile Numbers"
        )

    def test_voice_pricing_row_is_immutable(self) -> None:
        row = VoicePricingRow(
            country="Test Country",
            iso2="TC",
            baseline_mobile_price=Decimal("0.1000"),
            baseline_landline_price=Decimal("0.0800"),
            enterprise_mobile_price=Decimal("0.0900"),
            enterprise_landline_price=Decimal("0.0700")
        )

        with self.assertRaises(Exception):
            row.country = "Changed Country"


if __name__ == "__main__":
    unittest.main()