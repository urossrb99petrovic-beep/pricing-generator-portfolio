import sys
import unittest
from pathlib import Path


APPLICATION_ROOT = (
    Path(__file__).resolve().parent.parent
)

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(APPLICATION_ROOT)
    )


from app.models.generation_result import (
    GenerationResult
)


class TestOptionalPricingTypeOutput(
    unittest.TestCase
):

    def test_generation_result_accepts_none_pricing_type(
        self
    ) -> None:

        result = GenerationResult(
            currency="USD",
            product_id="PHONE_ID_LIVE_STATUS",
            product_output_name=(
                "Phone ID Live Status"
            ),
            pricing_type=None,
            rows=[]
        )

        self.assertIsNone(
            result.pricing_type
        )


if __name__ == "__main__":
    unittest.main()