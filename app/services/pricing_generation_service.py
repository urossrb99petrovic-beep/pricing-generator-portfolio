from typing import Any

from app.models.generated_pricing_row import (
    GeneratedPricingRow
)
from app.models.pricing_row import PricingRow
from app.models.sender_override_price import (
    SenderOverridePrice
)
from app.services.generation_engine import GenerationEngine
from app.services.pricing_data_service import (
    PricingDataService
)


class PricingGenerationService:
    """
    Coordinates product configuration, pricing-data extraction
    and final pricing generation.
    """

    def __init__(
        self,
        pricing_data_service: PricingDataService,
        generation_engine: GenerationEngine,
        sender_overrides_config: dict[str, Any]
    ) -> None:
        """
        Creates the product-level generation service.

        Args:
            pricing_data_service:
                Service used to extract source pricing.

            generation_engine:
                Engine used to apply pricing rules.

            sender_overrides_config:
                Sender override configuration loaded from
                countries.json.

        Raises:
            ValueError:
                If sender configuration is empty.
        """

        if not sender_overrides_config:
            raise ValueError(
                "Sender override configuration cannot be empty."
            )

        self._pricing_data_service = (
            pricing_data_service
        )

        self._generation_engine = generation_engine

        self._sender_overrides_config = (
            sender_overrides_config
        )

    def generate_product_pricing(
        self,
        product_config: dict[str, Any],
        pricing_type: str,
        selected_sender_ids: dict[str, str] | None = None,
        selected_local_countries: list[str] | None = None
    ) -> list[GeneratedPricingRow]:
        """
        Generates final pricing for one configured product.

        Args:
            product_config:
                Selected product configuration from
                products.json.

            pricing_type:
                Baseline or Enterprise.

            selected_sender_ids:
                User sender selections by country.

            selected_local_countries:
                Local Countries selected by the user.

        Returns:
            Final generated pricing rows.

        Raises:
            ValueError:
                If product configuration or selections are
                invalid.
        """

        self._validate_product_config(
            product_config
        )

        self._validate_product_pricing_type(
            product_config=product_config,
            pricing_type=pricing_type
        )

        normalized_sender_ids = (
            selected_sender_ids or {}
        )

        normalized_local_countries = (
            selected_local_countries or []
        )

        base_pricing_rows = (
            self._load_base_pricing_rows(
                product_config[
                    "base_worksheet"
                ]
            )
        )

        sender_options_enabled = (
            product_config[
                "sender_options"
            ]["enabled"]
        )

        if sender_options_enabled:
            complete_sender_ids = (
                self._complete_sender_selections(
                    product_config=product_config,
                    selected_sender_ids=(
                        normalized_sender_ids
                    )
                )
            )

            sender_override_prices = (
                self._load_sender_override_prices(
                    complete_sender_ids
                )
            )

        else:
            if normalized_sender_ids:
                raise ValueError(
                    f"Product "
                    f"'{product_config['product_id']}' "
                    f"does not support sender options."
                )

            complete_sender_ids = {}
            sender_override_prices = {}

        local_options_enabled = (
            product_config[
                "local_options"
            ]["enabled"]
        )

        if local_options_enabled:
            local_pricing_rows = (
                self._load_local_pricing_rows(
                    product_config[
                        "local_worksheet"
                    ],
                    normalized_local_countries
                )
            )

        else:
            if normalized_local_countries:
                raise ValueError(
                    f"Product "
                    f"'{product_config['product_id']}' "
                    f"does not support Local Countries."
                )

            local_pricing_rows = []

        return self._generation_engine.generate_pricing(
            base_pricing_rows=base_pricing_rows,
            pricing_type=pricing_type,
            selected_sender_ids=complete_sender_ids,
            sender_override_prices=(
                sender_override_prices
            ),
            local_pricing_rows=local_pricing_rows,
            selected_local_countries=(
                normalized_local_countries
            )
        )

    def _load_base_pricing_rows(
        self,
        worksheet_name: str
    ) -> list[PricingRow]:
        """
        Loads base pricing using the configured worksheet.
        """

        if worksheet_name == "SMS":
            return (
                self._pricing_data_service
                .get_sms_pricing()
            )

        if worksheet_name == "Premium SMS":
            return (
                self._pricing_data_service
                .get_premium_sms_pricing()
            )

        if worksheet_name == "SMS MKT":
            return (
                self._pricing_data_service
                .get_sms_marketing_pricing()
            )

        raise ValueError(
            f"Unsupported base pricing worksheet "
            f"'{worksheet_name}'."
        )

    def _load_local_pricing_rows(
        self,
        worksheet_name: object,
        selected_local_countries: list[str]
    ) -> list[PricingRow]:
        """
        Loads Local pricing when at least one Local Country was
        selected.
        """

        if not selected_local_countries:
            return []

        if worksheet_name is None:
            raise ValueError(
                "Local worksheet is not configured."
            )

        normalized_worksheet_name = str(
            worksheet_name
        ).strip()

        if normalized_worksheet_name == "Local SMS":
            return (
                self._pricing_data_service
                .get_local_sms_pricing()
            )

        if (
            normalized_worksheet_name
            == "Local Premium SMS"
        ):
            return (
                self._pricing_data_service
                .get_local_premium_sms_pricing()
            )

        raise ValueError(
            f"Unsupported Local pricing worksheet "
            f"'{normalized_worksheet_name}'."
        )

    def _complete_sender_selections(
        self,
        product_config: dict[str, Any],
        selected_sender_ids: dict[str, str]
    ) -> dict[str, str]:
        """
        Adds configured default sender IDs for supported
        countries that were not explicitly supplied.
        """

        supported_countries = (
            product_config[
                "sender_options"
            ]["supported_countries"]
        )

        configured_countries = (
            self._sender_overrides_config[
                "countries"
            ]
        )

        unsupported_selections = (
            selected_sender_ids.keys()
            - set(supported_countries)
        )

        if unsupported_selections:
            unsupported_country_list = ", ".join(
                sorted(
                    unsupported_selections
                )
            )

            raise ValueError(
                f"Sender selection contains unsupported "
                f"country code(s): "
                f"{unsupported_country_list}."
            )

        complete_sender_ids: dict[
            str,
            str
        ] = {}

        for country_code in supported_countries:
            if country_code not in configured_countries:
                raise ValueError(
                    f"Sender configuration does not contain "
                    f"country '{country_code}'."
                )

            country_config = configured_countries[
                country_code
            ]

            selected_sender_id = (
                selected_sender_ids.get(
                    country_code,
                    country_config[
                        "default_sender_id"
                    ]
                )
            )

            sender_ids = country_config[
                "sender_ids"
            ]

            if selected_sender_id not in sender_ids:
                raise ValueError(
                    f"Sender ID '{selected_sender_id}' is not "
                    f"configured for country "
                    f"'{country_code}'."
                )

            complete_sender_ids[
                country_code
            ] = selected_sender_id

        return complete_sender_ids

    def _load_sender_override_prices(
        self,
        selected_sender_ids: dict[str, str]
    ) -> dict[str, SenderOverridePrice]:
        """
        Loads prices only for sender selections configured to
        apply an override.
        """

        configured_countries = (
            self._sender_overrides_config[
                "countries"
            ]
        )

        sender_override_prices: dict[
            str,
            SenderOverridePrice
        ] = {}

        for country_code, sender_id in (
            selected_sender_ids.items()
        ):
            country_config = configured_countries[
                country_code
            ]

            sender_config = (
                country_config[
                    "sender_ids"
                ][
                    sender_id
                ]
            )

            apply_override = sender_config[
                "apply_override"
            ]

            if not apply_override:
                continue

            worksheet_lookup_value = (
                sender_config[
                    "worksheet_lookup_value"
                ]
            )

            if worksheet_lookup_value is None:
                raise ValueError(
                    f"Sender ID '{sender_id}' for country "
                    f"'{country_code}' requires an override "
                    f"but has no worksheet lookup value."
                )

            normalized_lookup_value = str(
                worksheet_lookup_value
            ).strip()

            if not normalized_lookup_value:
                raise ValueError(
                    f"Sender ID '{sender_id}' for country "
                    f"'{country_code}' has an empty worksheet "
                    f"lookup value."
                )

            sender_override_prices[
                country_code
            ] = (
                self._pricing_data_service
                .get_sender_override_price(
                    normalized_lookup_value
                )
            )

        return sender_override_prices

    @staticmethod
    def _validate_product_config(
        product_config: dict[str, Any]
    ) -> None:
        """
        Confirms that the required product configuration fields
        exist.
        """

        if not product_config:
            raise ValueError(
                "Product configuration cannot be empty."
            )

        required_fields = {
            "product_id",
            "enabled",
            "base_worksheet",
            "supported_pricing_types",
            "sender_options",
            "local_options"
        }

        missing_fields = (
            required_fields
            - product_config.keys()
        )

        if missing_fields:
            missing_field_list = ", ".join(
                sorted(
                    missing_fields
                )
            )

            raise ValueError(
                f"Product configuration is missing required "
                f"field(s): {missing_field_list}."
            )

        if not product_config["enabled"]:
            raise ValueError(
                f"Product "
                f"'{product_config['product_id']}' "
                f"is disabled."
            )

    @staticmethod
    def _validate_product_pricing_type(
        product_config: dict[str, Any],
        pricing_type: str
    ) -> None:
        """
        Confirms the Pricing Type is supported by the selected
        product.
        """

        if not pricing_type.strip():
            raise ValueError(
                "Pricing type cannot be empty."
            )

        supported_pricing_types = (
            product_config[
                "supported_pricing_types"
            ]
        )

        if (
            pricing_type
            not in supported_pricing_types
        ):
            raise ValueError(
                f"Pricing type '{pricing_type}' is not "
                f"supported by product "
                f"'{product_config['product_id']}'."
            )