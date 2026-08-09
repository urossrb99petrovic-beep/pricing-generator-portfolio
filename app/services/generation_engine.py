from decimal import Decimal

from app.models.generated_pricing_row import GeneratedPricingRow
from app.models.pricing_row import PricingRow
from app.models.sender_override_price import (
    SenderOverridePrice
)


class GenerationEngine:
    """
    Converts source pricing data into final generated pricing
    rows by applying Pricing Generator business rules.
    """

    SUPPORTED_PRICING_TYPES = {
        "Baseline",
        "Enterprise"
    }

    ALL_OTHERS_SOURCE_NAME = "All Others"

    DEFAULT_SENDER_ID = "DSC"

    SUPPORTED_SENDER_COUNTRIES = {
        "US",
        "CA"
    }

    def generate_pricing(
        self,
        base_pricing_rows: list[PricingRow],
        pricing_type: str,
        selected_sender_ids: dict[str, str] | None = None,
        sender_override_prices: dict[
            str,
            SenderOverridePrice
        ] | None = None,
        local_pricing_rows: list[PricingRow] | None = None,
        selected_local_countries: list[str] | None = None
    ) -> list[GeneratedPricingRow]:
        """
        Generates final destination pricing by applying all selected
        pricing rules in the required sequence.

        Args:
            base_pricing_rows:
                Standard source pricing rows for the selected
                product.

            pricing_type:
                Pricing type selected by the user.

            selected_sender_ids:
                Sender choice by supported country.

                Example:
                    {
                        "US": "10DLC",
                        "CA": "DSC"
                    }

            sender_override_prices:
                Loaded sender override prices by country.

                Example:
                    {
                        "US": SenderOverridePrice(...)
                    }

            local_pricing_rows:
                Local SMS or Local Premium SMS source pricing rows.

            selected_local_countries:
                Countries selected by the user for Local pricing.

        Returns:
            Final generated pricing rows after all relevant
            overrides have been applied.
        """

        normalized_sender_ids = (
            selected_sender_ids or {}
        )

        normalized_sender_prices = (
            sender_override_prices or {}
        )

        normalized_local_rows = (
            local_pricing_rows or []
        )

        normalized_local_countries = (
            selected_local_countries or []
        )

        generated_rows = self.generate_base_rows(
            pricing_rows=base_pricing_rows,
            pricing_type=pricing_type
        )

        generated_rows = self.apply_sender_overrides(
            generated_rows=generated_rows,
            pricing_type=pricing_type,
            selected_sender_ids=normalized_sender_ids,
            sender_override_prices=(
                normalized_sender_prices
            )
        )

        generated_rows = self.apply_local_overrides(
            generated_rows=generated_rows,
            local_pricing_rows=normalized_local_rows,
            selected_local_countries=(
                normalized_local_countries
            ),
            pricing_type=pricing_type
        )

        return generated_rows

    def generate_base_rows(
        self,
        pricing_rows: list[PricingRow],
        pricing_type: str
    ) -> list[GeneratedPricingRow]:
        """
        Converts source pricing rows into generated rows using
        the selected pricing type.

        Args:
            pricing_rows:
                Source pricing rows extracted from the workbook.

            pricing_type:
                Pricing type selected by the user.

        Returns:
            Generated pricing rows in source workbook order.

        Raises:
            ValueError:
                If the pricing type is unsupported or no source
                rows are supplied.
        """

        self._validate_pricing_type(
            pricing_type
        )

        if not pricing_rows:
            raise ValueError(
                "Pricing rows cannot be empty."
            )

        generated_rows: list[
            GeneratedPricingRow
        ] = []

        for pricing_row in pricing_rows:
            selected_price = (
                self._select_price(
                    pricing_row=pricing_row,
                    pricing_type=pricing_type
                )
            )

            country = pricing_row.country
            iso2 = pricing_row.iso2

            if (
                pricing_row.country
                == self.ALL_OTHERS_SOURCE_NAME
            ):
                country = ""
                iso2 = ""

            generated_rows.append(
                GeneratedPricingRow(
                    country=country,
                    iso2=iso2,
                    price=selected_price
                )
            )

        return generated_rows

    def apply_sender_overrides(
        self,
        generated_rows: list[GeneratedPricingRow],
        pricing_type: str,
        selected_sender_ids: dict[str, str],
        sender_override_prices: dict[
            str,
            SenderOverridePrice
        ]
    ) -> list[GeneratedPricingRow]:
        """
        Applies non-default US and Canada sender prices.

        Args:
            generated_rows:
                Base generated pricing rows.

            pricing_type:
                Pricing type selected by the user.

            selected_sender_ids:
                Sender choice by country.

                Example:
                    {
                        "US": "10DLC",
                        "CA": "DSC"
                    }

            sender_override_prices:
                Loaded sender override prices by country.

                Example:
                    {
                        "US": SenderOverridePrice(...)
                    }

        Returns:
            New generated rows with relevant prices replaced.

        Raises:
            ValueError:
                If input values are invalid, a required override
                price is missing, or the target ISO2 cannot be found.
        """

        self._validate_pricing_type(
            pricing_type
        )

        if not generated_rows:
            raise ValueError(
                "Generated pricing rows cannot be empty."
            )

        self._validate_selected_sender_ids(
            selected_sender_ids
        )

        updated_rows = list(
            generated_rows
        )

        for country_code, sender_id in (
            selected_sender_ids.items()
        ):
            if sender_id == self.DEFAULT_SENDER_ID:
                continue

            if (
                country_code
                not in sender_override_prices
            ):
                raise ValueError(
                    f"Sender override price is missing for "
                    f"country '{country_code}' and sender "
                    f"'{sender_id}'."
                )

            sender_override_price = (
                sender_override_prices[
                    country_code
                ]
            )

            selected_price = (
                self._select_sender_override_price(
                    sender_override_price=(
                        sender_override_price
                    ),
                    pricing_type=pricing_type
                )
            )

            updated_rows = (
                self._replace_price_by_iso2(
                    generated_rows=updated_rows,
                    iso2=country_code,
                    replacement_price=selected_price
                )
            )

        return updated_rows

    def apply_local_overrides(
        self,
        generated_rows: list[GeneratedPricingRow],
        local_pricing_rows: list[PricingRow],
        selected_local_countries: list[str],
        pricing_type: str
    ) -> list[GeneratedPricingRow]:
        """
        Applies Local SMS or Local Premium SMS prices to selected
        countries.

        Args:
            generated_rows:
                Base generated pricing rows.

            local_pricing_rows:
                Extracted Local pricing rows.

            selected_local_countries:
                Countries selected by the user for Local pricing.

            pricing_type:
                Pricing type selected by the user.

        Returns:
            New generated rows with selected Local prices applied.

        Raises:
            ValueError:
                If required data is missing, duplicated or cannot
                be matched safely.
        """

        self._validate_pricing_type(
            pricing_type
        )

        if not generated_rows:
            raise ValueError(
                "Generated pricing rows cannot be empty."
            )

        if not selected_local_countries:
            return list(
                generated_rows
            )

        if not local_pricing_rows:
            raise ValueError(
                "Local pricing rows cannot be empty when Local "
                "Countries are selected."
            )

        self._validate_selected_local_countries(
            selected_local_countries
        )

        local_rows_by_country = (
            self._build_local_pricing_mapping(
                local_pricing_rows
            )
        )

        updated_rows = list(
            generated_rows
        )

        for country_name in selected_local_countries:
            if country_name not in local_rows_by_country:
                raise ValueError(
                    f"Local pricing was not found for selected "
                    f"country '{country_name}'."
                )

            local_pricing_row = (
                local_rows_by_country[
                    country_name
                ]
            )

            selected_price = self._select_price(
                pricing_row=local_pricing_row,
                pricing_type=pricing_type
            )

            updated_rows = (
                self._replace_price_by_country(
                    generated_rows=updated_rows,
                    country_name=country_name,
                    replacement_price=selected_price
                )
            )

        return updated_rows

    @classmethod
    def _validate_selected_sender_ids(
        cls,
        selected_sender_ids: dict[str, str]
    ) -> None:
        """
        Validates selected sender-country values.
        """

        unsupported_countries = (
            selected_sender_ids.keys()
            - cls.SUPPORTED_SENDER_COUNTRIES
        )

        if unsupported_countries:
            unsupported_country_list = ", ".join(
                sorted(
                    unsupported_countries
                )
            )

            raise ValueError(
                f"Unsupported sender country code(s): "
                f"{unsupported_country_list}."
            )

        for country_code, sender_id in (
            selected_sender_ids.items()
        ):
            if not sender_id.strip():
                raise ValueError(
                    f"Sender ID for country "
                    f"'{country_code}' cannot be empty."
                )

    @classmethod
    def _validate_pricing_type(
        cls,
        pricing_type: str
    ) -> None:
        """
        Confirms that the selected pricing type is supported.

        Raises:
            ValueError:
                If the pricing type is empty or unsupported.
        """

        if not pricing_type.strip():
            raise ValueError(
                "Pricing type cannot be empty."
            )

        if (
            pricing_type
            not in cls.SUPPORTED_PRICING_TYPES
        ):
            supported_types = ", ".join(
                sorted(
                    cls.SUPPORTED_PRICING_TYPES
                )
            )

            raise ValueError(
                f"Unsupported pricing type "
                f"'{pricing_type}'. Supported types: "
                f"{supported_types}."
            )

    @staticmethod
    def _validate_selected_local_countries(
        selected_local_countries: list[str]
    ) -> None:
        """
        Confirms selected Local Country names are valid and unique.
        """

        blank_countries = [
            country_name
            for country_name in selected_local_countries
            if not country_name.strip()
        ]

        if blank_countries:
            raise ValueError(
                "Selected Local Country names cannot be blank."
            )

        seen_countries: set[str] = set()
        duplicate_countries: list[str] = []

        for country_name in selected_local_countries:
            if country_name in seen_countries:
                duplicate_countries.append(
                    country_name
                )
            else:
                seen_countries.add(
                    country_name
                )

        if duplicate_countries:
            duplicate_country_list = ", ".join(
                sorted(
                    set(
                        duplicate_countries
                    )
                )
            )

            raise ValueError(
                f"Duplicate selected Local Country name(s): "
                f"{duplicate_country_list}."
            )

    @staticmethod
    def _select_sender_override_price(
        sender_override_price: SenderOverridePrice,
        pricing_type: str
    ) -> Decimal:
        """
        Returns the sender override price matching Pricing Type.
        """

        if pricing_type == "Baseline":
            return (
                sender_override_price.baseline_price
            )

        return (
            sender_override_price.enterprise_price
        )

    @staticmethod
    def _select_price(
        pricing_row: PricingRow,
        pricing_type: str
    ):
        """
        Returns the source price matching the selected pricing
        type.
        """

        if pricing_type == "Baseline":
            return pricing_row.baseline_price

        return pricing_row.enterprise_price

    @staticmethod
    def _replace_price_by_iso2(
        generated_rows: list[GeneratedPricingRow],
        iso2: str,
        replacement_price: Decimal
    ) -> list[GeneratedPricingRow]:
        """
        Replaces one destination price using its ISO2 code while
        preserving row order.

        Raises:
            ValueError:
                If no row or multiple rows match the ISO2 code.
        """

        matching_indexes = [
            row_index
            for row_index, generated_row
            in enumerate(generated_rows)
            if generated_row.iso2 == iso2
        ]

        if not matching_indexes:
            raise ValueError(
                f"Generated pricing row with ISO2 "
                f"'{iso2}' was not found."
            )

        if len(matching_indexes) > 1:
            raise ValueError(
                f"Generated pricing contains multiple rows "
                f"with ISO2 '{iso2}'."
            )

        matching_index = matching_indexes[0]
        original_row = generated_rows[
            matching_index
        ]

        updated_rows = list(
            generated_rows
        )

        updated_rows[
            matching_index
        ] = GeneratedPricingRow(
            country=original_row.country,
            iso2=original_row.iso2,
            price=replacement_price
        )

        return updated_rows

    @staticmethod
    def _build_local_pricing_mapping(
        local_pricing_rows: list[PricingRow]
    ) -> dict[str, PricingRow]:
        """
        Creates a country-to-local-pricing mapping.

        Raises:
            ValueError:
                If Local pricing contains blank or duplicate
                country names.
        """

        local_rows_by_country: dict[
            str,
            PricingRow
        ] = {}

        duplicate_countries: list[str] = []

        for pricing_row in local_pricing_rows:
            country_name = (
                pricing_row.country.strip()
            )

            if not country_name:
                raise ValueError(
                    "Local pricing contains a blank country name."
                )

            if country_name in local_rows_by_country:
                duplicate_countries.append(
                    country_name
                )
                continue

            local_rows_by_country[
                country_name
            ] = pricing_row

        if duplicate_countries:
            duplicate_country_list = ", ".join(
                sorted(
                    set(
                        duplicate_countries
                    )
                )
            )

            raise ValueError(
                f"Local pricing contains duplicate country "
                f"name(s): {duplicate_country_list}."
            )

        return local_rows_by_country

    @staticmethod
    def _replace_price_by_country(
        generated_rows: list[GeneratedPricingRow],
        country_name: str,
        replacement_price: Decimal
    ) -> list[GeneratedPricingRow]:
        """
        Replaces one destination price using the Country name while
        preserving its ISO2 and original row position.

        Raises:
            ValueError:
                If no row or multiple rows match the Country name.
        """

        matching_indexes = [
            row_index
            for row_index, generated_row
            in enumerate(generated_rows)
            if generated_row.country == country_name
        ]

        if not matching_indexes:
            raise ValueError(
                f"Generated pricing row for country "
                f"'{country_name}' was not found."
            )

        if len(matching_indexes) > 1:
            raise ValueError(
                f"Generated pricing contains multiple rows for "
                f"country '{country_name}'."
            )

        matching_index = matching_indexes[0]

        original_row = generated_rows[
            matching_index
        ]

        updated_rows = list(
            generated_rows
        )

        updated_rows[
            matching_index
        ] = GeneratedPricingRow(
            country=original_row.country,
            iso2=original_row.iso2,
            price=replacement_price
        )

        return updated_rows
