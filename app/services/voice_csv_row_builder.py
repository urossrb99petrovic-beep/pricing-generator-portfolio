from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.models.generated_voice_pricing_row import (
    GeneratedVoicePricingRow
)


class VoiceCsvRowBuilder:
    """
    Converts generated Voice pricing rows into CSV rows
    according to a configured Voice output schema.

    This service builds the CSV table only. Writing the table
    to a physical file is handled separately.
    """

    PRICE_ATTRIBUTE_BY_GROUP = {
        "landline": "landline_price",
        "mobile": "mobile_price",

        "landline_outbound": "landline_price",
        "mobile_outbound": "mobile_price",

        "inbound": "inbound_price"
    }

    def __init__(
        self,
        voice_output_csv_schemas: dict[str, Any],
        country_name_corrections: dict[str, str]
        | None = None
    ) -> None:
        """
        Creates the Voice CSV row builder.

        Args:
            voice_output_csv_schemas:
                Voice CSV schemas loaded from schemas.json.

            country_name_corrections:
                Optional source-to-output country corrections.
        """

        if not voice_output_csv_schemas:
            raise ValueError(
                "Voice output CSV schemas cannot be empty."
            )

        self._voice_output_csv_schemas = (
            voice_output_csv_schemas
        )

        self._country_name_corrections = (
            country_name_corrections or {}
        )

    def build_rows(
        self,
        generated_rows: list[GeneratedVoicePricingRow],
        schema_id: str
    ) -> list[list[object]]:
        """
        Builds the complete CSV table for one Voice output.

        Args:
            generated_rows:
                Final Voice pricing rows.

            schema_id:
                Configured Voice output schema ID.

        Returns:
            Complete CSV table ready to be written by csv.writer.

        Raises:
            ValueError:
                If rows or schema configuration are invalid.
        """

        schema = self._get_schema(
            schema_id
        )

        self._validate_generated_rows(
            generated_rows=generated_rows,
            schema=schema
        )

        column_count = self._get_column_count(
            schema
        )

        csv_rows: list[list[object]] = []

        if "band_definition_row" in schema:
            csv_rows.append(
                self._build_configured_row(
                    schema=schema,
                    section_name=(
                        "band_definition_row"
                    ),
                    column_count=6
                )
            )

        if "band_threshold_row" in schema:
            csv_rows.append(
                self._build_configured_row(
                    schema=schema,
                    section_name=(
                        "band_threshold_row"
                    ),
                    column_count=6
                )
            )

        if "column_header_row" in schema:
            csv_rows.append(
                self._build_configured_row(
                    schema=schema,
                    section_name=(
                        "column_header_row"
                    ),
                    column_count=column_count
                )
            )

        all_others_row = self._build_voice_data_row(
            generated_row=generated_rows[0],
            schema=schema,
            row_rule_name=(
                "all_other_countries_row"
            ),
            column_count=column_count,
            is_all_others=True
        )

        csv_rows.append(
            all_others_row
        )

        for generated_row in generated_rows[1:]:
            csv_rows.append(
                self._build_voice_data_row(
                    generated_row=generated_row,
                    schema=schema,
                    row_rule_name=(
                        "country_data_rows"
                    ),
                    column_count=column_count,
                    is_all_others=False
                )
            )

        return csv_rows

    def _get_schema(
        self,
        schema_id: str
    ) -> dict[str, Any]:
        """
        Returns one configured Voice output schema.
        """

        normalized_schema_id = (
            schema_id.strip()
        )

        if not normalized_schema_id:
            raise ValueError(
                "Voice output schema ID cannot be empty."
            )

        schema = (
            self._voice_output_csv_schemas.get(
                normalized_schema_id
            )
        )

        if not isinstance(
            schema,
            dict
        ):
            raise ValueError(
                f"Unknown Voice output CSV schema "
                f"'{normalized_schema_id}'."
            )

        return schema

    @staticmethod
    def _get_column_count(
        schema: dict[str, Any]
    ) -> int:
        """
        Returns the configured total output-column count.
        """

        validation = schema.get(
            "validation",
            {}
        )

        column_count = validation.get(
            "exact_column_count"
        )

        if (
            not isinstance(column_count, int)
            or column_count <= 0
        ):
            raise ValueError(
                "Voice output schema must define a positive "
                "'exact_column_count'."
            )

        return column_count

    def _build_configured_row(
        self,
        schema: dict[str, Any],
        section_name: str,
        column_count: int
    ) -> list[object]:
        """
        Builds one configured row using Excel-style
        column letters.
        """

        section = schema.get(
            section_name
        )

        if not isinstance(
            section,
            dict
        ):
            raise ValueError(
                f"Voice output schema section "
                f"'{section_name}' is missing or invalid."
            )

        row_values: list[object] = [
            ""
            for _ in range(
                column_count
            )
        ]

        for column_letter, configured_value in (
            section.items()
        ):
            column_index = (
                self._excel_column_to_index(
                    column_letter
                )
            )

            if column_index >= column_count:
                raise ValueError(
                    f"Configured column "
                    f"'{column_letter}' is outside the "
                    f"Voice CSV column count "
                    f"{column_count}."
                )

            row_values[
                column_index
            ] = self._normalize_csv_value(
                configured_value
            )

        return row_values

    def _build_voice_data_row(
        self,
        generated_row: GeneratedVoicePricingRow,
        schema: dict[str, Any],
        row_rule_name: str,
        column_count: int,
        is_all_others: bool
    ) -> list[object]:
        """
        Builds one All Others or country pricing row.
        """

        row_rule = schema.get(
            row_rule_name
        )

        if not isinstance(
            row_rule,
            dict
        ):
            raise ValueError(
                f"Voice output schema section "
                f"'{row_rule_name}' is missing or invalid."
            )

        output_row: list[object] = [
            ""
            for _ in range(
                column_count
            )
        ]

        if not is_all_others:
            corrected_country_name = (
                self._country_name_corrections.get(
                    generated_row.country,
                    generated_row.country
                )
            )

            output_row[0] = (
                corrected_country_name
            )

            output_row[1] = (
                generated_row.iso2
            )

        price_column_groups = row_rule.get(
            "price_column_groups",
            {}
        )

        if not isinstance(
            price_column_groups,
            dict
        ):
            raise ValueError(
                f"Voice output schema section "
                f"'{row_rule_name}' has invalid "
                f"'price_column_groups'."
            )

        output_columns_by_header = (
            self._build_output_header_mapping(
                schema
            )
        )

        for (
            price_group_name,
            output_headers
        ) in price_column_groups.items():

            model_attribute = (
                self.PRICE_ATTRIBUTE_BY_GROUP.get(
                    price_group_name
                )
            )

            if model_attribute is None:
                raise ValueError(
                    f"Unsupported Voice price group "
                    f"'{price_group_name}'."
                )

            price_value = getattr(
                generated_row,
                model_attribute
            )

            if price_value is None:
                raise ValueError(
                    f"Voice pricing row for "
                    f"'{generated_row.country or 'All Others'}' "
                    f"does not contain required "
                    f"'{price_group_name}' pricing."
                )

            formatted_price = (
                self._format_decimal(
                    price_value
                )
            )

            if not isinstance(
                output_headers,
                list
            ):
                raise ValueError(
                    f"Voice price group "
                    f"'{price_group_name}' must define "
                    f"a list of output headers."
                )

            for output_header in output_headers:
                if (
                    output_header
                    not in output_columns_by_header
                ):
                    raise ValueError(
                        f"Voice output header "
                        f"'{output_header}' was not found "
                        f"in the configured schema."
                    )

                output_column_index = (
                    output_columns_by_header[
                        output_header
                    ]
                )

                output_row[
                    output_column_index
                ] = formatted_price

        return output_row

    def _build_output_header_mapping(
        self,
        schema: dict[str, Any]
    ) -> dict[str, int]:
        """
        Maps configured output header names to zero-based
        CSV column indexes.

        Example:
            Band1:Landline -> 2
            Band1:Mobile   -> 8
        """

        configured_columns = schema.get(
            "columns"
        )

        if not isinstance(
            configured_columns,
            dict
        ):
            raise ValueError(
                "Voice output schema must define "
                "'columns'."
            )

        output_columns_by_header: dict[
            str,
            int
        ] = {}

        for (
            column_letter,
            header_name
        ) in configured_columns.items():

            if not isinstance(
                header_name,
                str
            ):
                continue

            normalized_header_name = (
                header_name.strip()
            )

            if not normalized_header_name:
                continue

            if (
                normalized_header_name
                in output_columns_by_header
            ):
                raise ValueError(
                    f"Duplicate Voice output header "
                    f"'{normalized_header_name}'."
                )

            output_columns_by_header[
                normalized_header_name
            ] = (
                self._excel_column_to_index(
                    column_letter
                )
            )

        return output_columns_by_header

    @staticmethod
    def _excel_column_to_index(
        column_letter: str
    ) -> int:
        """
        Converts an Excel-style column name into a zero-based
        column index.

        Examples:
            A  -> 0
            B  -> 1
            Z  -> 25
            AA -> 26
            AL -> 37
        """

        normalized_column = (
            str(
                column_letter
            )
            .strip()
            .upper()
        )

        if (
            not normalized_column
            or not normalized_column.isalpha()
        ):
            raise ValueError(
                f"Invalid Excel column "
                f"'{column_letter}'."
            )

        column_number = 0

        for character in normalized_column:
            column_number = (
                column_number * 26
                + (
                    ord(character)
                    - ord("A")
                    + 1
                )
            )

        return (
            column_number - 1
        )

    @staticmethod
    def _format_decimal(
        value: Decimal
    ) -> str:
        """
        Formats Voice pricing exactly like the SMS exporter.

        Prices are rounded to a maximum of four decimal places
        using ROUND_HALF_UP and trailing zeroes are removed.
        """

        if not isinstance(
            value,
            Decimal
        ):
            raise ValueError(
                "Generated Voice pricing value must be Decimal."
            )

        if not value.is_finite():
            raise ValueError(
                "Generated Voice pricing value must be finite."
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

        return (
            formatted_value
            .rstrip("0")
            .rstrip(".")
        )

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
    def _validate_generated_rows(
        generated_rows: list[
            GeneratedVoicePricingRow
        ],
        schema: dict[str, Any]
    ) -> None:
        """
        Validates final Voice rows before CSV construction.
        """

        if not generated_rows:
            raise ValueError(
                "Generated Voice pricing rows cannot be empty."
            )

        all_others_row = (
            generated_rows[0]
        )

        if not isinstance(
            all_others_row,
            GeneratedVoicePricingRow
        ):
            raise ValueError(
                "Generated Voice pricing contains an "
                "invalid All Others row."
            )

        if (
            all_others_row.country
            or all_others_row.iso2
        ):
            raise ValueError(
                "The first generated Voice row must be "
                "the blank All Others output row."
            )

        seen_iso2_codes: set[str] = set()

        for row_index, generated_row in enumerate(
            generated_rows,
            start=1
        ):
            if not isinstance(
                generated_row,
                GeneratedVoicePricingRow
            ):
                raise ValueError(
                    f"Generated Voice row {row_index} "
                    f"is not a GeneratedVoicePricingRow."
                )

            if row_index == 1:
                continue

            if not generated_row.country.strip():
                raise ValueError(
                    f"Generated Voice country row "
                    f"{row_index} has a blank Country."
                )

            if not generated_row.iso2.strip():
                raise ValueError(
                    f"Generated Voice country row "
                    f"{row_index} for "
                    f"'{generated_row.country}' "
                    f"has a blank ISO2."
                )

            if (
                generated_row.iso2
                in seen_iso2_codes
            ):
                raise ValueError(
                    f"Generated Voice pricing contains "
                    f"duplicate ISO2 "
                    f"'{generated_row.iso2}'."
                )

            seen_iso2_codes.add(
                generated_row.iso2
            )

        price_groups = (
            schema.get(
                "country_data_rows",
                {}
            )
            .get(
                "price_column_groups",
                {}
            )
        )

        if (
            "inbound" in price_groups
        ):
            for row_index, generated_row in enumerate(
                generated_rows,
                start=1
            ):
                if (
                    generated_row.inbound_price
                    is None
                ):
                    raise ValueError(
                        f"Generated Voice row "
                        f"{row_index} does not contain "
                        f"required inbound pricing."
                    )