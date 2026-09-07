import sys
import unittest
from decimal import Decimal
from pathlib import Path


APPLICATION_ROOT = (
    Path(__file__).resolve().parent.parent
)

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(APPLICATION_ROOT)
    )


from app.models.phone_id_live_status_pricing_data import (
    PhoneIdLiveStatusPricingData
)

from app.models.phone_id_live_status_pricing_row import (
    PhoneIdLiveStatusPricingRow
)

from app.models.generated_voice_pricing_row import (
    GeneratedVoicePricingRow
)

from app.services.generation_engine import (
    GenerationEngine
)


class TestPhoneIdLiveStatusGenerationEngine(
    unittest.TestCase
):

    def setUp(
        self
    ) -> None:

        self.engine = (
            GenerationEngine()
        )

        self.pricing_data = (
            PhoneIdLiveStatusPricingData(
                all_other=(
                    PhoneIdLiveStatusPricingRow(
                        country=(
                            "All Other Countries"
                        ),
                        iso2="",
                        mobile_price=(
                            Decimal("0.1")
                        ),
                        landline_price=(
                            Decimal("0.1")
                        )
                    )
                ),
                countries=[
                    PhoneIdLiveStatusPricingRow(
                        country=(
                            "United States"
                        ),
                        iso2="US",
                        mobile_price=(
                            Decimal("0.0022")
                        ),
                        landline_price=(
                            Decimal("0.038")
                        )
                    ),
                    PhoneIdLiveStatusPricingRow(
                        country="Canada",
                        iso2="CA",
                        mobile_price=(
                            Decimal("0.01")
                        ),
                        landline_price=(
                            Decimal("0.02")
                        )
                    )
                ]
            )
        )

    def test_generation_returns_voice_rows(
        self
    ) -> None:

        rows = (
            self.engine
            .generate_phone_id_live_status_pricing(
                pricing_data=(
                    self.pricing_data
                )
            )
        )

        self.assertTrue(
            all(
                isinstance(
                    row,
                    GeneratedVoicePricingRow
                )
                for row in rows
            )
        )

    def test_all_other_is_first_and_blank(
        self
    ) -> None:

        rows = (
            self.engine
            .generate_phone_id_live_status_pricing(
                pricing_data=(
                    self.pricing_data
                )
            )
        )

        all_other = rows[0]

        self.assertEqual(
            all_other.country,
            ""
        )

        self.assertEqual(
            all_other.iso2,
            ""
        )

        self.assertEqual(
            all_other.mobile_price,
            Decimal("0.1")
        )

        self.assertEqual(
            all_other.landline_price,
            Decimal("0.1")
        )

    def test_country_prices_are_preserved(
        self
    ) -> None:

        rows = (
            self.engine
            .generate_phone_id_live_status_pricing(
                pricing_data=(
                    self.pricing_data
                )
            )
        )

        united_states = next(
            row
            for row in rows
            if row.iso2 == "US"
        )

        self.assertEqual(
            united_states.mobile_price,
            Decimal("0.0022")
        )

        self.assertEqual(
            united_states.landline_price,
            Decimal("0.038")
        )

    def test_inbound_price_is_none(
        self
    ) -> None:

        rows = (
            self.engine
            .generate_phone_id_live_status_pricing(
                pricing_data=(
                    self.pricing_data
                )
            )
        )

        self.assertTrue(
            all(
                row.inbound_price is None
                for row in rows
            )
        )

    def test_row_count_is_all_other_plus_countries(
        self
    ) -> None:

        rows = (
            self.engine
            .generate_phone_id_live_status_pricing(
                pricing_data=(
                    self.pricing_data
                )
            )
        )

        self.assertEqual(
            len(rows),
            3
        )


if __name__ == "__main__":
    unittest.main()