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


from app.models.generated_voice_pricing_row import (
    GeneratedVoicePricingRow
)
from app.models.voice_pricing_row import (
    VoicePricingRow
)
from app.services.generation_engine import (
    GenerationEngine
)


class TestVoiceGenerationEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = GenerationEngine()

        self.pricing_rows = [
            VoicePricingRow(
                country="All Others",
                iso2="",
                baseline_mobile_price=Decimal("3"),
                baseline_landline_price=Decimal("2"),
                enterprise_mobile_price=Decimal("2.5"),
                enterprise_landline_price=Decimal("1.5")
            ),
            VoicePricingRow(
                country="Test Country",
                iso2="TC",
                baseline_mobile_price=Decimal("0.20"),
                baseline_landline_price=Decimal("0.10"),
                enterprise_mobile_price=Decimal("0.18"),
                enterprise_landline_price=Decimal("0.09")
            )
        ]

    def test_generates_baseline_voice_rows(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_base_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline"
            )
        )

        country_row = generated_rows[1]

        self.assertIsInstance(
            country_row,
            GeneratedVoicePricingRow
        )

        self.assertEqual(
            country_row.landline_price,
            Decimal("0.10")
        )

        self.assertEqual(
            country_row.mobile_price,
            Decimal("0.20")
        )

    def test_generates_enterprise_voice_rows(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_base_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Enterprise"
            )
        )

        country_row = generated_rows[1]

        self.assertEqual(
            country_row.landline_price,
            Decimal("0.09")
        )

        self.assertEqual(
            country_row.mobile_price,
            Decimal("0.18")
        )

    def test_all_others_identity_becomes_blank(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_base_rows(
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
            all_others.landline_price,
            Decimal("2")
        )

        self.assertEqual(
            all_others.mobile_price,
            Decimal("3")
        )

    def test_inbound_price_is_selected(
        self
    ) -> None:
        pricing_rows = [
            VoicePricingRow(
                country="Example",
                iso2="EX",
                baseline_mobile_price=Decimal("0.20"),
                baseline_landline_price=Decimal("0.10"),
                enterprise_mobile_price=Decimal("0.18"),
                enterprise_landline_price=Decimal("0.09"),
                baseline_inbound_price=Decimal("0.05"),
                enterprise_inbound_price=Decimal("0.04")
            )
        ]

        baseline_rows = (
            self.engine.generate_voice_base_rows(
                pricing_rows=pricing_rows,
                pricing_type="Baseline"
            )
        )

        enterprise_rows = (
            self.engine.generate_voice_base_rows(
                pricing_rows=pricing_rows,
                pricing_type="Enterprise"
            )
        )

        self.assertEqual(
            baseline_rows[0].inbound_price,
            Decimal("0.05")
        )

        self.assertEqual(
            enterprise_rows[0].inbound_price,
            Decimal("0.04")
        )

    def test_none_inbound_is_preserved(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_base_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline"
            )
        )

        self.assertIsNone(
            generated_rows[1].inbound_price
        )

    def test_voice_row_order_is_preserved(
        self
    ) -> None:
        generated_rows = (
            self.engine.generate_voice_base_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Baseline"
            )
        )

        self.assertEqual(
            generated_rows[0].country,
            ""
        )

        self.assertEqual(
            generated_rows[1].country,
            "Test Country"
        )

    def test_rejects_empty_voice_rows(
        self
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            self.engine.generate_voice_base_rows(
                pricing_rows=[],
                pricing_type="Baseline"
            )

    def test_rejects_invalid_pricing_type(
        self
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            self.engine.generate_voice_base_rows(
                pricing_rows=self.pricing_rows,
                pricing_type="Something Else"
            )


if __name__ == "__main__":
    unittest.main()