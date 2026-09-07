from decimal import Decimal, ROUND_HALF_UP

from app.models.generated_pricing_row import GeneratedPricingRow
from app.models.pricing_row import PricingRow
from app.models.sender_override_price import (
    SenderOverridePrice
)
from app.models.generated_voice_pricing_row import (
    GeneratedVoicePricingRow
)
from app.models.voice_pricing_row import VoicePricingRow
from app.models.generated_mobile_pricing import (
    GeneratedMobilePricing
)
from app.models.mobile_pricing_row import (
    MobilePricingRow
)
from app.models.whatsapp_pricing import (
    WhatsAppPricing
)
from app.models.viber_pricing_data import (
    ViberPricingData
)
from app.models.generated_viber_pricing_row import (
    GeneratedViberPricingRow
)
from app.models.generated_phone_id_suite_pricing import (
    GeneratedPhoneIdSuitePricing
)

from app.models.generated_pricing_row import (
    GeneratedPricingRow
)

from app.models.phone_id_suite_pricing_data import (
    PhoneIdSuitePricingData
)
from app.models.generated_voice_pricing_row import (
    GeneratedVoicePricingRow
)

from app.models.phone_id_live_status_pricing_data import (
    PhoneIdLiveStatusPricingData
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

    def generate_voice_base_rows(
        self,
        pricing_rows: list[VoicePricingRow],
        pricing_type: str
    ) -> list[GeneratedVoicePricingRow]:
        """
        Converts source Voice pricing rows into generated Voice rows
        using the selected Pricing Type.

        No product-specific fallback or filtering is applied here.
        This method only selects Baseline or Enterprise pricing.

        Args:
            pricing_rows:
                Voice source rows extracted from the workbook.

            pricing_type:
                Baseline or Enterprise.

        Returns:
            Generated Voice rows in original workbook order.

        Raises:
            ValueError:
                If Pricing Type is unsupported or no source rows
                are supplied.
        """

        self._validate_pricing_type(
            pricing_type
        )

        if not pricing_rows:
            raise ValueError(
                "Voice pricing rows cannot be empty."
            )

        generated_rows: list[
            GeneratedVoicePricingRow
        ] = []

        for pricing_row in pricing_rows:
            if pricing_type == "Baseline":
                mobile_price = (
                    pricing_row.baseline_mobile_price
                )

                landline_price = (
                    pricing_row.baseline_landline_price
                )

                inbound_price = (
                    pricing_row.baseline_inbound_price
                )

            else:
                mobile_price = (
                    pricing_row.enterprise_mobile_price
                )

                landline_price = (
                    pricing_row.enterprise_landline_price
                )

                inbound_price = (
                    pricing_row.enterprise_inbound_price
                )

            country = pricing_row.country
            iso2 = pricing_row.iso2

            if (
                pricing_row.country.casefold()
                in {
                    "all others",
                    "all other countries"
                }
            ):
                country = ""
                iso2 = ""

            generated_rows.append(
                GeneratedVoicePricingRow(
                    country=country,
                    iso2=iso2,
                    landline_price=landline_price,
                    mobile_price=mobile_price,
                    inbound_price=inbound_price
                )
            )

        return generated_rows

    def generate_voice_api_rows(
        self,
        pricing_rows: list[VoicePricingRow],
        pricing_type: str,
        traffic_type: str,
        number_type: str
    ) -> list[GeneratedVoicePricingRow]:
        """
        Generates final Voice API pricing rows.

        Processing:
            1. Validate Pricing Type.
            2. Select the requested Number Type.
            3. Always retain the All Others row.
            4. Select Baseline or Enterprise pricing.
            5. For 1-Way, inbound pricing is not used.
            6. For 2-Way, missing inbound pricing falls back to
            the selected Pricing Type's All Others inbound price.

        Args:
            pricing_rows:
                Voice API source rows.

            pricing_type:
                Baseline or Enterprise.

            traffic_type:
                ONE_WAY or TWO_WAY.

            number_type:
                Source-workbook Number Type value, for example
                'US Cloud numbers' or 'Global Mobile Numbers'.

        Returns:
            Final Voice rows in source workbook order.

        Raises:
            ValueError:
                If selections or source data are invalid.
        """

        self._validate_pricing_type(
            pricing_type
        )

        if not pricing_rows:
            raise ValueError(
                "Voice API pricing rows cannot be empty."
            )

        if traffic_type not in {
            "ONE_WAY",
            "TWO_WAY"
        }:
            raise ValueError(
                f"Unsupported Voice traffic type "
                f"'{traffic_type}'."
            )

        normalized_number_type = (
            number_type.strip()
        )

        if not normalized_number_type:
            raise ValueError(
                "Voice Number Type cannot be empty."
            )

        all_others_rows = [
            row
            for row in pricing_rows
            if self._is_voice_all_others_row(
                row
            )
        ]

        if len(all_others_rows) != 1:
            raise ValueError(
                "Voice API pricing must contain exactly one "
                "All Others row."
            )

        all_others_source_row = (
            all_others_rows[0]
        )

        selected_source_rows: list[
            VoicePricingRow
        ] = [
            all_others_source_row
        ]

        for pricing_row in pricing_rows:
            if self._is_voice_all_others_row(
                pricing_row
            ):
                continue

            source_number_type = (
                pricing_row.number_type or ""
            ).strip()

            if (
                source_number_type.casefold()
                != normalized_number_type.casefold()
            ):
                continue

            selected_source_rows.append(
                pricing_row
            )

        if len(selected_source_rows) == 1:
            raise ValueError(
                f"No Voice API country rows were found for "
                f"Number Type '{normalized_number_type}'."
            )

        self._validate_unique_voice_iso2(
            selected_source_rows[
                1:
            ]
        )

        generated_rows = (
            self.generate_voice_base_rows(
                pricing_rows=selected_source_rows,
                pricing_type=pricing_type
            )
        )

        if traffic_type == "ONE_WAY":
            return [
                GeneratedVoicePricingRow(
                    country=row.country,
                    iso2=row.iso2,
                    landline_price=(
                        row.landline_price
                    ),
                    mobile_price=(
                        row.mobile_price
                    ),
                    inbound_price=None
                )
                for row in generated_rows
            ]

        all_others_inbound_price = (
            generated_rows[0].inbound_price
        )

        if all_others_inbound_price is None:
            raise ValueError(
                "Voice API All Others inbound pricing "
                f"is missing for Pricing Type "
                f"'{pricing_type}'."
            )

        final_rows: list[
            GeneratedVoicePricingRow
        ] = []

        for generated_row in generated_rows:
            inbound_price = (
                generated_row.inbound_price
            )

            if inbound_price is None:
                inbound_price = (
                    all_others_inbound_price
                )

            final_rows.append(
                GeneratedVoicePricingRow(
                    country=generated_row.country,
                    iso2=generated_row.iso2,
                    landline_price=(
                        generated_row.landline_price
                    ),
                    mobile_price=(
                        generated_row.mobile_price
                    ),
                    inbound_price=inbound_price
                )
            )

        return final_rows

    def generate_voice_verify_tts_rows(
        self,
        pricing_rows: list[VoicePricingRow],
        pricing_type: str,
        traffic_type: str
    ) -> list[GeneratedVoicePricingRow]:
        """
        Generates final Voice Verify + TTS pricing.

        ONE_WAY:
            Uses selected outbound Landline and Mobile prices.
            Inbound is not included.

        TWO_WAY:
            Uses selected outbound prices and inbound pricing.

            If All Others inbound is missing:
                use All Others Landline as the effective
                All Others inbound price.

            If a country's inbound price is missing:
                use the effective All Others inbound price.
        """

        self._validate_pricing_type(
            pricing_type
        )

        if not pricing_rows:
            raise ValueError(
                "Voice Verify + TTS pricing rows cannot be empty."
            )

        if traffic_type not in {
            "ONE_WAY",
            "TWO_WAY"
        }:
            raise ValueError(
                f"Unsupported Voice Verify + TTS traffic type "
                f"'{traffic_type}'."
            )

        all_others_rows = [
            row
            for row in pricing_rows
            if self._is_voice_all_others_row(
                row
            )
        ]

        if len(all_others_rows) != 1:
            raise ValueError(
                "Voice Verify + TTS pricing must contain "
                "exactly one All Others row."
            )

        generated_rows = (
            self.generate_voice_base_rows(
                pricing_rows=pricing_rows,
                pricing_type=pricing_type
            )
        )

        if traffic_type == "ONE_WAY":
            return [
                GeneratedVoicePricingRow(
                    country=row.country,
                    iso2=row.iso2,
                    landline_price=row.landline_price,
                    mobile_price=row.mobile_price,
                    inbound_price=None
                )
                for row in generated_rows
            ]

        all_others_generated = (
            generated_rows[0]
        )

        effective_all_others_inbound = (
            all_others_generated.inbound_price
        )

        if effective_all_others_inbound is None:
            effective_all_others_inbound = (
                all_others_generated.landline_price
            )

        final_rows: list[
            GeneratedVoicePricingRow
        ] = []

        for generated_row in generated_rows:
            inbound_price = (
                generated_row.inbound_price
            )

            if inbound_price is None:
                inbound_price = (
                    effective_all_others_inbound
                )

            final_rows.append(
                GeneratedVoicePricingRow(
                    country=generated_row.country,
                    iso2=generated_row.iso2,
                    landline_price=(
                        generated_row.landline_price
                    ),
                    mobile_price=(
                        generated_row.mobile_price
                    ),
                    inbound_price=inbound_price
                )
            )

        return final_rows

    def generate_toll_free_voice_rows(
        self,
        pricing_rows: list[VoicePricingRow],
        pricing_type: str
    ) -> list[GeneratedVoicePricingRow]:
        """
        Generates final Toll-Free Voice pricing.

        Toll-Free Voice is always a 2-Way product, so every
        generated row must contain:

            - Landline outbound price
            - Mobile outbound price
            - Inbound price

        No fallback is applied. Missing inbound pricing is treated
        as invalid source data.
        """

        self._validate_pricing_type(
            pricing_type
        )

        if not pricing_rows:
            raise ValueError(
                "Toll-Free Voice pricing rows cannot be empty."
            )

        generated_rows = (
            self.generate_voice_base_rows(
                pricing_rows=pricing_rows,
                pricing_type=pricing_type
            )
        )

        for generated_row in generated_rows:
            if generated_row.inbound_price is None:
                destination_name = (
                    generated_row.country
                    or "All Others"
                )

                raise ValueError(
                    f"Toll-Free Voice destination "
                    f"'{destination_name}' does not contain "
                    f"inbound pricing."
                )

        return generated_rows

    def generate_mobile_sms_voice_rows(
        self,
        pricing_rows: list[MobilePricingRow],
        pricing_type: str,
        traffic_type: str
    ) -> GeneratedMobilePricing:
        """
        Generates Mobile (SMS and Voice) pricing outputs.

        Filtering is performed independently per output.

        ONE_WAY:
            - SMS Outbound:
                country included when SMS Outbound exists.

            - Voice:
                country included when Voice Outbound exists.

        TWO_WAY:
            - SMS Outbound:
                country included when SMS Outbound exists.

            - SMS Inbound:
                country included when SMS Inbound exists.

            - Voice:
                country included only when BOTH Voice Outbound
                and Voice Inbound exist.

        Unsupported Mobile values are represented by None and
        cause the country to be omitted from the relevant output.
        No All Others fallback is applied.
        """

        self._validate_pricing_type(
            pricing_type
        )

        if not pricing_rows:
            raise ValueError(
                "Mobile pricing rows cannot be empty."
            )

        if traffic_type not in {
            "ONE_WAY",
            "TWO_WAY"
        }:
            raise ValueError(
                f"Unsupported Mobile traffic type "
                f"'{traffic_type}'."
            )

        all_others_rows = [
            row
            for row in pricing_rows
            if (
                not row.country.strip()
                and not row.iso2.strip()
            )
        ]

        if len(all_others_rows) != 1:
            raise ValueError(
                "Mobile pricing must contain exactly one "
                "blank All Others row."
            )

        all_others = (
            all_others_rows[0]
        )

        country_rows = [
            row
            for row in pricing_rows
            if row is not all_others
        ]

        self._validate_unique_mobile_iso2(
            country_rows
        )

        (
            all_others_sms_outbound,
            all_others_sms_inbound,
            all_others_voice_outbound,
            all_others_voice_inbound
        ) = self._select_mobile_prices(
            pricing_row=all_others,
            pricing_type=pricing_type
        )

        if all_others_sms_outbound is None:
            raise ValueError(
                "Mobile All Others SMS Outbound pricing "
                "cannot be missing."
            )

        if all_others_voice_outbound is None:
            raise ValueError(
                "Mobile All Others Voice Outbound pricing "
                "cannot be missing."
            )

        if (
            traffic_type == "TWO_WAY"
            and all_others_sms_inbound is None
        ):
            raise ValueError(
                "Mobile All Others SMS Inbound pricing "
                "cannot be missing for 2-Way generation."
            )

        if (
            traffic_type == "TWO_WAY"
            and all_others_voice_inbound is None
        ):
            raise ValueError(
                "Mobile All Others Voice Inbound pricing "
                "cannot be missing for 2-Way generation."
            )

        sms_outbound_rows: list[
            GeneratedPricingRow
        ] = [
            GeneratedPricingRow(
                country="",
                iso2="",
                price=all_others_sms_outbound
            )
        ]

        sms_inbound_rows: (
            list[GeneratedPricingRow]
            | None
        )

        if traffic_type == "TWO_WAY":
            sms_inbound_rows = [
                GeneratedPricingRow(
                    country="",
                    iso2="",
                    price=all_others_sms_inbound
                )
            ]

        else:
            sms_inbound_rows = None

        voice_rows: list[
            GeneratedVoicePricingRow
        ] = [
            GeneratedVoicePricingRow(
                country="",
                iso2="",
                landline_price=(
                    all_others_voice_outbound
                ),
                mobile_price=(
                    all_others_voice_outbound
                ),
                inbound_price=(
                    all_others_voice_inbound
                    if traffic_type == "TWO_WAY"
                    else None
                )
            )
        ]

        for pricing_row in country_rows:
            (
                sms_outbound_price,
                sms_inbound_price,
                voice_outbound_price,
                voice_inbound_price
            ) = self._select_mobile_prices(
                pricing_row=pricing_row,
                pricing_type=pricing_type
            )

            if sms_outbound_price is not None:
                sms_outbound_rows.append(
                    GeneratedPricingRow(
                        country=pricing_row.country,
                        iso2=pricing_row.iso2,
                        price=sms_outbound_price
                    )
                )

            if (
                traffic_type == "TWO_WAY"
                and sms_inbound_price is not None
            ):
                if sms_inbound_rows is None:
                    raise RuntimeError(
                        "Mobile SMS Inbound rows were not "
                        "initialized."
                    )

                sms_inbound_rows.append(
                    GeneratedPricingRow(
                        country=pricing_row.country,
                        iso2=pricing_row.iso2,
                        price=sms_inbound_price
                    )
                )

            if traffic_type == "ONE_WAY":
                if voice_outbound_price is not None:
                    voice_rows.append(
                        GeneratedVoicePricingRow(
                            country=pricing_row.country,
                            iso2=pricing_row.iso2,
                            landline_price=(
                                voice_outbound_price
                            ),
                            mobile_price=(
                                voice_outbound_price
                            ),
                            inbound_price=None
                        )
                    )

            else:
                if (
                    voice_outbound_price is not None
                    and voice_inbound_price is not None
                ):
                    voice_rows.append(
                        GeneratedVoicePricingRow(
                            country=pricing_row.country,
                            iso2=pricing_row.iso2,
                            landline_price=(
                                voice_outbound_price
                            ),
                            mobile_price=(
                                voice_outbound_price
                            ),
                            inbound_price=(
                                voice_inbound_price
                            )
                        )
                    )

        return GeneratedMobilePricing(
            sms_outbound_rows=sms_outbound_rows,
            sms_inbound_rows=sms_inbound_rows,
            voice_rows=voice_rows
        )

    def generate_whatsapp_rows(
        self,
        whatsapp_pricing: WhatsAppPricing,
        pricing_type: str
    ) -> list[GeneratedPricingRow]:
        """
        Converts the universal WhatsApp Other price into the
        standard generated All Others row.

        WhatsApp does not generate individual country rows because
        every country uses the same Telesign fee.
        """

        self._validate_pricing_type(
            pricing_type
        )

        if not isinstance(
            whatsapp_pricing,
            WhatsAppPricing
        ):
            raise ValueError(
                "WhatsApp pricing must be a WhatsAppPricing object."
            )

        if pricing_type == "Baseline":
            selected_price = (
                whatsapp_pricing.baseline_price
            )

        else:
            selected_price = (
                whatsapp_pricing.enterprise_price
            )

        return [
            GeneratedPricingRow(
                country="",
                iso2="",
                price=selected_price
            )
        ]

    def generate_viber_rows(
        self,
        viber_pricing: ViberPricingData,
        pricing_type: str
    ) -> list[GeneratedViberPricingRow]:
        """
        Generates final Viber pricing.

        All Others:
            Uses the displayed source prices directly.

        Individual countries:
            Price = Cost / (1 - selected DM%)

            Baseline:
                DM% baseline

            Enterprise:
                DM% mid-market

        Country prices are rounded to a maximum calculation
        precision of four decimal places using ROUND_HALF_UP.
        """

        self._validate_pricing_type(
            pricing_type
        )

        if not isinstance(
            viber_pricing,
            ViberPricingData
        ):
            raise ValueError(
                "Viber pricing must be a ViberPricingData object."
            )

        generated_rows: list[
            GeneratedViberPricingRow
        ] = []

        # ==================================================
        # ALL OTHERS
        #
        # These prices come directly from displayed source
        # pricing C:F and are NOT recalculated.
        # ==================================================

        generated_rows.append(
            GeneratedViberPricingRow(
                country="",
                iso2="",

                transactional_otp_price=(
                    viber_pricing
                    .all_other
                    .transactional_otp_price
                ),

                promotional_price=(
                    viber_pricing
                    .all_other
                    .promotional_price
                ),

                international_price=(
                    viber_pricing
                    .all_other
                    .international_price
                ),

                session_chat_price=(
                    viber_pricing
                    .all_other
                    .session_chat_price
                )
            )
        )

        # ==================================================
        # INDIVIDUAL COUNTRIES
        # ==================================================

        for source_row in (
            viber_pricing.countries
        ):
            if pricing_type == "Baseline":
                selected_dm = (
                    source_row.baseline_dm
                )

            else:
                selected_dm = (
                    source_row.enterprise_dm
                )

            transactional_otp_price = (
                self._calculate_viber_price(
                    cost=(
                        source_row
                        .transactional_otp_cost
                    ),
                    dm=selected_dm,
                    country=source_row.country,
                    price_name="Transactional/OTP"
                )
            )

            promotional_price = (
                self._calculate_viber_price(
                    cost=(
                        source_row
                        .promotional_cost
                    ),
                    dm=selected_dm,
                    country=source_row.country,
                    price_name="Promotional"
                )
            )

            session_chat_price = (
                self._calculate_viber_price(
                    cost=(
                        source_row
                        .session_chat_cost
                    ),
                    dm=selected_dm,
                    country=source_row.country,
                    price_name="Session Chat"
                )
            )

            international_price = (
                self._calculate_viber_price(
                    cost=(
                        source_row
                        .international_cost
                    ),
                    dm=selected_dm,
                    country=source_row.country,
                    price_name="International"
                )
            )

            generated_rows.append(
                GeneratedViberPricingRow(
                    country=source_row.country,
                    iso2=source_row.iso2,

                    transactional_otp_price=(
                        transactional_otp_price
                    ),

                    promotional_price=(
                        promotional_price
                    ),

                    international_price=(
                        international_price
                    ),

                    session_chat_price=(
                        session_chat_price
                    )
                )
            )

        return generated_rows

    def generate_phone_id_suite_pricing(
        self,
        pricing_data: PhoneIdSuitePricingData,
        selected_subproducts: list[str],
        pricing_fields: dict[str, str]
    ) -> GeneratedPhoneIdSuitePricing:
        """
        Generates Phone ID Suite pricing for the selected
        subproducts.

        Each selected subproduct produces its own independent
        list of GeneratedPricingRow objects.

        A country is included only when that specific
        subproduct has a numeric price.

        None means unavailable and the country is omitted from
        that subproduct only.

        All Other Countries is always included because the
        Phone ID Suite source contract requires a numeric
        All Others price for every subproduct.
        """

        if not selected_subproducts:
            raise ValueError(
                "At least one Phone ID Suite subproduct "
                "must be selected."
            )

        if not pricing_fields:
            raise ValueError(
                "Phone ID Suite pricing field mapping "
                "cannot be empty."
            )

        rows_by_subproduct: dict[
            str,
            list[GeneratedPricingRow]
        ] = {}

        # ==================================================
        # GENERATE EACH SELECTED SUBPRODUCT INDEPENDENTLY
        # ==================================================

        for subproduct_id in (
            selected_subproducts
        ):
            if (
                subproduct_id
                not in pricing_fields
            ):
                raise ValueError(
                    f"No pricing field is configured for "
                    f"Phone ID Suite subproduct "
                    f"'{subproduct_id}'."
                )

            pricing_field = (
                pricing_fields[
                    subproduct_id
                ]
            )

            if not hasattr(
                pricing_data.all_other,
                pricing_field
            ):
                raise ValueError(
                    f"Phone ID Suite pricing field "
                    f"'{pricing_field}' does not exist "
                    f"on the source pricing model."
                )

            generated_rows: list[
                GeneratedPricingRow
            ] = []

            # ==================================================
            # ALL OTHER COUNTRIES
            #
            # Existing SMS-style output represents All Others
            # using a blank Country and ISO2.
            # ==================================================

            all_other_price = getattr(
                pricing_data.all_other,
                pricing_field
            )

            if all_other_price is None:
                raise ValueError(
                    f"All other countries has no numeric "
                    f"price for Phone ID Suite subproduct "
                    f"'{subproduct_id}'."
                )

            generated_rows.append(
                GeneratedPricingRow(
                    country="",
                    iso2="",
                    price=all_other_price
                )
            )

            # ==================================================
            # COUNTRY PRICING
            #
            # None means unavailable for this subproduct only.
            # ==================================================

            for source_row in (
                pricing_data.countries
            ):
                price = getattr(
                    source_row,
                    pricing_field
                )

                if price is None:
                    continue

                generated_rows.append(
                    GeneratedPricingRow(
                        country=(
                            source_row.country
                        ),
                        iso2=(
                            source_row.iso2
                        ),
                        price=price
                    )
                )

            rows_by_subproduct[
                subproduct_id
            ] = generated_rows

        return GeneratedPhoneIdSuitePricing(
            rows_by_subproduct=(
                rows_by_subproduct
            )
        )

    def generate_phone_id_live_status_pricing(
        self,
        pricing_data: PhoneIdLiveStatusPricingData
    ) -> list[GeneratedVoicePricingRow]:
        """
        Generates Phone ID Live Status pricing.

        Phone ID Live Status uses the same generated row
        structure as Voice pricing:

            landline_price
            mobile_price

        All Other Countries is represented in generated output
        by a blank Country and ISO2.
        """

        generated_rows: list[
            GeneratedVoicePricingRow
        ] = []

        # ==================================================
        # ALL OTHER COUNTRIES
        # ==================================================

        generated_rows.append(
            GeneratedVoicePricingRow(
                country="",
                iso2="",
                landline_price=(
                    pricing_data
                    .all_other
                    .landline_price
                ),
                mobile_price=(
                    pricing_data
                    .all_other
                    .mobile_price
                ),
                inbound_price=None
            )
        )

        # ==================================================
        # COUNTRY PRICING
        # ==================================================

        for source_row in (
            pricing_data.countries
        ):
            generated_rows.append(
                GeneratedVoicePricingRow(
                    country=(
                        source_row.country
                    ),
                    iso2=(
                        source_row.iso2
                    ),
                    landline_price=(
                        source_row
                        .landline_price
                    ),
                    mobile_price=(
                        source_row
                        .mobile_price
                    ),
                    inbound_price=None
                )
            )

        if not generated_rows:
            raise RuntimeError(
                "Phone ID Live Status generation "
                "returned no pricing rows."
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

    @staticmethod
    def _calculate_viber_price(
        cost: Decimal,
        dm: Decimal,
        country: str,
        price_name: str
    ) -> Decimal:
        """
        Calculates one Viber country price.

            Price = Cost / (1 - DM%)

        Excel percentage cells are expected to be represented
        as decimal fractions:

            20% -> Decimal("0.20")

        The result is rounded to four decimal places using
        ROUND_HALF_UP.
        """

        if not cost.is_finite():
            raise ValueError(
                f"Viber {price_name} cost for "
                f"'{country}' must be finite."
            )

        if cost < Decimal("0"):
            raise ValueError(
                f"Viber {price_name} cost for "
                f"'{country}' cannot be negative."
            )

        if not dm.is_finite():
            raise ValueError(
                f"Viber DM% for '{country}' must be finite."
            )

        if (
            dm < Decimal("0")
            or dm >= Decimal("1")
        ):
            raise ValueError(
                f"Viber DM% for '{country}' must be "
                f"greater than or equal to 0 and less than 1. "
                f"Received: {dm}."
            )

        price = (
            cost
            / (
                Decimal("1")
                - dm
            )
        )

        return price.quantize(
            Decimal("0.0001"),
            rounding=ROUND_HALF_UP
        )

    @staticmethod
    def _is_voice_all_others_row(
        pricing_row: VoicePricingRow
    ) -> bool:
        """
        Returns True when a Voice source row represents
        All Others.
        """

        normalized_country = (
            pricing_row.country
            .strip()
            .casefold()
        )

        return normalized_country in {
            "all others",
            "all other countries"
        }

    @staticmethod
    def _validate_unique_voice_iso2(
        pricing_rows: list[VoicePricingRow]
    ) -> None:
        """
        Ensures that the selected Voice Number Type contains no
        duplicate ISO2 values.

        Duplicate ISO2 values are valid in the raw Voice API
        worksheet because different Number Types may coexist.
        After one Number Type has been selected, however, each
        destination must occur only once.
        """

        seen_iso2_codes: set[str] = set()

        for pricing_row in pricing_rows:
            normalized_iso2 = (
                pricing_row.iso2
                .strip()
                .upper()
            )

            if not normalized_iso2:
                raise ValueError(
                    f"Voice country "
                    f"'{pricing_row.country}' has a blank ISO2."
                )

            if normalized_iso2 in seen_iso2_codes:
                raise ValueError(
                    f"Selected Voice pricing contains duplicate "
                    f"ISO2 '{normalized_iso2}'."
                )

            seen_iso2_codes.add(
                normalized_iso2
            )

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
        pricing_type: str | None
    ) -> None:
        """
        Confirms that the selected pricing type is supported.

        Raises:
            ValueError:
                If the pricing type is empty or unsupported.
        """

        if (
            pricing_type is None
            or not pricing_type.strip()
        ):
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
    def _validate_unique_mobile_iso2(
        pricing_rows: list[MobilePricingRow]
    ) -> None:
        """
        Ensures each Mobile destination appears only once.
        """

        seen_iso2_codes: set[str] = set()

        for pricing_row in pricing_rows:
            normalized_iso2 = (
                pricing_row.iso2
                .strip()
                .upper()
            )

            if not normalized_iso2:
                raise ValueError(
                    f"Mobile country "
                    f"'{pricing_row.country}' "
                    f"has a blank ISO2."
                )

            if normalized_iso2 in seen_iso2_codes:
                raise ValueError(
                    f"Mobile pricing contains duplicate "
                    f"ISO2 '{normalized_iso2}'."
                )

            seen_iso2_codes.add(
                normalized_iso2
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
    def _select_mobile_prices(
        pricing_row: MobilePricingRow,
        pricing_type: str
    ) -> tuple[
        Decimal | None,
        Decimal | None,
        Decimal | None,
        Decimal | None
    ]:
        """
        Selects the four Mobile prices for Baseline or Enterprise.

        Returns:
            (
                sms_outbound,
                sms_inbound,
                voice_outbound,
                voice_inbound
            )
        """

        if pricing_type == "Baseline":
            return (
                pricing_row.baseline_sms_outbound_price,
                pricing_row.baseline_sms_inbound_price,
                pricing_row.baseline_voice_outbound_price,
                pricing_row.baseline_voice_inbound_price
            )

        return (
            pricing_row.enterprise_sms_outbound_price,
            pricing_row.enterprise_sms_inbound_price,
            pricing_row.enterprise_voice_outbound_price,
            pricing_row.enterprise_voice_inbound_price
        )

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
