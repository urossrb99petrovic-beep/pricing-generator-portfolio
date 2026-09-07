import sys
import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path


APPLICATION_ROOT = Path(__file__).resolve().parent.parent

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(APPLICATION_ROOT)
    )


from app.models.generated_voice_pricing_row import (
    GeneratedVoicePricingRow
)


class TestGeneratedVoicePricingRow(unittest.TestCase):

    def test_creates_outbound_only_row(self) -> None:
        row = GeneratedVoicePricingRow(
            country="Serbia",
            iso2="RS",
            landline_price=Decimal("0.10"),
            mobile_price=Decimal("0.20")
        )

        self.assertEqual(
            row.country,
            "Serbia"
        )

        self.assertEqual(
            row.iso2,
            "RS"
        )

        self.assertEqual(
            row.landline_price,
            Decimal("0.10")
        )

        self.assertEqual(
            row.mobile_price,
            Decimal("0.20")
        )

        self.assertIsNone(
            row.inbound_price
        )

    def test_creates_two_way_row(self) -> None:
        row = GeneratedVoicePricingRow(
            country="Serbia",
            iso2="RS",
            landline_price=Decimal("0.10"),
            mobile_price=Decimal("0.20"),
            inbound_price=Decimal("0.05")
        )

        self.assertEqual(
            row.inbound_price,
            Decimal("0.05")
        )

    def test_creates_blank_all_others_row(self) -> None:
        row = GeneratedVoicePricingRow(
            country="",
            iso2="",
            landline_price=Decimal("3"),
            mobile_price=Decimal("3")
        )

        self.assertEqual(
            row.country,
            ""
        )

        self.assertEqual(
            row.iso2,
            ""
        )

    def test_generated_voice_row_is_immutable(
        self
    ) -> None:
        row = GeneratedVoicePricingRow(
            country="Serbia",
            iso2="RS",
            landline_price=Decimal("0.10"),
            mobile_price=Decimal("0.20")
        )

        with self.assertRaises(
            FrozenInstanceError
        ):
            row.mobile_price = Decimal("0.30")


if __name__ == "__main__":
    unittest.main()