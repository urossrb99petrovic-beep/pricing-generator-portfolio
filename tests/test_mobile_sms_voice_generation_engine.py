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


from app.models.generated_mobile_pricing import (
    GeneratedMobilePricing
)
from app.models.mobile_pricing_row import (
    MobilePricingRow
)
from app.services.generation_engine import (
    GenerationEngine
)


class TestMobileSmsVoiceGenerationEngine(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.engine = GenerationEngine()

        self.pricing_rows = [
            # All Others
            MobilePricingRow(
                country="",
                iso2="",
                baseline_sms_outbound_price=Decimal("0.5"),
                baseline_sms_inbound_price=Decimal("0.6"),
                baseline_voice_outbound_price=Decimal("3"),
                baseline_voice_inbound_price=Decimal("2.8"),
                enterprise_sms_outbound_price=Decimal("0.7"),
                enterprise_sms_inbound_price=Decimal("0.8"),
                enterprise_voice_outbound_price=Decimal("2.7"),
                enterprise_voice_inbound_price=Decimal("2.6")
            ),

            # SMS only
            MobilePricingRow(
                country="SMS Only",
                iso2="SO",
                baseline_sms_outbound_price=Decimal("0.10"),
                baseline_sms_inbound_price=Decimal("0.11"),
                baseline_voice_outbound_price=None,
                baseline_voice_inbound_price=None,
                enterprise_sms_outbound_price=Decimal("0.12"),
                enterprise_sms_inbound_price=Decimal("0.13"),
                enterprise_voice_outbound_price=None,
                enterprise_voice_inbound_price=None
            ),

            # Voice only
            MobilePricingRow(
                country="Voice Only",
                iso2="VO",
                baseline_sms_outbound_price=None,
                baseline_sms_inbound_price=None,
                baseline_voice_outbound_price=Decimal("0.20"),
                baseline_voice_inbound_price=Decimal("0.21"),
                enterprise_sms_outbound_price=None,
                enterprise_sms_inbound_price=None,
                enterprise_voice_outbound_price=Decimal("0.22"),
                enterprise_voice_inbound_price=Decimal("0.23")
            ),

            # Voice outbound exists, inbound unsupported.
            MobilePricingRow(
                country="Partial Voice",
                iso2="PV",
                baseline_sms_outbound_price=Decimal("0.30"),
                baseline_sms_inbound_price=None,
                baseline_voice_outbound_price=Decimal("0.31"),
                baseline_voice_inbound_price=None,
                enterprise_sms_outbound_price=Decimal("0.32"),
                enterprise_sms_inbound_price=None,
                enterprise_voice_outbound_price=Decimal("0.33"),
                enterprise_voice_inbound_price=None
            ),

            # SMS inbound exists but outbound unsupported.
            MobilePricingRow(
                country="Inbound SMS Only",
                iso2="IO",
                baseline_sms_outbound_price=None,
                baseline_sms_inbound_price=Decimal("0.40"),
                baseline_voice_outbound_price=None,
                baseline_voice_inbound_price=None,
                enterprise_sms_outbound_price=None,
                enterprise_sms_inbound_price=Decimal("0.41"),
                enterprise_voice_outbound_price=None,
                enterprise_voice_inbound_price=None
            ),

            # Everything supported.
            MobilePricingRow(
                country="All Supported",
                iso2="AS",
                baseline_sms_outbound_price=Decimal("0.50"),
                baseline_sms_inbound_price=Decimal("0.51"),
                baseline_voice_outbound_price=Decimal("0.52"),
                baseline_voice_inbound_price=Decimal("0.53"),
                enterprise_sms_outbound_price=Decimal("0.60"),
                enterprise_sms_inbound_price=Decimal("0.61"),
                enterprise_voice_outbound_price=Decimal("0.62"),
                enterprise_voice_inbound_price=Decimal("0.63")
            )
        ]

    def test_one_way_returns_mobile_result(
        self
    ) -> None:
        result = (
            self.engine.generate_mobile_sms_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="ONE_WAY"
            )
        )

        self.assertIsInstance(
            result,
            GeneratedMobilePricing
        )

        self.assertIsNone(
            result.sms_inbound_rows
        )

    def test_one_way_sms_filters_unsupported_countries(
        self
    ) -> None:
        result = (
            self.engine.generate_mobile_sms_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="ONE_WAY"
            )
        )

        iso2_codes = [
            row.iso2
            for row in result.sms_outbound_rows
        ]

        self.assertEqual(
            iso2_codes,
            [
                "",
                "SO",
                "PV",
                "AS"
            ]
        )

        self.assertNotIn(
            "VO",
            iso2_codes
        )

    def test_one_way_voice_filters_independently(
        self
    ) -> None:
        result = (
            self.engine.generate_mobile_sms_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="ONE_WAY"
            )
        )

        iso2_codes = [
            row.iso2
            for row in result.voice_rows
        ]

        self.assertEqual(
            iso2_codes,
            [
                "",
                "VO",
                "PV",
                "AS"
            ]
        )

        self.assertNotIn(
            "SO",
            iso2_codes
        )

    def test_one_way_voice_duplicates_outbound_into_landline_and_mobile(
        self
    ) -> None:
        result = (
            self.engine.generate_mobile_sms_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="ONE_WAY"
            )
        )

        voice_only = next(
            row
            for row in result.voice_rows
            if row.iso2 == "VO"
        )

        self.assertEqual(
            voice_only.landline_price,
            Decimal("0.20")
        )

        self.assertEqual(
            voice_only.mobile_price,
            Decimal("0.20")
        )

        self.assertIsNone(
            voice_only.inbound_price
        )

    def test_two_way_creates_sms_inbound_output(
        self
    ) -> None:
        result = (
            self.engine.generate_mobile_sms_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="TWO_WAY"
            )
        )

        self.assertIsNotNone(
            result.sms_inbound_rows
        )

        iso2_codes = [
            row.iso2
            for row in result.sms_inbound_rows
        ]

        self.assertEqual(
            iso2_codes,
            [
                "",
                "SO",
                "IO",
                "AS"
            ]
        )

    def test_sms_outbound_and_inbound_filter_independently(
        self
    ) -> None:
        result = (
            self.engine.generate_mobile_sms_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="TWO_WAY"
            )
        )

        outbound_iso2 = {
            row.iso2
            for row in result.sms_outbound_rows
        }

        inbound_iso2 = {
            row.iso2
            for row in result.sms_inbound_rows
        }

        self.assertIn(
            "PV",
            outbound_iso2
        )

        self.assertNotIn(
            "PV",
            inbound_iso2
        )

        self.assertNotIn(
            "IO",
            outbound_iso2
        )

        self.assertIn(
            "IO",
            inbound_iso2
        )

    def test_two_way_voice_requires_both_voice_prices(
        self
    ) -> None:
        result = (
            self.engine.generate_mobile_sms_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="TWO_WAY"
            )
        )

        iso2_codes = [
            row.iso2
            for row in result.voice_rows
        ]

        self.assertEqual(
            iso2_codes,
            [
                "",
                "VO",
                "AS"
            ]
        )

        # PV has Voice Outbound but no Voice Inbound.
        self.assertNotIn(
            "PV",
            iso2_codes
        )

    def test_mobile_does_not_apply_all_others_fallback(
        self
    ) -> None:
        result = (
            self.engine.generate_mobile_sms_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="TWO_WAY"
            )
        )

        voice_iso2_codes = {
            row.iso2
            for row in result.voice_rows
        }

        # If a fallback had incorrectly been applied,
        # Partial Voice would appear here with inbound 2.8.
        self.assertNotIn(
            "PV",
            voice_iso2_codes
        )

    def test_enterprise_prices_are_selected(
        self
    ) -> None:
        result = (
            self.engine.generate_mobile_sms_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Enterprise",
                traffic_type="TWO_WAY"
            )
        )

        all_supported_sms = next(
            row
            for row in result.sms_outbound_rows
            if row.iso2 == "AS"
        )

        all_supported_voice = next(
            row
            for row in result.voice_rows
            if row.iso2 == "AS"
        )

        self.assertEqual(
            all_supported_sms.price,
            Decimal("0.60")
        )

        self.assertEqual(
            all_supported_voice.landline_price,
            Decimal("0.62")
        )

        self.assertEqual(
            all_supported_voice.mobile_price,
            Decimal("0.62")
        )

        self.assertEqual(
            all_supported_voice.inbound_price,
            Decimal("0.63")
        )

    def test_all_others_uses_source_prices(
        self
    ) -> None:
        result = (
            self.engine.generate_mobile_sms_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="TWO_WAY"
            )
        )

        sms_outbound = (
            result.sms_outbound_rows[0]
        )

        sms_inbound = (
            result.sms_inbound_rows[0]
        )

        voice = (
            result.voice_rows[0]
        )

        self.assertEqual(
            sms_outbound.price,
            Decimal("0.5")
        )

        self.assertEqual(
            sms_inbound.price,
            Decimal("0.6")
        )

        self.assertEqual(
            voice.landline_price,
            Decimal("3")
        )

        self.assertEqual(
            voice.mobile_price,
            Decimal("3")
        )

        self.assertEqual(
            voice.inbound_price,
            Decimal("2.8")
        )

    def test_rejects_invalid_traffic_type(
        self
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            self.engine.generate_mobile_sms_voice_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline",
                traffic_type="THREE_WAY"
            )

    def test_rejects_missing_all_others(
        self
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            self.engine.generate_mobile_sms_voice_rows(
                pricing_rows=self.pricing_rows[1:],
                pricing_type="Baseline",
                traffic_type="TWO_WAY"
            )


if __name__ == "__main__":
    unittest.main()