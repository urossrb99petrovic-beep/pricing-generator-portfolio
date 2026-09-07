import sys
import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path


APPLICATION_ROOT = Path(__file__).resolve().parent.parent

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(0, str(APPLICATION_ROOT))


from app.models.pricing_row import PricingRow


class TestPricingRow(unittest.TestCase):
    """
    Tests the PricingRow business model.
    """

    def test_creates_pricing_row(
        self
    ) -> None:
        """
        Confirms that a PricingRow stores all supplied values.
        """

        pricing_row = PricingRow(
            country="Serbia",
            iso2="RS",
            baseline_price=Decimal("0.032"),
            enterprise_price=Decimal("0.028")
        )

        self.assertEqual(
            pricing_row.country,
            "Serbia"
        )

        self.assertEqual(
            pricing_row.iso2,
            "RS"
        )

        self.assertEqual(
            pricing_row.baseline_price,
            Decimal("0.032")
        )

        self.assertEqual(
            pricing_row.enterprise_price,
            Decimal("0.028")
        )

    def test_pricing_row_is_immutable(
        self
    ) -> None:
        """
        Confirms that extracted pricing rows cannot be modified.
        """

        pricing_row = PricingRow(
            country="Serbia",
            iso2="RS",
            baseline_price=Decimal("0.032"),
            enterprise_price=Decimal("0.028")
        )

        with self.assertRaises(
            FrozenInstanceError
        ):
            pricing_row.country = "Croatia"


if __name__ == "__main__":
    unittest.main()