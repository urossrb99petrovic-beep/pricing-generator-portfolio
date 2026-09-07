import sys
import unittest
from decimal import Decimal
from pathlib import Path


APPLICATION_ROOT = Path(__file__).resolve().parent.parent

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(APPLICATION_ROOT)
    )


from app.models.voice_pricing_row import (
    VoicePricingRow
)
from app.services.generation_engine import (
    GenerationEngine
)


class TestTollFreeVoiceGenerationEngine(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.engine = GenerationEngine()

        self.pricing_rows = [
            VoicePricingRow(
                country="All Others",
                iso2="",
                baseline_mobile_price=Decimal("3"),
                baseline_landline_price=Decimal("3"),
                baseline_inbound_price=Decimal("3"),
                enterprise_mobile_price=Decimal("2.8"),
                enterprise_landline_price=Decimal("2.7"),
                enterprise_inbound_price=Decimal("2.6")
            ),
            VoicePricingRow(
                country="Albania",
                iso2="AL",
                baseline_mobile_price=Decimal("0.4505"),
                baseline_landline_price=Decimal("0.4665"),
                baseline_inbound_price=Decimal("0.2363"),
                enterprise_mobile_price=Decimal("0.5149"),
                enterprise_landline_price=Decimal("0.5332"),
                enterprise_inbound_price=Decimal("0.2954")
            )
        ]

    def test_generates_baseline_prices(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_toll_free_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline"
            )
        )

        albania = generated_rows[1]

        self.assertEqual(
            albania.mobile_price,
            Decimal("0.4505")
        )

        self.assertEqual(
            albania.landline_price,
            Decimal("0.4665")
        )

        self.assertEqual(
            albania.inbound_price,
            Decimal("0.2363")
        )

    def test_generates_enterprise_prices(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_toll_free_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Enterprise"
            )
        )

        albania = generated_rows[1]

        self.assertEqual(
            albania.mobile_price,
            Decimal("0.5149")
        )

        self.assertEqual(
            albania.landline_price,
            Decimal("0.5332")
        )

        self.assertEqual(
            albania.inbound_price,
            Decimal("0.2954")
        )

    def test_all_others_identity_is_blank(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_toll_free_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline"
            )
        )

        all_others = generated_rows[0]

        self.assertEqual(
            all_others.country,
            ""
        )

        self.assertEqual(
            all_others.iso2,
            ""
        )

        self.assertEqual(
            all_others.inbound_price,
            Decimal("3")
        )

    def test_rejects_missing_inbound(
        self
    ) -> None:
        pricing_rows = [
            VoicePricingRow(
                country="All Others",
                iso2="",
                baseline_mobile_price=Decimal("3"),
                baseline_landline_price=Decimal("3"),
                baseline_inbound_price=Decimal("3"),
                enterprise_mobile_price=Decimal("3"),
                enterprise_landline_price=Decimal("3"),
                enterprise_inbound_price=Decimal("3")
            ),
            VoicePricingRow(
                country="Broken Country",
                iso2="BC",
                baseline_mobile_price=Decimal("0.2"),
                baseline_landline_price=Decimal("0.1"),
                baseline_inbound_price=None,
                enterprise_mobile_price=Decimal("0.2"),
                enterprise_landline_price=Decimal("0.1"),
                enterprise_inbound_price=None
            )
        ]

        with self.assertRaises(
            ValueError
        ):
            self.engine.generate_toll_free_voice_rows(
                pricing_rows=pricing_rows,
                pricing_type="Baseline"
            )

    def test_rejects_empty_rows(
        self
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            self.engine.generate_toll_free_voice_rows(
                pricing_rows=[],
                pricing_type="Baseline"
            )


if __name__ == "__main__":
    unittest.main()