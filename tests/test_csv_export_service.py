import csv
import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory


APPLICATION_ROOT = Path(__file__).resolve().parent.parent

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(0, str(APPLICATION_ROOT))


from app.models.generated_pricing_row import (
    GeneratedPricingRow
)
from app.models.generation_result import GenerationResult
from app.services.csv_export_service import (
    CsvExportService
)
from app.utils.path_resolver import PathResolver


class TestCsvExportService(unittest.TestCase):
    """
    Tests the CSV export service using a temporary directory.
    """

    def setUp(self) -> None:
        self.temporary_directory = (
            TemporaryDirectory()
        )

        self.output_directory = Path(
            self.temporary_directory.name
        )

        self.path_resolver = PathResolver(
            project_root=self.output_directory
        )

        self.output_settings = {
            "directory": "{project_root}/output",
            "filename_pattern": (
                "{currency} - {product} - "
                "template {MMM YYYY}.csv"
            ),
            "overwrite_existing_file": True,
            "encoding": "utf-8",
            "delimiter": ",",
            "quoting": "minimal"
        }

        self.output_csv_schema = {
            "band_definition_row": {
                "A": "Band1",
                "B": "Band2",
                "C": "Band3",
                "D": "Band4",
                "E": "Band5",
                "F": "Band6",
                "G": None,
                "H": None
            },
            "band_threshold_row": {
                "A": 0,
                "B": None,
                "C": None,
                "D": None,
                "E": None,
                "F": None,
                "G": None,
                "H": None
            },
            "column_header_row": {
                "A": "Country",
                "B": "ISO2",
                "C": "Band1",
                "D": "Band2",
                "E": "Band3",
                "F": "Band4",
                "G": "Band5",
                "H": "Band6"
            }
        }

        self.generation_result = GenerationResult(
            currency="USD",
            product_id="SMS",
            product_output_name="SMS",
            pricing_type="Baseline",
            rows=[
                GeneratedPricingRow(
                    country="",
                    iso2="",
                    price=Decimal("0.5")
                ),
                GeneratedPricingRow(
                    country="Laos",
                    iso2="LA",
                    price=Decimal("0.032")
                ),
                GeneratedPricingRow(
                    country="Serbia",
                    iso2="RS",
                    price=Decimal("0.028")
                )
            ]
        )

        self.export_service = CsvExportService(
            path_resolver=self.path_resolver,
            output_settings=self.output_settings,
            output_csv_schema=(
                self.output_csv_schema
            ),
            country_name_corrections={
                "Laos": "Lao"
            }
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_exports_csv_with_expected_filename(
        self
    ) -> None:
        output_path = self.export_service.export(
            generation_result=(
                self.generation_result
            ),
            generation_date=date(
                2026,
                8,
                5
            )
        )

        self.assertEqual(
            output_path.name,
            "USD - SMS - template Aug 2026.csv"
        )

        self.assertTrue(
            output_path.exists()
        )

    def test_exports_expected_csv_structure(
        self
    ) -> None:
        output_path = self.export_service.export(
            generation_result=(
                self.generation_result
            ),
            generation_date=date(
                2026,
                8,
                5
            )
        )

        with output_path.open(
            mode="r",
            encoding="utf-8",
            newline=""
        ) as csv_file:
            rows = list(
                csv.reader(
                    csv_file
                )
            )

        self.assertEqual(
            rows[0],
            [
                "Band1",
                "Band2",
                "Band3",
                "Band4",
                "Band5",
                "Band6"
            ]
        )

        self.assertEqual(
            len(rows[0]),
            6
        )

        self.assertEqual(
            rows[1],
            [
                "0",
                "",
                "",
                "",
                "",
                ""
            ]
        )

        self.assertEqual(
            len(rows[1]),
            6
        )

        self.assertEqual(
            rows[2],
            [
                "Country",
                "ISO2",
                "Band1",
                "Band2",
                "Band3",
                "Band4",
                "Band5",
                "Band6"
            ]
        )

        self.assertEqual(
            len(rows[2]),
            8
        )

        self.assertEqual(
            rows[3],
            [
                "",
                "",
                "0.5",
                "",
                "",
                "",
                "",
                ""
            ]
        )

        self.assertEqual(
            rows[4],
            [
                "Lao",
                "LA",
                "0.032",
                "",
                "",
                "",
                "",
                ""
            ]
        )

        self.assertEqual(
            rows[5],
            [
                "Serbia",
                "RS",
                "0.028",
                "",
                "",
                "",
                "",
                ""
            ]
        )

    def test_output_row_count_is_correct(
        self
    ) -> None:
        output_path = self.export_service.export(
            generation_result=(
                self.generation_result
            ),
            generation_date=date(
                2026,
                8,
                5
            )
        )

        with output_path.open(
            mode="r",
            encoding="utf-8",
            newline=""
        ) as csv_file:
            rows = list(
                csv.reader(
                    csv_file
                )
            )

        expected_row_count = (
            3
            + len(
                self.generation_result.rows
            )
        )

        self.assertEqual(
            len(rows),
            expected_row_count
        )

    def test_overwrites_existing_file_when_enabled(
        self
    ) -> None:
        output_path = self.export_service.export(
            generation_result=(
                self.generation_result
            ),
            generation_date=date(
                2026,
                8,
                5
            )
        )

        output_path.write_text(
            "old content",
            encoding="utf-8"
        )

        rewritten_path = self.export_service.export(
            generation_result=(
                self.generation_result
            ),
            generation_date=date(
                2026,
                8,
                5
            )
        )

        self.assertEqual(
            rewritten_path,
            output_path
        )

        self.assertNotEqual(
            rewritten_path.read_text(
                encoding="utf-8"
            ),
            "old content"
        )

    def test_rejects_existing_file_when_overwrite_disabled(
        self
    ) -> None:
        self.output_settings[
            "overwrite_existing_file"
        ] = False

        export_service = CsvExportService(
            path_resolver=self.path_resolver,
            output_settings=self.output_settings,
            output_csv_schema=(
                self.output_csv_schema
            )
        )

        export_service.export(
            generation_result=(
                self.generation_result
            ),
            generation_date=date(
                2026,
                8,
                5
            )
        )

        with self.assertRaises(
            FileExistsError
        ):
            export_service.export(
                generation_result=(
                    self.generation_result
                ),
                generation_date=date(
                    2026,
                    8,
                    5
                )
            )

    def test_rejects_missing_generated_rows(
        self
    ) -> None:
        empty_result = GenerationResult(
            currency="USD",
            product_id="SMS",
            product_output_name="SMS",
            pricing_type="Baseline",
            rows=[]
        )

        with self.assertRaises(
            ValueError
        ) as error_context:
            self.export_service.export(
                empty_result
            )

        self.assertEqual(
            str(error_context.exception),
            (
                "Generation result contains no "
                "pricing rows."
            )
        )

    def test_keeps_price_with_fewer_than_four_decimals(
        self
    ) -> None:
        """
        Confirms shorter prices are not padded with zeroes.
        """

        formatted_value = (
            CsvExportService._format_decimal(
                Decimal("0.5")
            )
        )

        self.assertEqual(
            formatted_value,
            "0.5"
        )

    def test_keeps_price_with_exactly_four_decimals(
        self
    ) -> None:
        """
        Confirms an exact four-decimal price is preserved.
        """

        formatted_value = (
            CsvExportService._format_decimal(
                Decimal("0.2236")
            )
        )

        self.assertEqual(
            formatted_value,
            "0.2236"
        )

    def test_rounds_price_up_to_four_decimals(
        self
    ) -> None:
        """
        Confirms a fifth decimal of five rounds upward.
        """

        formatted_value = (
            CsvExportService._format_decimal(
                Decimal("0.06225")
            )
        )

        self.assertEqual(
            formatted_value,
            "0.0623"
        )

    def test_rounds_price_down_to_four_decimals(
        self
    ) -> None:
        """
        Confirms a fifth decimal below five rounds downward.
        """

        formatted_value = (
            CsvExportService._format_decimal(
                Decimal("0.06224")
            )
        )

        self.assertEqual(
            formatted_value,
            "0.0622"
        )

    def test_removes_unnecessary_trailing_zeroes(
        self
    ) -> None:
        """
        Confirms rounded values do not retain unnecessary zeroes.
        """

        formatted_value = (
            CsvExportService._format_decimal(
                Decimal("0.0622000000")
            )
        )

        self.assertEqual(
            formatted_value,
            "0.0622"
        )

    def test_exported_csv_does_not_contain_utf8_bom(
        self
    ) -> None:
        """
        Confirms the CSV begins directly with the Band1 header
        rather than a UTF-8 byte-order mark.
        """

        output_path = self.export_service.export(
            generation_result=self.generation_result,
            generation_date=date(
                2026,
                8,
                6
            )
        )

        file_bytes = output_path.read_bytes()

        self.assertFalse(
            file_bytes.startswith(
                b"\xef\xbb\xbf"
            )
        )

        self.assertTrue(
            file_bytes.startswith(
                b"Band1,"
            )
        )

if __name__ == "__main__":
    unittest.main()