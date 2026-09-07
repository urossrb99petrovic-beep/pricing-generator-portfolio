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
from app.models.generated_voice_pricing_row import (
    GeneratedVoicePricingRow
)
from app.models.generated_mobile_pricing import (
    GeneratedMobilePricing
)
from app.models.generated_viber_pricing_row import (
    GeneratedViberPricingRow
)
from app.models.generated_phone_id_suite_pricing import (
    GeneratedPhoneIdSuitePricing
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
        pricing_type: str | None,
        selected_sender_ids: dict[str, str] | None = None,
        selected_local_countries: list[str] | None = None,
        selected_product_options: dict[str, str] | None = None,
        selected_subproducts: list[str] | None = None
    ) -> (
        list[GeneratedPricingRow]
        | list[GeneratedVoicePricingRow]
        | list[GeneratedViberPricingRow]
        | GeneratedMobilePricing
        | GeneratedPhoneIdSuitePricing
    ):
        """
        Generates final pricing for one configured product.

        Args:
            product_config:
                Selected product configuration from products.json.

            pricing_type:
                Baseline or Enterprise for products that use
                Pricing Type.

                None for products such as:
                    - Phone ID Suite
                    - Phone ID Live Status

            selected_sender_ids:
                User sender selections by country.

            selected_local_countries:
                Local Countries selected by the user.

            selected_product_options:
                Generic product-specific selections.

                Examples:
                    {
                        "billing_type": "PER_TRANSACTION"
                    }

                    {
                        "traffic_type": "TWO_WAY",
                        "number_type": "US_CLOUD_NUMBERS"
                    }

            selected_subproducts:
                Selected configured subproduct IDs.

                Currently used by Phone ID Suite.

                Example:
                    [
                        "PHONE_ID_STANDARD",
                        "PHONE_ID_CONTACT",
                        "PHONE_ID_SIM_SWAP"
                    ]

        Returns:
            Final generated pricing for the selected product.

            Depending on the product this may be:
                - standard pricing rows;
                - Voice pricing rows;
                - Viber pricing rows;
                - Mobile multi-output pricing;
                - Phone ID Suite multi-subproduct pricing.

        Raises:
            ValueError:
                If product configuration or selections
                are invalid.
        """

        # ==================================================
        # PRODUCT CONFIGURATION
        # ==================================================

        self._validate_product_config(
            product_config
        )

        self._validate_product_pricing_type(
            product_config=product_config,
            pricing_type=pricing_type
        )

        # ==================================================
        # NORMALIZE USER SELECTIONS
        # ==================================================

        normalized_sender_ids = (
            selected_sender_ids or {}
        )

        normalized_local_countries = (
            selected_local_countries or []
        )

        normalized_product_options = {
            option_id.strip(): option_value.strip()
            for option_id, option_value
            in (
                selected_product_options or {}
            ).items()
        }

        normalized_subproducts = [
            str(
                subproduct_id
            ).strip()
            for subproduct_id
            in (
                selected_subproducts or []
            )
        ]

        # ==================================================
        # VALIDATE GENERIC PRODUCT OPTIONS
        # ==================================================

        self._validate_product_options(
            product_config=product_config,
            selected_product_options=(
                normalized_product_options
            )
        )

        self._validate_selected_subproducts(
            product_config=product_config,
            selected_subproducts=(
                normalized_subproducts
            )
        )

        product_id = (
            product_config[
                "product_id"
            ]
        )

        # ==================================================
        # VOICE VERIFY
        # ==================================================

        if product_id == "VOICE_VERIFY":

            if normalized_sender_ids:
                raise ValueError(
                    "Product 'VOICE_VERIFY' does not support "
                    "sender options."
                )

            if normalized_local_countries:
                raise ValueError(
                    "Product 'VOICE_VERIFY' does not support "
                    "Local Countries."
                )

            return self._generate_voice_verify_pricing(
                pricing_type=pricing_type,
                selected_product_options=(
                    normalized_product_options
                )
            )

        # ==================================================
        # VOICE
        # ==================================================

        if product_id == "VOICE":

            if normalized_sender_ids:
                raise ValueError(
                    "Product 'VOICE' does not support "
                    "sender options."
                )

            if normalized_local_countries:
                raise ValueError(
                    "Product 'VOICE' does not support "
                    "Local Countries."
                )

            return self._generate_voice_api_pricing(
                product_config=product_config,
                pricing_type=pricing_type,
                selected_product_options=(
                    normalized_product_options
                )
            )

        # ==================================================
        # VOICE VERIFY + TTS
        # ==================================================

        if product_id == "VOICE_VERIFY_TTS":

            if normalized_sender_ids:
                raise ValueError(
                    "Product 'VOICE_VERIFY_TTS' does not support "
                    "sender options."
                )

            if normalized_local_countries:
                raise ValueError(
                    "Product 'VOICE_VERIFY_TTS' does not support "
                    "Local Countries."
                )

            return self._generate_voice_verify_tts_pricing(
                pricing_type=pricing_type,
                selected_product_options=(
                    normalized_product_options
                )
            )

        # ==================================================
        # TOLL-FREE VOICE
        # ==================================================

        if product_id == "TOLL_FREE_VOICE":

            if normalized_sender_ids:
                raise ValueError(
                    "Product 'TOLL_FREE_VOICE' does not support "
                    "sender options."
                )

            if normalized_local_countries:
                raise ValueError(
                    "Product 'TOLL_FREE_VOICE' does not support "
                    "Local Countries."
                )

            return self._generate_toll_free_voice_pricing(
                pricing_type=pricing_type
            )

        # ==================================================
        # MOBILE
        # ==================================================

        if product_id == "MOBILE_SMS_VOICE":

            if normalized_sender_ids:
                raise ValueError(
                    "Product 'MOBILE_SMS_VOICE' does not support "
                    "sender options."
                )

            if normalized_local_countries:
                raise ValueError(
                    "Product 'MOBILE_SMS_VOICE' does not support "
                    "Local Countries."
                )

            return self._generate_mobile_sms_voice_pricing(
                pricing_type=pricing_type,
                selected_product_options=(
                    normalized_product_options
                )
            )

        # ==================================================
        # WHATSAPP
        # ==================================================

        if product_id == "WHATSAPP":

            if normalized_sender_ids:
                raise ValueError(
                    "WhatsApp does not support sender options."
                )

            if normalized_local_countries:
                raise ValueError(
                    "WhatsApp does not support Local Countries."
                )

            if normalized_product_options:
                raise ValueError(
                    "WhatsApp does not support additional "
                    "product options."
                )

            return self._generate_whatsapp_pricing(
                pricing_type=pricing_type
            )

        # ==================================================
        # VIBER
        # ==================================================

        if product_id == "VIBER":

            if normalized_sender_ids:
                raise ValueError(
                    "Viber does not support sender options."
                )

            if normalized_local_countries:
                raise ValueError(
                    "Viber does not support Local Countries."
                )

            if normalized_product_options:
                raise ValueError(
                    "Viber does not support additional "
                    "product options."
                )

            return self._generate_viber_pricing(
                pricing_type=pricing_type
            )

        # ==================================================
        # PHONE ID SUITE
        #
        # This must happen BEFORE generic base pricing is
        # loaded because Phone ID Suite has its own worksheet
        # structure and produces multiple independent datasets.
        # ==================================================

        if product_id == "PHONE_ID_SUITE":

            # ----------------------------------------------
            # Phone ID Suite has no Sender ID options.
            # ----------------------------------------------

            if normalized_sender_ids:
                raise ValueError(
                    "Phone ID Suite does not support "
                    "sender options."
                )

            # ----------------------------------------------
            # Phone ID Suite has no Local Country options.
            # ----------------------------------------------

            if normalized_local_countries:
                raise ValueError(
                    "Phone ID Suite does not support "
                    "Local Countries."
                )

            # ----------------------------------------------
            # Phone ID Suite currently has no generic
            # choice_options.
            # ----------------------------------------------

            if normalized_product_options:
                raise ValueError(
                    "Phone ID Suite does not support "
                    "additional product options."
                )

            # ----------------------------------------------
            # Resolve configured pricing fields.
            #
            # products.json is the source of truth:
            #
            # PHONE_ID_STANDARD
            #     -> phone_id_standard
            #
            # PHONE_ID_CONTACT
            #     -> phone_id_contact
            #
            # etc.
            # ----------------------------------------------

            configured_subproducts = (
                product_config.get(
                    "subproducts",
                    []
                )
            )

            pricing_fields: dict[
                str,
                str
            ] = {}

            for subproduct_config in (
                configured_subproducts
            ):
                subproduct_id = str(
                    subproduct_config.get(
                        "product_id",
                        ""
                    )
                ).strip()

                pricing_field = str(
                    subproduct_config.get(
                        "pricing_field",
                        ""
                    )
                ).strip()

                if not subproduct_id:
                    raise ValueError(
                        "Phone ID Suite contains a "
                        "subproduct without a product_id."
                    )

                if not pricing_field:
                    raise ValueError(
                        f"Phone ID Suite subproduct "
                        f"'{subproduct_id}' has no "
                        f"pricing_field configured."
                    )

                pricing_fields[
                    subproduct_id
                ] = pricing_field

            # ----------------------------------------------
            # Read the complete Suite source once.
            #
            # We do NOT re-read the workbook separately
            # for every selected subproduct.
            # ----------------------------------------------

            pricing_data = (
                self._pricing_data_service
                .get_phone_id_suite_pricing()
            )

            # ----------------------------------------------
            # Generate independent output datasets.
            #
            # Countries whose price is None are omitted only
            # from the affected subproduct.
            # ----------------------------------------------

            return (
                self._generation_engine
                .generate_phone_id_suite_pricing(
                    pricing_data=pricing_data,
                    selected_subproducts=(
                        normalized_subproducts
                    ),
                    pricing_fields=(
                        pricing_fields
                    )
                )
            )

        # ==================================================
        # PHONE ID LIVE STATUS
        #
        # Live Status uses its own worksheet structure and
        # produces standard Voice-style generated rows.
        #
        # This branch MUST execute before the generic
        # base-pricing workflow.
        # ==================================================

        if product_id == "PHONE_ID_LIVE_STATUS":

            # ----------------------------------------------
            # No sender options.
            # ----------------------------------------------

            if normalized_sender_ids:
                raise ValueError(
                    "Phone ID Live Status does not support "
                    "sender options."
                )

            # ----------------------------------------------
            # No Local Country options.
            # ----------------------------------------------

            if normalized_local_countries:
                raise ValueError(
                    "Phone ID Live Status does not support "
                    "Local Countries."
                )

            # ----------------------------------------------
            # No generic choice options.
            # ----------------------------------------------

            if normalized_product_options:
                raise ValueError(
                    "Phone ID Live Status does not support "
                    "additional product options."
                )

            # ----------------------------------------------
            # No subproduct selections.
            # ----------------------------------------------

            if normalized_subproducts:
                raise ValueError(
                    "Phone ID Live Status does not support "
                    "subproduct selections."
                )

            pricing_data = (
                self._pricing_data_service
                .get_phone_id_live_status_pricing()
            )

            return (
                self._generation_engine
                .generate_phone_id_live_status_pricing(
                    pricing_data=pricing_data
                )
            )

        # ==================================================
        # STANDARD SMS-STYLE PRODUCTS
        #
        # Only products reaching this point use the generic
        # base pricing workflow.
        # ==================================================

        base_pricing_rows = (
            self._load_base_pricing_rows(
                product_config[
                    "base_worksheet"
                ]
            )
        )

        # ==================================================
        # SENDER OPTIONS
        # ==================================================

        sender_options_enabled = (
            product_config[
                "sender_options"
            ][
                "enabled"
            ]
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

        # ==================================================
        # LOCAL COUNTRY OPTIONS
        # ==================================================

        local_options_enabled = (
            product_config[
                "local_options"
            ][
                "enabled"
            ]
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

        # ==================================================
        # STANDARD GENERATION
        # ==================================================

        return self._generation_engine.generate_pricing(
            base_pricing_rows=base_pricing_rows,
            pricing_type=pricing_type,
            selected_sender_ids=(
                complete_sender_ids
            ),
            sender_override_prices=(
                sender_override_prices
            ),
            local_pricing_rows=(
                local_pricing_rows
            ),
            selected_local_countries=(
                normalized_local_countries
            )
        )

    def _generate_voice_verify_pricing(
        self,
        pricing_type: str,
        selected_product_options: dict[str, str]
    ) -> list[GeneratedVoicePricingRow]:
        """
        Generates Voice Verify pricing according to the selected
        Billing Type.

        PER_TRANSACTION:
            Reads Voice Verify Per Transaction.

        PER_MINUTE:
            Reads Voice Verify Per Minute.
        """

        billing_type = (
            selected_product_options[
                "billing_type"
            ]
        )

        if billing_type == "PER_TRANSACTION":
            pricing_rows = (
                self._pricing_data_service
                .get_voice_verify_transaction_pricing()
            )

        elif billing_type == "PER_MINUTE":
            pricing_rows = (
                self._pricing_data_service
                .get_voice_verify_minute_pricing()
            )

        else:
            raise ValueError(
                f"Unsupported Voice Verify billing type "
                f"'{billing_type}'."
            )

        return (
            self._generation_engine
            .generate_voice_base_rows(
                pricing_rows=pricing_rows,
                pricing_type=pricing_type
            )
        )

    def _generate_voice_api_pricing(
        self,
        product_config: dict[str, Any],
        pricing_type: str,
        selected_product_options: dict[str, str]
    ) -> list[GeneratedVoicePricingRow]:
        """
        Generates Voice API pricing using the selected Traffic
        Type and Number Type.

        Internal Number Type IDs from the GUI/configuration are
        translated to the exact worksheet values before filtering.
        """

        traffic_type = (
            selected_product_options[
                "traffic_type"
            ]
        )

        number_type_id = (
            selected_product_options[
                "number_type"
            ]
        )

        worksheet_number_type = (
            self._get_product_option_worksheet_value(
                product_config=product_config,
                option_id="number_type",
                selected_value=number_type_id
            )
        )

        pricing_rows = (
            self._pricing_data_service
            .get_voice_api_pricing()
        )

        return (
            self._generation_engine
            .generate_voice_api_rows(
                pricing_rows=pricing_rows,
                pricing_type=pricing_type,
                traffic_type=traffic_type,
                number_type=worksheet_number_type
            )
        )

    def _generate_voice_verify_tts_pricing(
        self,
        pricing_type: str,
        selected_product_options: dict[str, str]
    ) -> list[GeneratedVoicePricingRow]:
        """
        Generates Voice Verify + TTS pricing according to the
        selected Traffic Type.

        ONE_WAY:
            Outbound Voice pricing only.

        TWO_WAY:
            Outbound and inbound pricing using the TTS-specific
            inbound fallback rules implemented by GenerationEngine.
        """

        traffic_type = (
            selected_product_options[
                "traffic_type"
            ]
        )

        pricing_rows = (
            self._pricing_data_service
            .get_voice_verify_tts_pricing()
        )

        return (
            self._generation_engine
            .generate_voice_verify_tts_rows(
                pricing_rows=pricing_rows,
                pricing_type=pricing_type,
                traffic_type=traffic_type
            )
        )

    def _generate_toll_free_voice_pricing(
        self,
        pricing_type: str
    ) -> list[GeneratedVoicePricingRow]:
        """
        Generates Toll-Free Voice pricing.

        Toll-Free Voice is inherently 2-Way and therefore does
        not require a Traffic Type product option.
        """

        pricing_rows = (
            self._pricing_data_service
            .get_toll_free_voice_pricing()
        )

        return (
            self._generation_engine
            .generate_toll_free_voice_rows(
                pricing_rows=pricing_rows,
                pricing_type=pricing_type
            )
        )

    def _generate_mobile_sms_voice_pricing(
        self,
        pricing_type: str,
        selected_product_options: dict[str, str]
    ) -> GeneratedMobilePricing:
        """
        Generates Mobile (SMS and Voice) pricing according to the
        selected Traffic Type.

        ONE_WAY:
            SMS Outbound + Voice

        TWO_WAY:
            SMS Outbound + SMS Inbound + Voice

        Unsupported source prices remain output-specific:
            - SMS unsupported does not remove Voice.
            - Voice unsupported does not remove SMS.
            - No All Others fallback is applied to countries.
        """

        traffic_type = (
            selected_product_options[
                "traffic_type"
            ]
        )

        pricing_rows = (
            self._pricing_data_service
            .get_mobile_sms_voice_pricing()
        )

        return (
            self._generation_engine
            .generate_mobile_sms_voice_rows(
                pricing_rows=pricing_rows,
                pricing_type=pricing_type,
                traffic_type=traffic_type
            )
        )

    def _generate_whatsapp_pricing(
        self,
        pricing_type: str
    ) -> list[GeneratedPricingRow]:
        """
        Loads the universal WhatsApp Other source pricing and
        generates the single standard All Others output row.
        """

        whatsapp_pricing = (
            self._pricing_data_service
            .get_whatsapp_pricing()
        )

        return (
            self._generation_engine
            .generate_whatsapp_rows(
                whatsapp_pricing=whatsapp_pricing,
                pricing_type=pricing_type
            )
        )

    def _generate_viber_pricing(
        self,
        pricing_type: str
    ) -> list[GeneratedViberPricingRow]:
        """
        Loads Viber source pricing and applies the selected
        Baseline or Enterprise pricing calculation.
        """

        viber_pricing = (
            self._pricing_data_service
            .get_viber_pricing()
        )

        return (
            self._generation_engine
            .generate_viber_rows(
                viber_pricing=viber_pricing,
                pricing_type=pricing_type
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
    def _get_product_option_worksheet_value(
        product_config: dict[str, Any],
        option_id: str,
        selected_value: str
    ) -> str:
        """
        Resolves an internal product-option value ID to the exact
        value expected in the source workbook.

        Example:

            US_CLOUD_NUMBERS
            -> US Cloud numbers
        """

        for option_config in product_config.get(
            "choice_options",
            []
        ):
            if (
                option_config.get(
                    "option_id"
                )
                != option_id
            ):
                continue

            for value_config in option_config.get(
                "values",
                []
            ):
                if (
                    value_config.get(
                        "value_id"
                    )
                    != selected_value
                ):
                    continue

                worksheet_value = str(
                    value_config.get(
                        "worksheet_value",
                        ""
                    )
                ).strip()

                if not worksheet_value:
                    raise ValueError(
                        f"Product option '{option_id}' value "
                        f"'{selected_value}' does not define "
                        f"a worksheet_value."
                    )

                return worksheet_value

        raise ValueError(
            f"Could not resolve worksheet value for "
            f"product option '{option_id}' value "
            f"'{selected_value}'."
        )

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
    def _validate_product_options(
        product_config: dict[str, Any],
        selected_product_options: dict[str, str]
    ) -> None:
        """
        Validates generic product-specific selections against the
        product's choice_options configuration.

        Validation covers:
            - unsupported option IDs;
            - missing required selections;
            - unsupported option values.
        """

        configured_options = (
            product_config.get(
                "choice_options",
                []
            )
        )

        options_by_id: dict[
            str,
            dict[str, Any]
        ] = {}

        for option_config in configured_options:
            option_id = str(
                option_config.get(
                    "option_id",
                    ""
                )
            ).strip()

            if not option_id:
                raise ValueError(
                    f"Product "
                    f"'{product_config['product_id']}' "
                    f"contains a choice option without an "
                    f"option_id."
                )

            if option_id in options_by_id:
                raise ValueError(
                    f"Product "
                    f"'{product_config['product_id']}' "
                    f"contains duplicate choice option "
                    f"'{option_id}'."
                )

            options_by_id[
                option_id
            ] = option_config

        unsupported_option_ids = (
            selected_product_options.keys()
            - options_by_id.keys()
        )

        if unsupported_option_ids:
            unsupported_option_list = ", ".join(
                sorted(
                    unsupported_option_ids
                )
            )

            raise ValueError(
                f"Product "
                f"'{product_config['product_id']}' "
                f"does not support product option(s): "
                f"{unsupported_option_list}."
            )

        for option_id, option_config in (
            options_by_id.items()
        ):
            selected_value = (
                selected_product_options.get(
                    option_id,
                    ""
                )
            )

            is_required = bool(
                option_config.get(
                    "required",
                    False
                )
            )

            if (
                is_required
                and not selected_value
            ):
                raise ValueError(
                    f"Required product option "
                    f"'{option_id}' was not selected for "
                    f"product "
                    f"'{product_config['product_id']}'."
                )

            if not selected_value:
                continue

            valid_value_ids = {
                str(
                    value_config.get(
                        "value_id",
                        ""
                    )
                ).strip()
                for value_config
                in option_config.get(
                    "values",
                    []
                )
            }

            if (
                selected_value
                not in valid_value_ids
            ):
                raise ValueError(
                    f"Product option '{option_id}' value "
                    f"'{selected_value}' is not supported by "
                    f"product "
                    f"'{product_config['product_id']}'."
                )

    def _validate_product_pricing_type(
        self,
        product_config: dict[str, Any],
        pricing_type: str | None
    ) -> None:
        """
        Validates Pricing Type according to the selected product.

        Products with configured pricing types:
            A Pricing Type is mandatory and must match one of
            the configured values.

        Products with no configured pricing types:
            Pricing Type must not be supplied.
        """

        supported_pricing_types = (
            product_config.get(
                "supported_pricing_types",
                []
            )
        )

        product_id = (
            product_config.get(
                "product_id",
                "UNKNOWN"
            )
        )

        # ==================================================
        # SINGLE-PRICING PRODUCT
        #
        # Example:
        # Phone ID Suite
        # Phone ID Live Status
        # ==================================================

        if not supported_pricing_types:

            if pricing_type is None:
                return

            normalized_pricing_type = (
                str(
                    pricing_type
                )
                .strip()
            )

            if not normalized_pricing_type:
                return

            raise ValueError(
                f"Product '{product_id}' does not "
                f"support a Pricing Type."
            )

        # ==================================================
        # PRODUCT REQUIRING PRICING TYPE
        # ==================================================

        if pricing_type is None:
            raise ValueError(
                f"Product '{product_id}' requires "
                f"a Pricing Type."
            )

        normalized_pricing_type = (
            str(
                pricing_type
            )
            .strip()
        )

        if not normalized_pricing_type:
            raise ValueError(
                f"Product '{product_id}' requires "
                f"a Pricing Type."
            )

        if (
            normalized_pricing_type
            not in supported_pricing_types
        ):
            supported_values = (
                ", ".join(
                    supported_pricing_types
                )
            )

            raise ValueError(
                f"Pricing Type "
                f"'{normalized_pricing_type}' "
                f"is not supported for product "
                f"'{product_id}'. "
                f"Supported values: "
                f"{supported_values}."
            )

    def _validate_selected_subproducts(
        self,
        product_config: dict[str, Any],
        selected_subproducts: (
            list[str] | None
        )
    ) -> None:
        """
        Validates optional subproduct selections.

        Normal products:
            Must not receive any subproduct selections.

        Products with configured subproducts:
            - only configured subproducts may be selected;
            - duplicate selections are rejected;
            - every required subproduct must be selected.

        Phone ID Suite uses this to guarantee that
        Phone ID Standard can never be omitted.
        """

        product_id = (
            product_config.get(
                "product_id",
                "UNKNOWN"
            )
        )

        configured_subproducts = (
            product_config.get(
                "subproducts",
                []
            )
        )

        normalized_selected = []

        for selected_subproduct in (
            selected_subproducts or []
        ):
            normalized_value = (
                str(
                    selected_subproduct
                )
                .strip()
            )

            if not normalized_value:
                raise ValueError(
                    f"Product '{product_id}' received "
                    f"an empty subproduct selection."
                )

            normalized_selected.append(
                normalized_value
            )

        # ==================================================
        # PRODUCT DOES NOT SUPPORT SUBPRODUCTS
        # ==================================================

        if not configured_subproducts:

            if normalized_selected:
                selected_values = ", ".join(
                    normalized_selected
                )

                raise ValueError(
                    f"Product '{product_id}' does not "
                    f"support subproduct selections: "
                    f"{selected_values}."
                )

            return

        # ==================================================
        # DUPLICATES
        # ==================================================

        if (
            len(normalized_selected)
            != len(
                set(
                    normalized_selected
                )
            )
        ):
            raise ValueError(
                f"Product '{product_id}' contains "
                f"duplicate subproduct selections."
            )

        # ==================================================
        # VALID CONFIGURED IDS
        # ==================================================

        configured_ids = {
            str(
                subproduct[
                    "product_id"
                ]
            ).strip()
            for subproduct
            in configured_subproducts
        }

        unsupported_ids = [
            selected_id
            for selected_id
            in normalized_selected
            if selected_id
            not in configured_ids
        ]

        if unsupported_ids:
            unsupported_values = ", ".join(
                unsupported_ids
            )

            raise ValueError(
                f"Product '{product_id}' does not "
                f"support subproduct(s): "
                f"{unsupported_values}."
            )

        # ==================================================
        # REQUIRED SUBPRODUCTS
        #
        # For Phone ID Suite this is:
        #
        #     PHONE_ID_STANDARD
        # ==================================================

        required_ids = {
            str(
                subproduct[
                    "product_id"
                ]
            ).strip()
            for subproduct
            in configured_subproducts
            if subproduct.get(
                "required",
                False
            )
        }

        selected_ids = set(
            normalized_selected
        )

        missing_required = sorted(
            required_ids
            - selected_ids
        )

        if missing_required:
            missing_values = ", ".join(
                missing_required
            )

            raise ValueError(
                f"Product '{product_id}' requires "
                f"subproduct(s): "
                f"{missing_values}."
            )

        