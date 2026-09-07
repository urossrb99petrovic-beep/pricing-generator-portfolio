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


class TestVoiceVerifyTtsGenerationEngine(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.engine = GenerationEngine()

        self.pricing_rows = [
            VoicePricingRow(
                country="All Others",
                iso2="",
                baseline_mobile_price=Decimal("3"),
                baseline_landline_price=Decimal("2.8"),
                baseline_inbound_price=None,
                enterprise_mobile_price=Decimal("2.7"),
                enterprise_landline_price=Decimal("2.5"),
                enterprise_inbound_price=None
            ),

            VoicePricingRow(
                country="Numeric Inbound",
                iso2="NI",
                baseline_mobile_price=Decimal("0.20"),
                baseline_landline_price=Decimal("0.10"),
                baseline_inbound_price=Decimal("0.05"),
                enterprise_mobile_price=Decimal("0.18"),
                enterprise_landline_price=Decimal("0.09"),
                enterprise_inbound_price=Decimal("0.04")
            ),

            VoicePricingRow(
                country="Unsupported Inbound",
                iso2="UI",
                baseline_mobile_price=Decimal("0.30"),
                baseline_landline_price=Decimal("0.15"),
                baseline_inbound_price=None,
                enterprise_mobile_price=Decimal("0.27"),
                enterprise_landline_price=Decimal("0.13"),
                enterprise_inbound_price=None
            )
        ]

    def test_one_way_selects_baseline_outbound(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_verify_tts_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="ONE_WAY"
            )
        )

        country = generated_rows[1]

        self.assertEqual(
            country.landline_price,
            Decimal("0.10")
        )

        self.assertEqual(
            country.mobile_price,
            Decimal("0.20")
        )

    def test_one_way_removes_all_inbound(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_verify_tts_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="ONE_WAY"
            )
        )

        for generated_row in generated_rows:
            self.assertIsNone(
                generated_row.inbound_price
            )

    def test_two_way_keeps_numeric_country_inbound(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_verify_tts_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="TWO_WAY"
            )
        )

        country = next(
            row
            for row in generated_rows
            if row.iso2 == "NI"
        )

        self.assertEqual(
            country.inbound_price,
            Decimal("0.05")
        )

    def test_all_others_inbound_falls_back_to_landline(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_verify_tts_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="TWO_WAY"
            )
        )

        all_others = generated_rows[0]

        self.assertEqual(
            all_others.landline_price,
            Decimal("2.8")
        )

        self.assertEqual(
            all_others.inbound_price,
            Decimal("2.8")
        )

    def test_country_missing_inbound_uses_effective_all_others(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_verify_tts_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="TWO_WAY"
            )
        )

        unsupported_country = next(
            row
            for row in generated_rows
            if row.iso2 == "UI"
        )

        self.assertEqual(
            unsupported_country.inbound_price,
            Decimal("2.8")
        )

    def test_enterprise_uses_enterprise_landline_fallback(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_verify_tts_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Enterprise",
                traffic_type="TWO_WAY"
            )
        )

        all_others = generated_rows[0]

        unsupported_country = next(
            row
            for row in generated_rows
            if row.iso2 == "UI"
        )

        self.assertEqual(
            all_others.inbound_price,
            Decimal("2.5")
        )

        self.assertEqual(
            unsupported_country.inbound_price,
            Decimal("2.5")
        )

        self.assertEqual(
            unsupported_country.landline_price,
            Decimal("0.13")
        )

        self.assertEqual(
            unsupported_country.mobile_price,
            Decimal("0.27")
        )

    def test_existing_all_others_inbound_would_take_priority(
        self
    ) -> None:
        pricing_rows = [
            VoicePricingRow(
                country="All Others",
                iso2="",
                baseline_mobile_price=Decimal("3"),
                baseline_landline_price=Decimal("2.8"),
                baseline_inbound_price=Decimal("1.2"),
                enterprise_mobile_price=Decimal("3"),
                enterprise_landline_price=Decimal("2.8"),
                enterprise_inbound_price=Decimal("1.1")
            ),
            VoicePricingRow(
                country="Country",
                iso2="CO",
                baseline_mobile_price=Decimal("0.2"),
                baseline_landline_price=Decimal("0.1"),
                baseline_inbound_price=None,
                enterprise_mobile_price=Decimal("0.2"),
                enterprise_landline_price=Decimal("0.1"),
                enterprise_inbound_price=None
            )
        ]

        generated_rows = (
            self.engine.generate_voice_verify_tts_rows(
                pricing_rows=pricing_rows,
                pricing_type="Baseline",
                traffic_type="TWO_WAY"
            )
        )

        self.assertEqual(
            generated_rows[0].inbound_price,
            Decimal("1.2")
        )

        self.assertEqual(
            generated_rows[1].inbound_price,
            Decimal("1.2")
        )

    def test_rejects_invalid_traffic_type(
        self
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            self.engine.generate_voice_verify_tts_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="THREE_WAY"
            )

    def test_rejects_empty_rows(
        self
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            self.engine.generate_voice_verify_tts_rows(
                pricing_rows=[],
                pricing_type="Baseline",
                traffic_type="ONE_WAY"
            )

    def test_rejects_missing_all_others(
        self
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            self.engine.generate_voice_verify_tts_rows(
                pricing_rows=self.pricing_rows[1:],
                pricing_type="Baseline",
                traffic_type="TWO_WAY"
            )


if __name__ == "__main__":
    unittest.main()