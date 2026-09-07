import sys
import unittest
from datetime import date
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


from app.models.generation_result import (
    GenerationResult
)

from app.services.csv_export_service import (
    CsvExportService
)


class TestCsvExportOptionalPricingType(
    unittest.TestCase
):

    def setUp(
        self
    ) -> None:

        self.export_service = (
            CsvExportService(
                path_resolver=Mock(),
                output_settings={
                    "directory": "unused",
                    "filename_pattern": (
                        "{currency} - {product} - "
                        "{pricing_type} - template "
                        "{MMM YYYY}.csv"
                    )
                },
                output_csv_schema={
                    "band_definition_row": {},
                    "band_threshold_row": {},
                    "column_header_row": {}
                },
                country_name_corrections={}
            )
        )

        self.test_date = date(
            2026,
            8,
            19
        )

    def test_filename_with_pricing_type_is_unchanged(
        self
    ) -> None:

        result = GenerationResult(
            currency="USD",
            product_id="SMS",
            product_output_name="SMS",
            pricing_type="Baseline",
            rows=[]
        )

        filename = (
            self.export_service
            ._build_filename(
                generation_result=result,
                generation_date=(
                    self.test_date
                )
            )
        )

        self.assertEqual(
            filename,
            (
                "USD - SMS - Baseline - "
                "template Aug 2026.csv"
            )
        )

    def test_filename_without_pricing_type_removes_segment(
        self
    ) -> None:

        result = GenerationResult(
            currency="USD",
            product_id=(
                "PHONE_ID_STANDARD"
            ),
            product_output_name=(
                "Phone ID Standard"
            ),
            pricing_type=None,
            rows=[]
        )

        filename = (
            self.export_service
            ._build_filename(
                generation_result=result,
                generation_date=(
                    self.test_date
                )
            )
        )

        self.assertEqual(
            filename,
            (
                "USD - Phone ID Standard - "
                "template Aug 2026.csv"
            )
        )

    def test_filename_without_pricing_type_never_contains_none(
        self
    ) -> None:

        result = GenerationResult(
            currency="USD",
            product_id=(
                "PHONE_ID_CONTACT"
            ),
            product_output_name=(
                "Phone ID Contact"
            ),
            pricing_type=None,
            rows=[]
        )

        filename = (
            self.export_service
            ._build_filename(
                generation_result=result,
                generation_date=(
                    self.test_date
                )
            )
        )

        self.assertNotIn(
            "None",
            filename
        )

        self.assertNotIn(
            "{pricing_type}",
            filename
        )


if __name__ == "__main__":
    unittest.main()