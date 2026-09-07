import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


APPLICATION_ROOT = (
    Path(__file__).resolve().parent.parent
)

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(APPLICATION_ROOT)
    )


from app.models.generation_request import (
    GenerationRequest
)
from app.services.generation_engine import (
    GenerationEngine
)
from app.services.pricing_generation_service import (
    PricingGenerationService
)


class TestOptionalPricingType(
    unittest.TestCase
):

    def setUp(
        self
    ) -> None:

        self.service = (
            PricingGenerationService(
                pricing_data_service=Mock(),
                generation_engine=(
                    GenerationEngine()
                ),
                sender_overrides_config={
                    "countries": {}
                }
            )
        )

        self.single_pricing_product = {
            "product_id": (
                "PHONE_ID_LIVE_STATUS"
            ),
            "supported_pricing_types": []
        }

        self.standard_pricing_product = {
            "product_id": "SMS",
            "supported_pricing_types": [
                "Baseline",
                "Enterprise"
            ]
        }

    def test_generation_request_accepts_none(
        self
    ) -> None:

        request = GenerationRequest(
            currency="USD",
            product_id=(
                "PHONE_ID_LIVE_STATUS"
            ),
            pricing_type=None
        )

        self.assertIsNone(
            request.pricing_type
        )

    def test_single_pricing_accepts_none(
        self
    ) -> None:

        self.service._validate_product_pricing_type(
            product_config=(
                self.single_pricing_product
            ),
            pricing_type=None
        )

    def test_single_pricing_accepts_blank_as_missing(
        self
    ) -> None:

        self.service._validate_product_pricing_type(
            product_config=(
                self.single_pricing_product
            ),
            pricing_type="   "
        )

    def test_single_pricing_rejects_baseline(
        self
    ) -> None:

        with self.assertRaises(
            ValueError
        ) as error_context:

            self.service._validate_product_pricing_type(
                product_config=(
                    self.single_pricing_product
                ),
                pricing_type="Baseline"
            )

        self.assertIn(
            "does not support a Pricing Type",
            str(
                error_context.exception
            )
        )

    def test_standard_product_requires_pricing_type(
        self
    ) -> None:

        with self.assertRaises(
            ValueError
        ) as error_context:

            self.service._validate_product_pricing_type(
                product_config=(
                    self.standard_pricing_product
                ),
                pricing_type=None
            )

        self.assertIn(
            "requires a Pricing Type",
            str(
                error_context.exception
            )
        )

    def test_standard_product_accepts_baseline(
        self
    ) -> None:

        self.service._validate_product_pricing_type(
            product_config=(
                self.standard_pricing_product
            ),
            pricing_type="Baseline"
        )

    def test_standard_product_rejects_unknown_type(
        self
    ) -> None:

        with self.assertRaises(
            ValueError
        ):

            self.service._validate_product_pricing_type(
                product_config=(
                    self.standard_pricing_product
                ),
                pricing_type="Something Else"
            )


if __name__ == "__main__":
    unittest.main()