from decimal import Decimal
import unittest

from app.models.pricing_row import PricingRow
from app.models.sender_override_price import SenderOverridePrice
from app.services.generation_engine import GenerationEngine


class GenerationEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = GenerationEngine()
        self.base_rows = [
            PricingRow("Exampleland", "EX", Decimal("0.10"), Decimal("0.08")),
            PricingRow("United States", "US", Decimal("0.12"), Decimal("0.09")),
            PricingRow("All Others", "", Decimal("0.20"), Decimal("0.18")),
        ]

    def test_selects_requested_base_price_and_normalizes_all_others(self) -> None:
        rows = self.engine.generate_base_rows(self.base_rows, "Enterprise")

        self.assertEqual(rows[0].price, Decimal("0.08"))
        self.assertEqual(rows[1].price, Decimal("0.09"))
        self.assertEqual(rows[2].country, "")
        self.assertEqual(rows[2].iso2, "")

    def test_non_default_sender_price_replaces_matching_country(self) -> None:
        rows = self.engine.generate_pricing(
            base_pricing_rows=self.base_rows,
            pricing_type="Baseline",
            selected_sender_ids={"US": "10DLC"},
            sender_override_prices={
                "US": SenderOverridePrice(
                    lookup_value="Synthetic 10DLC",
                    baseline_price=Decimal("0.15"),
                    enterprise_price=Decimal("0.11"),
                )
            },
        )

        us_row = next(row for row in rows if row.iso2 == "US")
        self.assertEqual(us_row.price, Decimal("0.15"))

    def test_unsupported_pricing_type_fails_explicitly(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.generate_base_rows(self.base_rows, "Unknown")


if __name__ == "__main__":
    unittest.main()
