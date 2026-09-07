import sys
import unittest
from pathlib import Path


APPLICATION_ROOT = Path(__file__).resolve().parent.parent

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(0, str(APPLICATION_ROOT))


from app.models.generation_request import (
    GenerationRequest
)


class TestGenerationRequest(unittest.TestCase):
    """
    Tests the GenerationRequest model.
    """

    def test_creates_generation_request(
        self
    ) -> None:
        request = GenerationRequest(
            currency="USD",
            product_id="LOCAL_SMS",
            pricing_type="Baseline",
            sender_ids={
                "US": "10DLC"
            },
            local_countries=[
                "Serbia"
            ]
        )

        self.assertEqual(
            request.currency,
            "USD"
        )

        self.assertEqual(
            request.product_id,
            "LOCAL_SMS"
        )

        self.assertEqual(
            request.sender_ids["US"],
            "10DLC"
        )

        self.assertEqual(
            request.local_countries,
            ["Serbia"]
        )

    def test_creates_separate_mutable_defaults(
        self
    ) -> None:
        first_request = GenerationRequest(
            currency="USD",
            product_id="SMS_MARKETING",
            pricing_type="Baseline"
        )

        second_request = GenerationRequest(
            currency="EUR",
            product_id="SMS_MARKETING",
            pricing_type="Enterprise"
        )

        self.assertIsNot(
            first_request.sender_ids,
            second_request.sender_ids
        )

        self.assertIsNot(
            first_request.local_countries,
            second_request.local_countries
        )


if __name__ == "__main__":
    unittest.main()