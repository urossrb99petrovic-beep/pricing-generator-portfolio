from decimal import Decimal
from typing import Any

from app.models.generated_viber_pricing_row import (
    GeneratedViberPricingRow
)


class ViberCsvRowBuilder:
    """
    Builds the dedicated Viber upload CSV structure.

    Template structure:

        Row 1:
            30 Viber band headers.

        Row 2:
            zero threshold values in A, G, M, S and Y.

        Row 3:
            Country, ISO2 and 30 Viber band headers.

        Row 4:
            All Others.

        Row 5+:
            Individual countries.

    Only Band1 pricing columns are populated:

        C  = Transactional/OTP
        I  = Transactional/OTP
        O  = Promotional
        U  = International
        AA = Session Chat
    """

    def __init__(
        self,
        output_schema: dict[str, Any]
    ) -> None:

        if not output_schema:
            raise ValueError(
                "Viber output schema cannot be empty."
            )

        self._output_schema = output_schema

    def build_rows(
        self,
        pricing_rows: list[
            GeneratedViberPricingRow
        ]
    ) -> list[list[str]]:
        """
        Builds all Viber CSV rows.
        """

        if not pricing_rows:
            raise ValueError(
                "Viber pricing rows cannot be empty."
            )

        self._validate_first_row_is_all_other(
            pricing_rows[0]
        )

        row_1 = self._build_row_1()
        row_2 = self._build_row_2()
        row_3 = self._build_row_3()

        output_rows = [
            row_1,
            row_2,
            row_3
        ]

        for pricing_row in pricing_rows:
            output_rows.append(
                self._build_pricing_row(
                    pricing_row
                )
            )

        return output_rows

    def _build_row_1(
        self
    ) -> list[str]:

        headers = self._output_schema.get(
            "row_1_headers"
        )

        if (
            not isinstance(headers, list)
            or len(headers) != 30
        ):
            raise ValueError(
                "Viber row 1 must contain exactly "
                "30 configured headers."
            )

        return [
            str(value)
            for value in headers
        ]

    def _build_row_2(
        self
    ) -> list[str]:
        """
        Creates the 30-column band threshold row.

        Zeroes:
            A, G, M, S, Y
        """

        row = [
            ""
            for _ in range(30)
        ]

        zero_columns = (
            self._output_schema.get(
                "row_2_zero_columns",
                []
            )
        )

        for column_letter in zero_columns:
            column_index = (
                self._excel_column_to_index(
                    column_letter
                )
            )

            if (
                column_index < 0
                or column_index >= len(row)
            ):
                raise ValueError(
                    f"Viber row 2 column "
                    f"'{column_letter}' is outside "
                    f"the 30-column template."
                )

            row[
                column_index
            ] = "0"

        return row

    def _build_row_3(
        self
    ) -> list[str]:

        headers = self._output_schema.get(
            "row_3_headers"
        )

        if (
            not isinstance(headers, list)
            or len(headers) != 32
        ):
            raise ValueError(
                "Viber row 3 must contain exactly "
                "32 configured headers."
            )

        return [
            str(value)
            for value in headers
        ]

    def _build_pricing_row(
        self,
        pricing_row: GeneratedViberPricingRow
    ) -> list[str]:
        """
        Builds one 32-column All Others or country row.
        """

        row = [
            ""
            for _ in range(32)
        ]

        row[0] = pricing_row.country
        row[1] = pricing_row.iso2

        price_columns = (
            self._output_schema.get(
                "price_columns",
                {}
            )
        )

        self._write_price(
            row=row,
            column_letter=(
                price_columns[
                    "transactional_otp_primary"
                ]
            ),
            price=(
                pricing_row
                .transactional_otp_price
            )
        )

        self._write_price(
            row=row,
            column_letter=(
                price_columns[
                    "transactional_otp_secondary"
                ]
            ),
            price=(
                pricing_row
                .transactional_otp_price
            )
        )

        self._write_price(
            row=row,
            column_letter=(
                price_columns[
                    "promotional"
                ]
            ),
            price=(
                pricing_row
                .promotional_price
            )
        )

        self._write_price(
            row=row,
            column_letter=(
                price_columns[
                    "international"
                ]
            ),
            price=(
                pricing_row
                .international_price
            )
        )

        self._write_price(
            row=row,
            column_letter=(
                price_columns[
                    "session_chat"
                ]
            ),
            price=(
                pricing_row
                .session_chat_price
            )
        )

        return row

    def _write_price(
        self,
        row: list[str],
        column_letter: str,
        price: Decimal
    ) -> None:

        column_index = (
            self._excel_column_to_index(
                column_letter
            )
        )

        if (
            column_index < 0
            or column_index >= len(row)
        ):
            raise ValueError(
                f"Viber price column "
                f"'{column_letter}' is outside "
                f"the 32-column template."
            )

        row[
            column_index
        ] = self._format_price(
            price
        )

    @staticmethod
    def _format_price(
        price: Decimal
    ) -> str:
        """
        Formats a Viber price with a maximum of four
        decimal places and removes unnecessary trailing
        zeroes.

        Examples:

            0.4000 -> 0.4
            0.4250 -> 0.425
            0.4257 -> 0.4257
            1.0000 -> 1
        """

        if not isinstance(
            price,
            Decimal
        ):
            raise ValueError(
                "Viber output price must be Decimal."
            )

        if not price.is_finite():
            raise ValueError(
                "Viber output price must be finite."
            )

        normalized_value = format(
            price,
            "f"
        )

        if "." in normalized_value:
            normalized_value = (
                normalized_value
                .rstrip("0")
                .rstrip(".")
            )

        if normalized_value in {
            "",
            "-0"
        }:
            normalized_value = "0"

        return normalized_value

    @staticmethod
    def _excel_column_to_index(
        column_letter: str
    ) -> int:
        """
        Converts Excel column letters into zero-based
        indexes.

        A  -> 0
        C  -> 2
        I  -> 8
        AA -> 26
        """

        normalized_column = (
            str(
                column_letter
            )
            .strip()
            .upper()
        )

        if not normalized_column:
            raise ValueError(
                "Excel column cannot be empty."
            )

        column_number = 0

        for character in (
            normalized_column
        ):
            if (
                character < "A"
                or character > "Z"
            ):
                raise ValueError(
                    f"Invalid Excel column "
                    f"'{column_letter}'."
                )

            column_number = (
                column_number
                * 26
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
    def _validate_first_row_is_all_other(
        first_row: GeneratedViberPricingRow
    ) -> None:
        """
        The first generated Viber pricing row must represent
        All Others.
        """

        if (
            first_row.country.strip()
            or first_row.iso2.strip()
        ):
            raise ValueError(
                "The first Viber pricing row must "
                "represent All Others."
            )