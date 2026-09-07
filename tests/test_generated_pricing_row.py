import sys
import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path


APPLICATION_ROOT = Path(__file__).resolve().parent.parent

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(0, str(APPLICATION_ROOT))


from app.models.generated_pricing_row import (
    GeneratedPricingRow
)


class TestGeneratedPricingRow(unittest.TestCase):
    """
    Tests the GeneratedPricingRow model.
    """

    def test_creates_generated_pricing_row(
        self
    ) -> None:
        """
        Confirms a generated row stores the final values.
        """

        generated_row = GeneratedPricingRow(
            country="Serbia",
            iso2="RS",
            price=Decimal("0.028")
        )

        self.assertEqual(
            generated_row.country,
            "Serbia"
        )

        self.assertEqual(
            generated_row.iso2,
            "RS"
        )

        self.assertEqual(
            generated_row.price,
            Decimal("0.028")
        )

    def test_generated_pricing_row_is_immutable(
        self
    ) -> None:
        """
        Confirms generated rows cannot be modified.
        """

        generated_row = GeneratedPricingRow(
            country="Serbia",
            iso2="RS",
            price=Decimal("0.028")
        )

        with self.assertRaises(
            FrozenInstanceError
        ):
            generated_row.price = Decimal("0.03")

    def test_creates_blank_all_others_row(
        self
    ) -> None:
        """
        Confirms the final All Others representation supports
        blank Country and ISO2 values.
        """

        generated_row = GeneratedPricingRow(
            country="",
            iso2="",
            price=Decimal("0.5")
        )

        self.assertEqual(
            generated_row.country,
            ""
        )

        self.assertEqual(
            generated_row.iso2,
            ""
        )

        self.assertEqual(
            generated_row.price,
            Decimal("0.5")
        )


if __name__ == "__main__":
    unittest.main()