import sys
import unittest
from decimal import Decimal
from pathlib import Path


APPLICATION_ROOT = Path(__file__).resolve().parent.parent

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(0, str(APPLICATION_ROOT))


from app.models.generated_pricing_row import (
    GeneratedPricingRow
)
from app.models.generation_result import (
    GenerationResult
)


class TestGenerationResult(unittest.TestCase):
    """
    Tests the GenerationResult model.
    """

    def test_creates_generation_result(
        self
    ) -> None:
        result = GenerationResult(
            currency="USD",
            product_id="SMS",
            product_output_name="SMS",
            pricing_type="Baseline",
            rows=[
                GeneratedPricingRow(
                    country="Serbia",
                    iso2="RS",
                    price=Decimal("0.03")
                )
            ]
        )

        self.assertEqual(
            result.currency,
            "USD"
        )

        self.assertEqual(
            result.product_output_name,
            "SMS"
        )

        self.assertEqual(
            len(result.rows),
            1
        )


if __name__ == "__main__":
    unittest.main()