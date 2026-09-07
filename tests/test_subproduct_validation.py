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


class TestSubproductValidation(
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

        self.phone_id_suite = {
            "product_id": (
                "PHONE_ID_SUITE"
            ),
            "subproducts": [
                {
                    "product_id": (
                        "PHONE_ID_STANDARD"
                    ),
                    "required": True
                },
                {
                    "product_id": (
                        "PHONE_ID_CONTACT"
                    ),
                    "required": False
                },
                {
                    "product_id": (
                        "PHONE_ID_SIM_SWAP"
                    ),
                    "required": False
                }
            ]
        }

        self.sms_product = {
            "product_id": "SMS"
        }

    def test_generation_request_defaults_to_no_subproducts(
        self
    ) -> None:

        request = GenerationRequest(
            currency="USD",
            product_id="SMS",
            pricing_type="Baseline"
        )

        self.assertEqual(
            request.selected_subproducts,
            []
        )

    def test_phone_id_standard_only_is_valid(
        self
    ) -> None:

        self.service._validate_selected_subproducts(
            product_config=(
                self.phone_id_suite
            ),
            selected_subproducts=[
                "PHONE_ID_STANDARD"
            ]
        )

    def test_phone_id_standard_plus_optional_is_valid(
        self
    ) -> None:

        self.service._validate_selected_subproducts(
            product_config=(
                self.phone_id_suite
            ),
            selected_subproducts=[
                "PHONE_ID_STANDARD",
                "PHONE_ID_CONTACT",
                "PHONE_ID_SIM_SWAP"
            ]
        )

    def test_phone_id_standard_cannot_be_missing(
        self
    ) -> None:

        with self.assertRaises(
            ValueError
        ) as error_context:

            self.service._validate_selected_subproducts(
                product_config=(
                    self.phone_id_suite
                ),
                selected_subproducts=[
                    "PHONE_ID_CONTACT"
                ]
            )

        self.assertIn(
            "PHONE_ID_STANDARD",
            str(
                error_context.exception
            )
        )

    def test_empty_phone_id_selection_is_invalid(
        self
    ) -> None:

        with self.assertRaises(
            ValueError
        ):

            self.service._validate_selected_subproducts(
                product_config=(
                    self.phone_id_suite
                ),
                selected_subproducts=[]
            )

    def test_unknown_subproduct_is_rejected(
        self
    ) -> None:

        with self.assertRaises(
            ValueError
        ) as error_context:

            self.service._validate_selected_subproducts(
                product_config=(
                    self.phone_id_suite
                ),
                selected_subproducts=[
                    "PHONE_ID_STANDARD",
                    "NOT_A_REAL_PRODUCT"
                ]
            )

        self.assertIn(
            "NOT_A_REAL_PRODUCT",
            str(
                error_context.exception
            )
        )

    def test_duplicate_subproduct_is_rejected(
        self
    ) -> None:

        with self.assertRaises(
            ValueError
        ):

            self.service._validate_selected_subproducts(
                product_config=(
                    self.phone_id_suite
                ),
                selected_subproducts=[
                    "PHONE_ID_STANDARD",
                    "PHONE_ID_CONTACT",
                    "PHONE_ID_CONTACT"
                ]
            )

    def test_normal_product_accepts_empty_selection(
        self
    ) -> None:

        self.service._validate_selected_subproducts(
            product_config=(
                self.sms_product
            ),
            selected_subproducts=[]
        )

    def test_normal_product_rejects_subproduct_selection(
        self
    ) -> None:

        with self.assertRaises(
            ValueError
        ) as error_context:

            self.service._validate_selected_subproducts(
                product_config=(
                    self.sms_product
                ),
                selected_subproducts=[
                    "PHONE_ID_STANDARD"
                ]
            )

        self.assertIn(
            "does not support subproduct selections",
            str(
                error_context.exception
            )
        )


if __name__ == "__main__":
    unittest.main()