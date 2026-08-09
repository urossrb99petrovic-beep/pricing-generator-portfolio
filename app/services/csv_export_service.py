import csv
import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from app.models.generation_result import GenerationResult
from app.models.generated_pricing_row import (
    GeneratedPricingRow
)
from app.utils.path_resolver import PathResolver


class CsvExportService:
    """
    Converts generated pricing rows into the configured CSV
    template and saves the file.
    """

    INVALID_FILENAME_CHARACTERS = re.compile(
        r'[<>:"/\\|?*]'
    )

    def __init__(
        self,
        path_resolver: PathResolver,
        output_settings: dict[str, Any],
        output_csv_schema: dict[str, Any],
        country_name_corrections: dict[str, str]
        | None = None
    ) -> None:
        """
        Creates the CSV export service.

        Args:
            path_resolver:
                Resolves the configured output directory.

            output_settings:
                Output configuration loaded from settings.json.

            output_csv_schema:
                CSV layout configuration loaded from
                schemas.json.

            country_name_corrections:
                Optional source-to-output country name mapping
                loaded from countries.json.
        """

        if not output_settings:
            raise ValueError(
                "Output settings cannot be empty."
            )

        if not output_csv_schema:
            raise ValueError(
                "Output CSV schema cannot be empty."
            )

        self._path_resolver = path_resolver
        self._output_settings = output_settings
        self._output_csv_schema = output_csv_schema

        self._country_name_corrections = (
            country_name_corrections or {}
        )

    def export(
        self,
        generation_result: GenerationResult,
        generation_date: date | None = None
    ) -> Path:
        """
        Writes one completed pricing generation to CSV.

        Args:
            generation_result:
                Final generated pricing data.

            generation_date:
                Date used in the output filename. Defaults to
                today's date. A supplied date makes testing
                deterministic.

        Returns:
            Absolute path of the written CSV file.

        Raises:
            ValueError:
                If generation data or configuration is invalid.

            FileExistsError:
                If the target exists and overwriting is disabled.
        """

        self._validate_generation_result(
            generation_result
        )

        effective_date = (
            generation_date or date.today()
        )

        output_directory = (
            self._resolve_output_directory()
        )

        output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        output_filename = self._build_filename(
            generation_result=generation_result,
            generation_date=effective_date
        )

        output_path = (
            output_directory / output_filename
        )

        overwrite_existing_file = bool(
            self._output_settings.get(
                "overwrite_existing_file",
                False
            )
        )

        if (
            output_path.exists()
            and not overwrite_existing_file
        ):
            raise FileExistsError(
                f"Output CSV already exists: "
                f"{output_path}"
            )

        csv_rows = self._build_csv_rows(
            generation_result.rows
        )

        encoding = str(
            self._output_settings.get(
                "encoding",
                "utf-8-sig"
            )
        )

        delimiter = str(
            self._output_settings.get(
                "delimiter",
                ","
            )
        )

        if len(delimiter) != 1:
            raise ValueError(
                "CSV delimiter must contain exactly "
                "one character."
            )

        quoting = self._resolve_quoting()

        with output_path.open(
            mode="w",
            encoding=encoding,
            newline=""
        ) as output_file:
            writer = csv.writer(
                output_file,
                delimiter=delimiter,
                quoting=quoting,
                lineterminator="\n"
            )

            writer.writerows(
                csv_rows
            )

        return output_path.resolve()

    def _build_csv_rows(
        self,
        generated_rows: list[GeneratedPricingRow]
    ) -> list[list[object]]:
        """
        Builds the complete CSV table in the required order.
        """

        band_definition_row = (
            self._build_configured_row(
                section_name="band_definition_row",
                column_count=6
            )
        )

        band_threshold_row = (
            self._build_configured_row(
                section_name="band_threshold_row",
                column_count=6
            )
        )

        column_header_row = (
            self._build_configured_row(
                section_name="column_header_row",
                column_count=8
            )
        )

        all_others_source_row = generated_rows[0]

        all_others_row = [
            "",
            "",
            self._format_decimal(
                all_others_source_row.price
            ),
            "",
            "",
            "",
            "",
            ""
        ]

        country_rows = [
            self._build_country_row(
                generated_row
            )
            for generated_row in generated_rows[1:]
        ]

        return [
            band_definition_row,
            band_threshold_row,
            column_header_row,
            all_others_row,
            *country_rows
        ]

    def _build_country_row(
        self,
        generated_row: GeneratedPricingRow
    ) -> list[object]:
        """
        Converts one generated destination into an eight-column
        CSV row.
        """

        corrected_country_name = (
            self._country_name_corrections.get(
                generated_row.country,
                generated_row.country
            )
        )

        return [
            corrected_country_name,
            generated_row.iso2,
            self._format_decimal(
                generated_row.price
            ),
            "",
            "",
            "",
            "",
            ""
        ]

    def _build_configured_row(
        self,
        section_name: str,
        column_count: int
    ) -> list[object]:
        """
        Builds a configured CSV row using Excel-style column
        letters.
        """

        section = self._output_csv_schema.get(
            section_name
        )

        if not isinstance(section, dict):
            raise ValueError(
                f"Output CSV schema section "
                f"'{section_name}' is missing or invalid."
            )

        column_letters = [
            chr(ord("A") + index)
            for index in range(column_count)
        ]

        return [
            self._normalize_csv_value(
                section.get(column_letter)
            )
            for column_letter in column_letters
        ]

    def _resolve_output_directory(self) -> Path:
        """
        Resolves the configured destination directory.
        """

        output_directory_pattern = str(
            self._output_settings.get(
                "directory",
                ""
            )
        ).strip()

        if not output_directory_pattern:
            raise ValueError(
                "Output directory cannot be empty."
            )

        return self._path_resolver.resolve_path(
            output_directory_pattern
        )

    def _build_filename(
        self,
        generation_result: GenerationResult,
        generation_date: date
    ) -> str:
        """
        Renders and sanitizes the configured filename.
        """

        filename_pattern = str(
            self._output_settings.get(
                "filename_pattern",
                ""
            )
        ).strip()

        if not filename_pattern:
            raise ValueError(
                "Output filename pattern cannot be empty."
            )

        rendered_filename = filename_pattern

        replacements = {
            "{currency}": generation_result.currency,
            "{product}": (
                generation_result.product_output_name
            ),
            "{pricing_type}": (
                generation_result.pricing_type
            ),
            "{MMM YYYY}": (
                generation_date.strftime("%b %Y")
            )
        }

        for placeholder, replacement_value in (
            replacements.items()
        ):
            rendered_filename = (
                rendered_filename.replace(
                    placeholder,
                    replacement_value
                )
            )

        unresolved_placeholders = re.findall(
            r"\{[^{}]+\}",
            rendered_filename
        )

        if unresolved_placeholders:
            unresolved_list = ", ".join(
                sorted(
                    set(
                        unresolved_placeholders
                    )
                )
            )

            raise ValueError(
                f"Unsupported output filename "
                f"placeholder(s): {unresolved_list}."
            )

        safe_filename = (
            self.INVALID_FILENAME_CHARACTERS.sub(
                "_",
                rendered_filename
            )
        ).strip()

        if not safe_filename:
            raise ValueError(
                "Rendered output filename cannot be empty."
            )

        if not safe_filename.lower().endswith(
            ".csv"
        ):
            safe_filename = (
                f"{safe_filename}.csv"
            )

        return safe_filename

    def _resolve_quoting(self) -> int:
        """
        Converts configured quoting text into a csv module
        constant.
        """

        configured_quoting = str(
            self._output_settings.get(
                "quoting",
                "minimal"
            )
        ).strip().lower()

        quoting_options = {
            "minimal": csv.QUOTE_MINIMAL,
            "all": csv.QUOTE_ALL,
            "nonnumeric": csv.QUOTE_NONNUMERIC,
            "none": csv.QUOTE_NONE
        }

        if configured_quoting not in quoting_options:
            raise ValueError(
                f"Unsupported CSV quoting option "
                f"'{configured_quoting}'."
            )

        return quoting_options[
            configured_quoting
        ]

    @staticmethod
    def _format_decimal(
        value: Decimal
    ) -> str:
        """
        Formats a generated price for CSV output.

        Prices with more than four decimal places are rounded to
        four decimal places using standard half-up rounding.
        Unnecessary trailing zeroes are removed.
        """

        if not isinstance(value, Decimal):
            raise ValueError(
                "Generated pricing value must be Decimal."
            )

        if not value.is_finite():
            raise ValueError(
                "Generated pricing value must be finite."
            )

        four_decimal_places = Decimal(
            "0.0001"
        )

        rounded_value = value.quantize(
            four_decimal_places,
            rounding=ROUND_HALF_UP
        )

        if rounded_value == 0:
            return "0"

        formatted_value = format(
            rounded_value,
            "f"
        )

        formatted_value = (
            formatted_value
            .rstrip("0")
            .rstrip(".")
        )

        return formatted_value
    
    @staticmethod
    def _normalize_csv_value(
        value: object
    ) -> object:
        """
        Converts configured null values into blank CSV cells.
        """

        if value is None:
            return ""

        return value

    @staticmethod
    def _validate_generation_result(
        generation_result: GenerationResult
    ) -> None:
        """
        Confirms the result contains valid exportable rows.
        """

        if not generation_result.rows:
            raise ValueError(
                "Generation result contains no pricing rows."
            )

        all_others_row = (
            generation_result.rows[0]
        )

        if (
            all_others_row.country
            or all_others_row.iso2
        ):
            raise ValueError(
                "The first generated row must be the blank "
                "All Others output row."
            )

        seen_iso2_codes: set[str] = set()

        for row_index, generated_row in enumerate(
            generation_result.rows,
            start=1
        ):
            if not isinstance(
                generated_row,
                GeneratedPricingRow
            ):
                raise ValueError(
                    f"Generation result row {row_index} "
                    f"is not a GeneratedPricingRow."
                )

            if row_index == 1:
                continue

            if not generated_row.country.strip():
                raise ValueError(
                    f"Generated country row {row_index} "
                    f"has a blank Country."
                )

            if not generated_row.iso2.strip():
                raise ValueError(
                    f"Generated country row {row_index} "
                    f"for country '{generated_row.country}' "
                    f"has a blank ISO2."
                )

            if generated_row.iso2 in seen_iso2_codes:
                raise ValueError(
                    f"Generated pricing contains duplicate "
                    f"ISO2 '{generated_row.iso2}'."
                )

            seen_iso2_codes.add(
                generated_row.iso2
            )