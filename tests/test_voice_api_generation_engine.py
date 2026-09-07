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


class TestVoiceApiGenerationEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = GenerationEngine()

        self.pricing_rows = [
            VoicePricingRow(
                country="All Others",
                iso2="",
                baseline_mobile_price=Decimal("3"),
                baseline_landline_price=Decimal("2"),
                baseline_inbound_price=Decimal("1"),
                enterprise_mobile_price=Decimal("2.5"),
                enterprise_landline_price=Decimal("1.5"),
                enterprise_inbound_price=Decimal("0.8"),
                number_type=""
            ),

            VoicePricingRow(
                country="Austria",
                iso2="AT",
                baseline_mobile_price=Decimal("0.20"),
                baseline_landline_price=Decimal("0.10"),
                baseline_inbound_price=Decimal("0.05"),
                enterprise_mobile_price=Decimal("0.18"),
                enterprise_landline_price=Decimal("0.09"),
                enterprise_inbound_price=Decimal("0.04"),
                number_type="US Cloud numbers"
            ),

            VoicePricingRow(
                country="Austria",
                iso2="AT",
                baseline_mobile_price=Decimal("0.30"),
                baseline_landline_price=Decimal("0.15"),
                baseline_inbound_price=Decimal("0.07"),
                enterprise_mobile_price=Decimal("0.27"),
                enterprise_landline_price=Decimal("0.13"),
                enterprise_inbound_price=Decimal("0.06"),
                number_type="Global Mobile Numbers"
            ),

            VoicePricingRow(
                country="Andorra",
                iso2="AD",
                baseline_mobile_price=Decimal("0.25"),
                baseline_landline_price=Decimal("0.04"),
                baseline_inbound_price=None,
                enterprise_mobile_price=Decimal("0.28"),
                enterprise_landline_price=Decimal("0.05"),
                enterprise_inbound_price=None,
                number_type="US Cloud numbers"
            )
        ]

    def test_selects_us_cloud_rows(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_api_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="ONE_WAY",
                number_type="US Cloud numbers"
            )
        )

        self.assertEqual(
            len(generated_rows),
            3
        )

        iso2_codes = [
            row.iso2
            for row in generated_rows
        ]

        self.assertEqual(
            iso2_codes,
            [
                "",
                "AT",
                "AD"
            ]
        )

    def test_selects_global_mobile_rows(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_api_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="ONE_WAY",
                number_type="Global Mobile Numbers"
            )
        )

        self.assertEqual(
            len(generated_rows),
            2
        )

        austria = generated_rows[1]

        self.assertEqual(
            austria.iso2,
            "AT"
        )

        self.assertEqual(
            austria.mobile_price,
            Decimal("0.30")
        )

        self.assertEqual(
            austria.landline_price,
            Decimal("0.15")
        )

    def test_one_way_removes_inbound_pricing(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_api_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="ONE_WAY",
                number_type="US Cloud numbers"
            )
        )

        for generated_row in generated_rows:
            self.assertIsNone(
                generated_row.inbound_price
            )

    def test_two_way_keeps_numeric_inbound(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_api_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="TWO_WAY",
                number_type="US Cloud numbers"
            )
        )

        austria = next(
            row
            for row in generated_rows
            if row.iso2 == "AT"
        )

        self.assertEqual(
            austria.inbound_price,
            Decimal("0.05")
        )

    def test_two_way_uses_all_others_inbound_fallback(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_api_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="TWO_WAY",
                number_type="US Cloud numbers"
            )
        )

        andorra = next(
            row
            for row in generated_rows
            if row.iso2 == "AD"
        )

        self.assertEqual(
            andorra.inbound_price,
            Decimal("1")
        )

    def test_enterprise_uses_enterprise_fallback(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_api_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Enterprise",
                traffic_type="TWO_WAY",
                number_type="US Cloud numbers"
            )
        )

        andorra = next(
            row
            for row in generated_rows
            if row.iso2 == "AD"
        )

        self.assertEqual(
            andorra.inbound_price,
            Decimal("0.8")
        )

        self.assertEqual(
            andorra.mobile_price,
            Decimal("0.28")
        )

        self.assertEqual(
            andorra.landline_price,
            Decimal("0.05")
        )

    def test_all_others_is_always_retained(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_api_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="ONE_WAY",
                number_type="Global Mobile Numbers"
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

    def test_number_type_matching_is_case_insensitive(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_api_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="ONE_WAY",
                number_type="global mobile numbers"
            )
        )

        self.assertEqual(
            len(generated_rows),
            2
        )

    def test_rejects_invalid_traffic_type(
        self
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            self.engine.generate_voice_api_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="THREE_WAY",
                number_type="US Cloud numbers"
            )

    def test_rejects_unknown_number_type(
        self
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            self.engine.generate_voice_api_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="ONE_WAY",
                number_type="Something Else"
            )

    def test_rejects_duplicate_iso2_within_selected_type(
        self
    ) -> None:
        pricing_rows = (
            self.pricing_rows
            + [
                VoicePricingRow(
                    country="Duplicate Austria",
                    iso2="AT",
                    baseline_mobile_price=Decimal("0.1"),
                    baseline_landline_price=Decimal("0.1"),
                    baseline_inbound_price=Decimal("0.1"),
                    enterprise_mobile_price=Decimal("0.1"),
                    enterprise_landline_price=Decimal("0.1"),
                    enterprise_inbound_price=Decimal("0.1"),
                    number_type="US Cloud numbers"
                )
            ]
        )

        with self.assertRaises(
            ValueError
        ):
            self.engine.generate_voice_api_rows(
                pricing_rows=pricing_rows,
                pricing_type="Baseline",
                traffic_type="TWO_WAY",
                number_type="US Cloud numbers"
            )


if __name__ == "__main__":
    unittest.main()