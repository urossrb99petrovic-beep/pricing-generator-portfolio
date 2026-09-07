import sys
import unittest
from pathlib import Path

APPLICATION_ROOT = Path(__file__).resolve().parent.parent

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(0, str(APPLICATION_ROOT))

from app.models.generation_request import GenerationRequest


class TestGenerationRequestProductOptions(unittest.TestCase):

    def test_product_options_are_empty_by_default(self) -> None:
        request = GenerationRequest(
            currency="USD",
            product_id="SMS",
            pricing_type="Baseline"
        )

        self.assertEqual(request.product_options, {})

    def test_voice_verify_can_store_billing_type(self) -> None:
        request = GenerationRequest(
            currency="USD",
            product_id="VOICE_VERIFY",
            pricing_type="Baseline",
            product_options={
                "billing_type": "PER_TRANSACTION"
            }
        )

        self.assertEqual(
            request.product_options["billing_type"],
            "PER_TRANSACTION"
        )

    def test_voice_can_store_multiple_product_options(self) -> None:
        request = GenerationRequest(
            currency="USD",
            product_id="VOICE",
            pricing_type="Enterprise",
            product_options={
                "traffic_type": "TWO_WAY",
                "number_type": "GLOBAL_MOBILE_NUMBERS"
            }
        )

        self.assertEqual(
            request.product_options["traffic_type"],
            "TWO_WAY"
        )

        self.assertEqual(
            request.product_options["number_type"],
            "GLOBAL_MOBILE_NUMBERS"
        )

    def test_existing_sms_fields_still_work(self) -> None:
        request = GenerationRequest(
            currency="EUR",
            product_id="SMS",
            pricing_type="Enterprise",
            sender_ids={
                "US": "10DLC",
                "CA": "DSC"
            },
            local_countries=[
                "Serbia"
            ]
        )

        self.assertEqual(
            request.sender_ids,
            {
                "US": "10DLC",
                "CA": "DSC"
            }
        )

        self.assertEqual(
            request.local_countries,
            ["Serbia"]
        )

        self.assertEqual(
            request.product_options,
            {}
        )

    def test_product_options_are_not_shared_between_requests(self) -> None:
        first_request = GenerationRequest(
            currency="USD",
            product_id="VOICE",
            pricing_type="Baseline"
        )

        second_request = GenerationRequest(
            currency="USD",
            product_id="VOICE",
            pricing_type="Baseline"
        )

        first_request.product_options["traffic_type"] = "ONE_WAY"

        self.assertEqual(
            first_request.product_options,
            {
                "traffic_type": "ONE_WAY"
            }
        )

        self.assertEqual(
            second_request.product_options,
            {}
        )


if __name__ == "__main__":
    unittest.main()