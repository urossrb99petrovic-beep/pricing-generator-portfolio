from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd

from app.models.pricing_row import PricingRow
from app.models.voice_pricing_row import VoicePricingRow
from app.models.mobile_pricing_row import MobilePricingRow
from app.services.workbook_service import WorkbookService
from app.models.sender_override_price import (
    SenderOverridePrice
)
from app.models.whatsapp_pricing import (
    WhatsAppPricing
)
from app.models.viber_all_other_pricing import (
    ViberAllOtherPricing
)
from app.models.viber_country_pricing_row import (
    ViberCountryPricingRow
)
from app.models.viber_pricing_data import (
    ViberPricingData
)
from app.models.phone_id_suite_pricing_data import (
    PhoneIdSuitePricingData
)

from app.models.phone_id_suite_pricing_row import (
    PhoneIdSuitePricingRow
)
from app.models.phone_id_live_status_pricing_data import (
    PhoneIdLiveStatusPricingData
)

from app.models.phone_id_live_status_pricing_row import (
    PhoneIdLiveStatusPricingRow
)




class PricingDataService:
    """
    Interprets pricing data from an already opened workbook.

    WorkbookService handles Excel access.
    PricingDataService applies Pricing Generator business rules
    and converts worksheet data into business models.
    """
    SMS_WORKSHEET = "SMS"
    PREMIUM_SMS_WORKSHEET = "Premium SMS"
    LOCAL_SMS_WORKSHEET = "Local SMS"
    LOCAL_PREMIUM_SMS_WORKSHEET = "Local Premium SMS"
    SENDER_OVERRIDE_WORKSHEET = "2-way SMS"
    SMS_MKT_WORKSHEET = "SMS MKT"

    VOICE_VERIFY_TRANSACTION_WORKSHEET = (
        "Voice Verify Per Transaction"
    )

    VOICE_VERIFY_MINUTE_WORKSHEET = (
        "Voice Verify Per Minute"
    )

    VOICE_API_WORKSHEET = (
        "Voice API (1-way and 2-way)"
    )

    VOICE_VERIFY_TTS_WORKSHEET = (
        "Voice Verify + TTS"
    )

    TOLL_FREE_VOICE_WORKSHEET = (
        "Toll-Free (Voice Enabled)"
    )
    MOBILE_SMS_VOICE_WORKSHEET = (
        "Mobile (SMS and Voice Enabled)"
    )
    WHATSAPP_WORKSHEET = (
        "WhatsApp Telesign"
    )
    VIBER_WORKSHEET = (
        "Viber Regular Companies"
    )
    PHONE_ID_SUITE_WORKSHEET = (
        "Single pricing"
    )
    PHONE_ID_LIVE_STATUS_WORKSHEET = (
        "Phone ID Live Status"
    )

    STANDARD_PRICING_SCHEMA = "standard_pricing_worksheet"
    LOCAL_PRICING_SCHEMA = "local_pricing_worksheet"
    SENDER_OVERRIDE_SCHEMA = "sender_override_worksheet"
    VOICE_VERIFY_PRICING_SCHEMA = (
        "voice_verify_pricing_worksheet"
    )
    VOICE_API_PRICING_SCHEMA = (
        "voice_api_pricing_worksheet"
    )
    VOICE_VERIFY_TTS_PRICING_SCHEMA = (
        "voice_verify_tts_pricing_worksheet"
    )
    TOLL_FREE_VOICE_PRICING_SCHEMA = (
        "toll_free_voice_pricing_worksheet"
    )
    MOBILE_SMS_VOICE_PRICING_SCHEMA = (
        "mobile_sms_voice_pricing_worksheet"
    )
    WHATSAPP_PRICING_SCHEMA = (
        "whatsapp_pricing_worksheet"
    )
    VIBER_PRICING_SCHEMA = (
        "viber_pricing_worksheet"
    )
    PHONE_ID_SUITE_PRICING_SCHEMA = (
        "phone_id_suite_pricing_worksheet"
    )
    PHONE_ID_LIVE_STATUS_PRICING_SCHEMA = (
        "phone_id_live_status_pricing_worksheet"
    )


    def __init__(
        self,
        workbook_service: WorkbookService,
        workbook_schemas: dict[str, Any]
    ) -> None:
        """
        Creates the pricing-data service.

        Args:
            workbook_service:
                Already initialized and opened workbook service.

            workbook_schemas:
                Workbook schema definitions loaded from
                schemas.json.

        Raises:
            RuntimeError:
                If the supplied workbook is already closed.

            ValueError:
                If no workbook schemas were supplied.
        """

        if not workbook_service.is_open:
            raise RuntimeError(
                "PricingDataService requires an open workbook."
            )

        if not workbook_schemas:
            raise ValueError(
                "Workbook schemas cannot be empty."
            )

        self._workbook_service = workbook_service
        self._workbook_schemas = workbook_schemas

    @property
    def workbook_service(self) -> WorkbookService:
        """
        Returns the workbook service used for data extraction.
        """

        return self._workbook_service

    @property
    def workbook_path(self):
        """
        Returns the path of the source pricing workbook.
        """

        return self._workbook_service.workbook_path

    def get_worksheet_schema(
        self,
        schema_name: str
    ) -> dict[str, Any]:
        """
        Returns one configured workbook schema.

        Args:
            schema_name:
                Schema identifier from the workbook_schemas
                section of schemas.json.

        Returns:
            Requested worksheet schema.

        Raises:
            ValueError:
                If the schema name is empty or does not exist.
        """

        if not schema_name.strip():
            raise ValueError(
                "Worksheet schema name cannot be empty."
            )

        if schema_name not in self._workbook_schemas:
            raise ValueError(
                f"Workbook schema '{schema_name}' does not exist."
            )

        return self._workbook_schemas[
            schema_name
        ].copy()

    def get_sms_pricing(self) -> list[PricingRow]:
        """
        Returns standard SMS pricing rows from the SMS worksheet.

        Returns:
            Pricing rows in their original workbook order.
        """

        worksheet_schema = self.get_worksheet_schema(
            self.STANDARD_PRICING_SCHEMA
        )

        return self._read_standard_pricing(
            worksheet_name=self.SMS_WORKSHEET,
            worksheet_schema=worksheet_schema
        )

    def get_premium_sms_pricing(
        self
    ) -> list[PricingRow]:
        """
        Returns Premium SMS pricing rows from the Premium SMS
        worksheet.

        Returns:
            Pricing rows in their original workbook order.
        """

        worksheet_schema = self.get_worksheet_schema(
            self.STANDARD_PRICING_SCHEMA
        )

        return self._read_standard_pricing(
            worksheet_name=self.PREMIUM_SMS_WORKSHEET,
            worksheet_schema=worksheet_schema
        )

    def get_sms_marketing_pricing(
        self
    ) -> list[PricingRow]:
        """
        Returns SMS Marketing pricing rows from the SMS MKT
        worksheet.

        Returns:
            Pricing rows in their original workbook order.
        """

        worksheet_schema = self.get_worksheet_schema(
            self.STANDARD_PRICING_SCHEMA
        )

        return self._read_standard_pricing(
            worksheet_name=self.SMS_MKT_WORKSHEET,
            worksheet_schema=worksheet_schema
        )

    def get_local_sms_pricing(
        self
    ) -> list[PricingRow]:
        """
        Returns Local SMS pricing rows.

        Returns:
            Clean Local SMS pricing rows in workbook order.
        """

        worksheet_schema = self.get_worksheet_schema(
            self.LOCAL_PRICING_SCHEMA
        )

        return self._read_local_pricing(
            worksheet_name=self.LOCAL_SMS_WORKSHEET,
            worksheet_schema=worksheet_schema
        )

    def get_local_premium_sms_pricing(
        self
    ) -> list[PricingRow]:
        """
        Returns Local Premium SMS pricing rows.

        Returns:
            Clean Local Premium SMS pricing rows in workbook order.
        """

        worksheet_schema = self.get_worksheet_schema(
            self.LOCAL_PRICING_SCHEMA
        )

        return self._read_local_pricing(
            worksheet_name=(
                self.LOCAL_PREMIUM_SMS_WORKSHEET
            ),
            worksheet_schema=worksheet_schema
        )

    def get_sender_override_price(
        self,
        lookup_value: str
    ) -> SenderOverridePrice:
        """
        Returns sender-specific pricing for one exact configured
        lookup value from the 2-way SMS worksheet.

        Args:
            lookup_value:
                Exact Country-column value configured for the sender
                option, for example:
                "United States - Toll Free"

        Returns:
            Matching Baseline and Enterprise sender override prices.

        Raises:
            ValueError:
                If the lookup is empty, missing or matches multiple
                worksheet rows.
        """

        if not lookup_value.strip():
            raise ValueError(
                "Sender override lookup value cannot be empty."
            )

        worksheet_schema = self.get_worksheet_schema(
            self.SENDER_OVERRIDE_SCHEMA
        )

        return self._read_sender_override_price(
            lookup_value=lookup_value,
            worksheet_schema=worksheet_schema
        )

    def get_voice_verify_transaction_pricing(
        self
    ) -> list[VoicePricingRow]:
        """
        Returns Voice Verify Per Transaction pricing rows.

        The worksheet contains separate Mobile and Landline
        prices for both Baseline and Enterprise pricing.
        """

        worksheet_schema = self.get_worksheet_schema(
            self.VOICE_VERIFY_PRICING_SCHEMA
        )

        return self._read_voice_verify_pricing(
            worksheet_name=(
                self.VOICE_VERIFY_TRANSACTION_WORKSHEET
            ),
            worksheet_schema=worksheet_schema
        )

    def get_voice_verify_minute_pricing(
        self
    ) -> list[VoicePricingRow]:
        """
        Returns Voice Verify Per Minute pricing rows.

        The worksheet contains separate Mobile and Landline
        prices for both Baseline and Enterprise pricing.
        """

        worksheet_schema = self.get_worksheet_schema(
            self.VOICE_VERIFY_PRICING_SCHEMA
        )

        return self._read_voice_verify_pricing(
            worksheet_name=(
                self.VOICE_VERIFY_MINUTE_WORKSHEET
            ),
            worksheet_schema=worksheet_schema
        )

    def get_voice_api_pricing(
        self
    ) -> list[VoicePricingRow]:
        """
        Returns Voice API pricing rows.

        The worksheet contains separate outbound Mobile and
        Landline prices, optional Inbound prices and a Number Type
        used to distinguish US Cloud Numbers from Global Mobile
        Numbers.

        Both number types are returned here. Filtering belongs to
        the generation layer.
        """

        worksheet_schema = self.get_worksheet_schema(
            self.VOICE_API_PRICING_SCHEMA
        )

        return self._read_voice_api_pricing(
            worksheet_name=self.VOICE_API_WORKSHEET,
            worksheet_schema=worksheet_schema
        )

    def get_voice_verify_tts_pricing(
        self
    ) -> list[VoicePricingRow]:
        """
        Returns Voice Verify + TTS pricing rows.

        The worksheet contains separate outbound Mobile and
        Landline prices together with optional Inbound pricing.

        Blank or 'not supported' inbound values are represented
        as None. The generation layer will later apply the
        required fallback.
        """

        worksheet_schema = self.get_worksheet_schema(
            self.VOICE_VERIFY_TTS_PRICING_SCHEMA
        )

        return self._read_voice_verify_tts_pricing(
            worksheet_name=(
                self.VOICE_VERIFY_TTS_WORKSHEET
            ),
            worksheet_schema=worksheet_schema
        )

    def get_toll_free_voice_pricing(
        self
    ) -> list[VoicePricingRow]:
        """
        Returns Toll-Free Voice pricing rows.

        Toll-Free Voice contains separate outbound Mobile and
        Landline prices together with mandatory Inbound pricing
        for Baseline and Enterprise.
        """

        worksheet_schema = self.get_worksheet_schema(
            self.TOLL_FREE_VOICE_PRICING_SCHEMA
        )

        return self._read_toll_free_voice_pricing(
            worksheet_name=(
                self.TOLL_FREE_VOICE_WORKSHEET
            ),
            worksheet_schema=worksheet_schema
        )

    def get_mobile_sms_voice_pricing(
        self
    ) -> list[MobilePricingRow]:
        """
        Returns Mobile SMS + Voice pricing rows.

        The worksheet contains SMS Outbound, SMS Inbound,
        Voice Outbound and Voice Inbound prices for both
        Baseline and Enterprise.

        Unsupported source prices are represented as None.
        """

        worksheet_schema = self.get_worksheet_schema(
            self.MOBILE_SMS_VOICE_PRICING_SCHEMA
        )

        return self._read_mobile_sms_voice_pricing(
            worksheet_name=(
                self.MOBILE_SMS_VOICE_WORKSHEET
            ),
            worksheet_schema=worksheet_schema
        )

    def get_whatsapp_pricing(
        self
    ) -> WhatsAppPricing:
        """
        Returns the universal WhatsApp pricing from the
        'Other' market row.

        The source row is located dynamically by Market value
        rather than by a fixed Excel row number.
        """

        worksheet_schema = self.get_worksheet_schema(
            self.WHATSAPP_PRICING_SCHEMA
        )

        return self._read_whatsapp_pricing(
            worksheet_name=self.WHATSAPP_WORKSHEET,
            worksheet_schema=worksheet_schema
        )

    def get_viber_pricing(
        self
    ) -> ViberPricingData:
        """
        Returns complete Viber pricing source data.

        All Others is read from the displayed price columns.
        Individual countries are read from Cost and DM columns.
        """

        worksheet_schema = self.get_worksheet_schema(
            self.VIBER_PRICING_SCHEMA
        )

        return self._read_viber_pricing(
            worksheet_name=self.VIBER_WORKSHEET,
            worksheet_schema=worksheet_schema
        )

    def get_phone_id_suite_pricing(
        self
    ) -> PhoneIdSuitePricingData:
        """
        Reads Phone ID Suite source pricing from the configured
        Single pricing worksheet.
        """

        worksheet_schema = (
            self.get_worksheet_schema(
                self.PHONE_ID_SUITE_PRICING_SCHEMA
            )
        )

        return (
            self._read_phone_id_suite_pricing(
                worksheet_name=(
                    self.PHONE_ID_SUITE_WORKSHEET
                ),
                worksheet_schema=(
                    worksheet_schema
                )
            )
        )

    def get_phone_id_live_status_pricing(
        self
    ) -> PhoneIdLiveStatusPricingData:
        """
        Reads Phone ID Live Status pricing from the configured
        worksheet.
        """

        worksheet_schema = (
            self.get_worksheet_schema(
                self.PHONE_ID_LIVE_STATUS_PRICING_SCHEMA
            )
        )

        return (
            self._read_phone_id_live_status_pricing(
                worksheet_name=(
                    self.PHONE_ID_LIVE_STATUS_WORKSHEET
                ),
                worksheet_schema=(
                    worksheet_schema
                )
            )
        )

    def _read_local_pricing(
        self,
        worksheet_name: str,
        worksheet_schema: dict[str, Any]
    ) -> list[PricingRow]:
        """
        Reads a Local pricing worksheet and converts its rows into
        PricingRow objects.

        Local worksheets contain Country, Baseline and Enterprise,
        but do not contain ISO2 or an All Others row.
        """

        self._require_open_workbook()

        if not worksheet_name.strip():
            raise ValueError(
                "Local pricing worksheet name cannot be empty."
            )

        worksheet_data = (
            self._workbook_service.read_worksheet(
                worksheet_name
            )
        )

        header_indexes = (
            self._workbook_service.get_header_indexes(
                worksheet_data=worksheet_data,
                worksheet_schema=worksheet_schema
            )
        )

        data_start_row_number = worksheet_schema[
            "data_start_row"
        ]

        data_start_row_index = (
            data_start_row_number - 1
        )

        if (
            data_start_row_index < 0
            or data_start_row_index
            >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured data start row "
                f"{data_start_row_number} is outside "
                f"worksheet '{worksheet_name}'."
            )

        pricing_rows: list[PricingRow] = []

        for dataframe_row_index in range(
            data_start_row_index,
            len(worksheet_data.index)
        ):
            worksheet_row = worksheet_data.iloc[
                dataframe_row_index
            ]

            if self._is_blank_pricing_row(
                worksheet_row=worksheet_row,
                header_indexes=header_indexes
            ):
                continue

            try:
                pricing_row = (
                    self._create_local_pricing_row(
                        worksheet_row=worksheet_row,
                        header_indexes=header_indexes,
                        worksheet_schema=worksheet_schema
                    )
                )

            except ValueError as error:
                excel_row_number = (
                    dataframe_row_index + 1
                )

                raise ValueError(
                    f"Invalid local pricing data in worksheet "
                    f"'{worksheet_name}', Excel row "
                    f"{excel_row_number}. {error}"
                ) from error

            pricing_rows.append(
                pricing_row
            )

        if not pricing_rows:
            raise RuntimeError(
                f"No local pricing rows were found in worksheet "
                f"'{worksheet_name}' of workbook "
                f"'{self.workbook_path.name}'."
            )

        return pricing_rows

    def _read_standard_pricing(
        self,
        worksheet_name: str,
        worksheet_schema: dict[str, Any]
    ) -> list[PricingRow]:
        """
        Reads a standard pricing worksheet and converts its data
        rows into PricingRow objects.

        Args:
            worksheet_name:
                Name of the pricing worksheet.

            worksheet_schema:
                Schema describing headers and the first data row.

        Returns:
            Pricing rows in workbook order.

        Raises:
            ValueError:
                If worksheet or schema settings are invalid.

            RuntimeError:
                If no valid pricing rows are extracted.
        """

        self._require_open_workbook()

        if not worksheet_name.strip():
            raise ValueError(
                "Pricing worksheet name cannot be empty."
            )

        worksheet_data = (
            self._workbook_service.read_worksheet(
                worksheet_name
            )
        )

        header_indexes = (
            self._workbook_service.get_header_indexes(
                worksheet_data=worksheet_data,
                worksheet_schema=worksheet_schema
            )
        )

        all_other_row_number = worksheet_schema.get(
            "all_other_countries_row"
        )

        pricing_rows: list[PricingRow] = []

        if all_other_row_number is not None:
            all_other_row_index = all_other_row_number - 1

            if (
                all_other_row_index < 0
                or all_other_row_index
                >= len(worksheet_data.index)
            ):
                raise ValueError(
                    f"Configured All Other Countries row "
                    f"{all_other_row_number} is outside "
                    f"worksheet '{worksheet_name}'."
                )

            all_other_worksheet_row = worksheet_data.iloc[
                all_other_row_index
            ]

            if not self._is_blank_pricing_row(
                worksheet_row=all_other_worksheet_row,
                header_indexes=header_indexes
            ):
                try:
                    all_other_pricing_row = (
                        self._create_pricing_row(
                            worksheet_row=(
                                all_other_worksheet_row
                            ),
                            header_indexes=header_indexes
                        )
                    )

                except ValueError as error:
                    raise ValueError(
                        f"Invalid All Other Countries pricing "
                        f"in worksheet '{worksheet_name}', "
                        f"Excel row {all_other_row_number}. "
                        f"{error}"
                    ) from error

                pricing_rows.append(
                    all_other_pricing_row
                )

        data_start_row_number = worksheet_schema[
            "data_start_row"
        ]

        data_start_row_index = (
            data_start_row_number - 1
        )

        if (
            data_start_row_index < 0
            or data_start_row_index
            >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured data start row "
                f"{data_start_row_number} is outside "
                f"worksheet '{worksheet_name}'."
            )

        for dataframe_row_index in range(
            data_start_row_index,
            len(worksheet_data.index)
        ):
            worksheet_row = worksheet_data.iloc[
                dataframe_row_index
            ]

            if self._is_blank_pricing_row(
                worksheet_row=worksheet_row,
                header_indexes=header_indexes
            ):
                continue

            try:
                pricing_row = self._create_pricing_row(
                    worksheet_row=worksheet_row,
                    header_indexes=header_indexes
                )

            except ValueError as error:
                excel_row_number = (
                    dataframe_row_index + 1
                )

                raise ValueError(
                    f"Invalid pricing data in worksheet "
                    f"'{worksheet_name}', Excel row "
                    f"{excel_row_number}. {error}"
                ) from error

            pricing_rows.append(
                pricing_row
            )

        if not pricing_rows:
            raise RuntimeError(
                f"No pricing rows were found in worksheet "
                f"'{worksheet_name}' of workbook "
                f"'{self.workbook_path.name}'."
            )

        return pricing_rows

    def _read_sender_override_price(
        self,
        lookup_value: str,
        worksheet_schema: dict[str, Any]
    ) -> SenderOverridePrice:
        """
        Finds exactly one sender override row and converts it into a
        SenderOverridePrice object.
        """

        self._require_open_workbook()

        worksheet_data = (
            self._workbook_service.read_worksheet(
                self.SENDER_OVERRIDE_WORKSHEET
            )
        )

        header_indexes = (
            self._workbook_service.get_header_indexes(
                worksheet_data=worksheet_data,
                worksheet_schema=worksheet_schema
            )
        )

        required_fields = {
            "lookup_value",
            "baseline_price",
            "enterprise_price"
        }

        missing_fields = (
            required_fields
            - header_indexes.keys()
        )

        if missing_fields:
            missing_field_list = ", ".join(
                sorted(missing_fields)
            )

            raise ValueError(
                "Cannot read sender override pricing because "
                f"required field index(es) are missing: "
                f"{missing_field_list}."
            )

        data_start_row_number = worksheet_schema[
            "data_start_row"
        ]

        data_start_row_index = (
            data_start_row_number - 1
        )

        if (
            data_start_row_index < 0
            or data_start_row_index
            >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured data start row "
                f"{data_start_row_number} is outside worksheet "
                f"'{self.SENDER_OVERRIDE_WORKSHEET}'."
            )

        matching_rows: list[
            tuple[int, pd.Series]
        ] = []

        for dataframe_row_index in range(
            data_start_row_index,
            len(worksheet_data.index)
        ):
            worksheet_row = worksheet_data.iloc[
                dataframe_row_index
            ]

            raw_lookup_value = worksheet_row.iloc[
                header_indexes["lookup_value"]
            ]

            normalized_lookup_value = (
                self._normalize_text_value(
                    raw_lookup_value
                )
            )

            if normalized_lookup_value == lookup_value:
                matching_rows.append(
                    (
                        dataframe_row_index,
                        worksheet_row
                    )
                )

        if not matching_rows:
            raise ValueError(
                f"Sender override lookup value "
                f"'{lookup_value}' was not found in worksheet "
                f"'{self.SENDER_OVERRIDE_WORKSHEET}'."
            )

        if len(matching_rows) > 1:
            matching_excel_rows = ", ".join(
                str(dataframe_row_index + 1)
                for dataframe_row_index, _
                in matching_rows
            )

            raise ValueError(
                f"Sender override lookup value "
                f"'{lookup_value}' matched multiple rows in "
                f"worksheet '{self.SENDER_OVERRIDE_WORKSHEET}': "
                f"{matching_excel_rows}."
            )

        dataframe_row_index, worksheet_row = (
            matching_rows[0]
        )

        try:
            baseline_price = (
                self._convert_price_to_decimal(
                    worksheet_row.iloc[
                        header_indexes[
                            "baseline_price"
                        ]
                    ],
                    "baseline_price"
                )
            )

            enterprise_price = (
                self._convert_price_to_decimal(
                    worksheet_row.iloc[
                        header_indexes[
                            "enterprise_price"
                        ]
                    ],
                    "enterprise_price"
                )
            )

        except ValueError as error:
            excel_row_number = (
                dataframe_row_index + 1
            )

            raise ValueError(
                f"Invalid sender override pricing in worksheet "
                f"'{self.SENDER_OVERRIDE_WORKSHEET}', Excel row "
                f"{excel_row_number}. {error}"
            ) from error

        return SenderOverridePrice(
            lookup_value=lookup_value,
            baseline_price=baseline_price,
            enterprise_price=enterprise_price
        )

    def _read_voice_verify_pricing(
        self,
        worksheet_name: str,
        worksheet_schema: dict[str, Any]
    ) -> list[VoicePricingRow]:
        """
        Reads a Voice Verify pricing worksheet.

        Voice Verify worksheets use two-row grouped headers and
        contain separate Mobile and Landline prices for Baseline
        and Enterprise pricing.

        The configured All Other Countries row is included as the
        first returned VoicePricingRow.

        Args:
            worksheet_name:
                Voice Verify worksheet to read.

            worksheet_schema:
                Grouped Voice Verify worksheet schema.

        Returns:
            VoicePricingRow objects in original workbook order.

        Raises:
            ValueError:
                If worksheet configuration or pricing data is invalid.

            RuntimeError:
                If no Voice Verify pricing rows are extracted.
        """

        self._require_open_workbook()

        if not worksheet_name.strip():
            raise ValueError(
                "Voice Verify worksheet name cannot be empty."
            )

        worksheet_data = (
            self._workbook_service.read_worksheet(
                worksheet_name
            )
        )

        header_indexes = (
            self._workbook_service
            .get_grouped_header_indexes(
                worksheet_data=worksheet_data,
                worksheet_schema=worksheet_schema
            )
        )

        pricing_rows: list[VoicePricingRow] = []

        all_other_row_number = worksheet_schema.get(
            "all_other_countries_row"
        )

        if all_other_row_number is not None:
            all_other_row_index = (
                all_other_row_number - 1
            )

            if (
                all_other_row_index < 0
                or all_other_row_index
                >= len(worksheet_data.index)
            ):
                raise ValueError(
                    f"Configured All Other Countries row "
                    f"{all_other_row_number} is outside "
                    f"worksheet '{worksheet_name}'."
                )

            all_other_worksheet_row = (
                worksheet_data.iloc[
                    all_other_row_index
                ]
            )

            if not self._is_blank_voice_pricing_row(
                worksheet_row=all_other_worksheet_row,
                header_indexes=header_indexes
            ):
                try:
                    all_other_pricing_row = (
                        self._create_voice_verify_pricing_row(
                            worksheet_row=(
                                all_other_worksheet_row
                            ),
                            header_indexes=header_indexes
                        )
                    )

                except ValueError as error:
                    raise ValueError(
                        f"Invalid All Other Countries Voice "
                        f"pricing in worksheet "
                        f"'{worksheet_name}', Excel row "
                        f"{all_other_row_number}. {error}"
                    ) from error

                pricing_rows.append(
                    all_other_pricing_row
                )

        data_start_row_number = worksheet_schema[
            "data_start_row"
        ]

        data_start_row_index = (
            data_start_row_number - 1
        )

        if (
            data_start_row_index < 0
            or data_start_row_index
            >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured data start row "
                f"{data_start_row_number} is outside "
                f"worksheet '{worksheet_name}'."
            )

        for dataframe_row_index in range(
            data_start_row_index,
            len(worksheet_data.index)
        ):
            worksheet_row = worksheet_data.iloc[
                dataframe_row_index
            ]

            if self._is_blank_voice_pricing_row(
                worksheet_row=worksheet_row,
                header_indexes=header_indexes
            ):
                continue
        
            try:
                
                pricing_row = (
                    self._create_voice_verify_pricing_row(
                        worksheet_row=worksheet_row,
                        header_indexes=header_indexes
                    )
                )

            except ValueError as error:
                excel_row_number = (
                    dataframe_row_index + 1
                )

                raise ValueError(
                    f"Invalid Voice Verify pricing data "
                    f"in worksheet '{worksheet_name}', "
                    f"Excel row {excel_row_number}. "
                    f"{error}"
                ) from error

            pricing_rows.append(
                pricing_row
            )

        if not pricing_rows:
            raise RuntimeError(
                f"No Voice Verify pricing rows were found "
                f"in worksheet '{worksheet_name}' of workbook "
                f"'{self.workbook_path.name}'."
            )

        return pricing_rows

    def _read_voice_api_pricing(
        self,
        worksheet_name: str,
        worksheet_schema: dict[str, Any]
    ) -> list[VoicePricingRow]:
        """
        Reads the Voice API pricing worksheet.

        The source contains:
            - outbound Mobile pricing;
            - outbound Landline pricing;
            - Inbound pricing;
            - Number Type.

        Inbound cells containing 'not supported' are represented
        as None. The generation layer will later apply the required
        All Others fallback.

        Duplicate ISO2 values are deliberately retained because
        different Number Types may have different pricing.
        """

        self._require_open_workbook()

        if not worksheet_name.strip():
            raise ValueError(
                "Voice API worksheet name cannot be empty."
            )

        worksheet_data = (
            self._workbook_service.read_worksheet(
                worksheet_name
            )
        )

        header_indexes = (
            self._workbook_service
            .get_grouped_header_indexes(
                worksheet_data=worksheet_data,
                worksheet_schema=worksheet_schema
            )
        )

        pricing_rows: list[VoicePricingRow] = []

        all_other_row_number = worksheet_schema.get(
            "all_other_countries_row"
        )

        if all_other_row_number is not None:
            all_other_row_index = (
                all_other_row_number - 1
            )

            if (
                all_other_row_index < 0
                or all_other_row_index
                >= len(worksheet_data.index)
            ):
                raise ValueError(
                    f"Configured All Other Countries row "
                    f"{all_other_row_number} is outside "
                    f"worksheet '{worksheet_name}'."
                )

            all_other_worksheet_row = (
                worksheet_data.iloc[
                    all_other_row_index
                ]
            )

            if not self._is_blank_voice_pricing_row(
                worksheet_row=all_other_worksheet_row,
                header_indexes=header_indexes
            ):
                try:
                    all_other_pricing_row = (
                        self._create_voice_api_pricing_row(
                            worksheet_row=(
                                all_other_worksheet_row
                            ),
                            header_indexes=header_indexes
                        )
                    )

                except ValueError as error:
                    raise ValueError(
                        f"Invalid All Other Countries Voice API "
                        f"pricing in worksheet "
                        f"'{worksheet_name}', Excel row "
                        f"{all_other_row_number}. {error}"
                    ) from error

                pricing_rows.append(
                    all_other_pricing_row
                )

        data_start_row_number = worksheet_schema[
            "data_start_row"
        ]

        data_start_row_index = (
            data_start_row_number - 1
        )

        if (
            data_start_row_index < 0
            or data_start_row_index
            >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured data start row "
                f"{data_start_row_number} is outside "
                f"worksheet '{worksheet_name}'."
            )

        for dataframe_row_index in range(
            data_start_row_index,
            len(worksheet_data.index)
        ):
            worksheet_row = worksheet_data.iloc[
                dataframe_row_index
            ]

            if self._is_blank_voice_pricing_row(
                worksheet_row=worksheet_row,
                header_indexes=header_indexes
            ):
                continue

            try:
                pricing_row = (
                    self._create_voice_api_pricing_row(
                        worksheet_row=worksheet_row,
                        header_indexes=header_indexes
                    )
                )

            except ValueError as error:
                excel_row_number = (
                    dataframe_row_index + 1
                )

                raise ValueError(
                    f"Invalid Voice API pricing data "
                    f"in worksheet '{worksheet_name}', "
                    f"Excel row {excel_row_number}. "
                    f"{error}"
                ) from error

            pricing_rows.append(
                pricing_row
            )

        if not pricing_rows:
            raise RuntimeError(
                f"No Voice API pricing rows were found "
                f"in worksheet '{worksheet_name}' of workbook "
                f"'{self.workbook_path.name}'."
            )

        return pricing_rows

    def _read_voice_verify_tts_pricing(
        self,
        worksheet_name: str,
        worksheet_schema: dict[str, Any]
    ) -> list[VoicePricingRow]:
        """
        Reads the Voice Verify + TTS worksheet.

        The source contains:
            - outbound Mobile pricing;
            - outbound Landline pricing;
            - optional Inbound pricing.

        Blank and 'not supported' inbound values are represented
        as None. The generation layer applies the appropriate
        fallback later.
        """

        self._require_open_workbook()

        if not worksheet_name.strip():
            raise ValueError(
                "Voice Verify + TTS worksheet name cannot be empty."
            )

        worksheet_data = (
            self._workbook_service.read_worksheet(
                worksheet_name
            )
        )

        header_indexes = (
            self._workbook_service
            .get_grouped_header_indexes(
                worksheet_data=worksheet_data,
                worksheet_schema=worksheet_schema
            )
        )

        pricing_rows: list[VoicePricingRow] = []

        all_other_row_number = worksheet_schema.get(
            "all_other_countries_row"
        )

        if all_other_row_number is not None:
            all_other_row_index = (
                all_other_row_number - 1
            )

            if (
                all_other_row_index < 0
                or all_other_row_index
                >= len(worksheet_data.index)
            ):
                raise ValueError(
                    f"Configured All Other Countries row "
                    f"{all_other_row_number} is outside "
                    f"worksheet '{worksheet_name}'."
                )

            all_other_worksheet_row = (
                worksheet_data.iloc[
                    all_other_row_index
                ]
            )

            if not self._is_blank_voice_pricing_row(
                worksheet_row=all_other_worksheet_row,
                header_indexes=header_indexes
            ):
                try:
                    all_other_pricing_row = (
                        self._create_voice_verify_tts_pricing_row(
                            worksheet_row=(
                                all_other_worksheet_row
                            ),
                            header_indexes=header_indexes
                        )
                    )

                except ValueError as error:
                    raise ValueError(
                        f"Invalid All Other Countries "
                        f"Voice Verify + TTS pricing in worksheet "
                        f"'{worksheet_name}', Excel row "
                        f"{all_other_row_number}. {error}"
                    ) from error

                pricing_rows.append(
                    all_other_pricing_row
                )

        data_start_row_number = worksheet_schema[
            "data_start_row"
        ]

        data_start_row_index = (
            data_start_row_number - 1
        )

        if (
            data_start_row_index < 0
            or data_start_row_index
            >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured data start row "
                f"{data_start_row_number} is outside "
                f"worksheet '{worksheet_name}'."
            )

        for dataframe_row_index in range(
            data_start_row_index,
            len(worksheet_data.index)
        ):
            worksheet_row = worksheet_data.iloc[
                dataframe_row_index
            ]

            if self._is_blank_voice_pricing_row(
                worksheet_row=worksheet_row,
                header_indexes=header_indexes
            ):
                continue

            try:
                pricing_row = (
                    self._create_voice_verify_tts_pricing_row(
                        worksheet_row=worksheet_row,
                        header_indexes=header_indexes
                    )
                )

            except ValueError as error:
                excel_row_number = (
                    dataframe_row_index + 1
                )

                raise ValueError(
                    f"Invalid Voice Verify + TTS pricing data "
                    f"in worksheet '{worksheet_name}', "
                    f"Excel row {excel_row_number}. "
                    f"{error}"
                ) from error

            pricing_rows.append(
                pricing_row
            )

        if not pricing_rows:
            raise RuntimeError(
                f"No Voice Verify + TTS pricing rows were found "
                f"in worksheet '{worksheet_name}' of workbook "
                f"'{self.workbook_path.name}'."
            )

        return pricing_rows

    def _read_toll_free_voice_pricing(
        self,
        worksheet_name: str,
        worksheet_schema: dict[str, Any]
    ) -> list[VoicePricingRow]:
        """
        Reads the Toll-Free Voice pricing worksheet.

        All outbound and inbound pricing fields are required to
        contain numeric prices.
        """

        self._require_open_workbook()

        if not worksheet_name.strip():
            raise ValueError(
                "Toll-Free Voice worksheet name cannot be empty."
            )

        worksheet_data = (
            self._workbook_service.read_worksheet(
                worksheet_name
            )
        )

        header_indexes = (
            self._workbook_service
            .get_grouped_header_indexes(
                worksheet_data=worksheet_data,
                worksheet_schema=worksheet_schema
            )
        )

        pricing_rows: list[VoicePricingRow] = []

        all_other_row_number = worksheet_schema.get(
            "all_other_countries_row"
        )

        if all_other_row_number is not None:
            all_other_row_index = (
                all_other_row_number - 1
            )

            if (
                all_other_row_index < 0
                or all_other_row_index
                >= len(worksheet_data.index)
            ):
                raise ValueError(
                    f"Configured All Other Countries row "
                    f"{all_other_row_number} is outside "
                    f"worksheet '{worksheet_name}'."
                )

            all_other_worksheet_row = (
                worksheet_data.iloc[
                    all_other_row_index
                ]
            )

            if not self._is_blank_voice_pricing_row(
                worksheet_row=all_other_worksheet_row,
                header_indexes=header_indexes
            ):
                try:
                    all_other_pricing_row = (
                        self._create_toll_free_voice_pricing_row(
                            worksheet_row=(
                                all_other_worksheet_row
                            ),
                            header_indexes=header_indexes
                        )
                    )

                except ValueError as error:
                    raise ValueError(
                        f"Invalid All Other Countries Toll-Free "
                        f"Voice pricing in worksheet "
                        f"'{worksheet_name}', Excel row "
                        f"{all_other_row_number}. {error}"
                    ) from error

                pricing_rows.append(
                    all_other_pricing_row
                )

        data_start_row_number = worksheet_schema[
            "data_start_row"
        ]

        data_start_row_index = (
            data_start_row_number - 1
        )

        if (
            data_start_row_index < 0
            or data_start_row_index
            >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured data start row "
                f"{data_start_row_number} is outside "
                f"worksheet '{worksheet_name}'."
            )

        for dataframe_row_index in range(
            data_start_row_index,
            len(worksheet_data.index)
        ):
            worksheet_row = worksheet_data.iloc[
                dataframe_row_index
            ]

            if self._is_blank_voice_pricing_row(
                worksheet_row=worksheet_row,
                header_indexes=header_indexes
            ):
                continue

            try:
                pricing_row = (
                    self._create_toll_free_voice_pricing_row(
                        worksheet_row=worksheet_row,
                        header_indexes=header_indexes
                    )
                )

            except ValueError as error:
                excel_row_number = (
                    dataframe_row_index + 1
                )

                raise ValueError(
                    f"Invalid Toll-Free Voice pricing data "
                    f"in worksheet '{worksheet_name}', "
                    f"Excel row {excel_row_number}. "
                    f"{error}"
                ) from error

            pricing_rows.append(
                pricing_row
            )

        if not pricing_rows:
            raise RuntimeError(
                f"No Toll-Free Voice pricing rows were found "
                f"in worksheet '{worksheet_name}' of workbook "
                f"'{self.workbook_path.name}'."
            )

        return pricing_rows

    def _read_mobile_sms_voice_pricing(
        self,
        worksheet_name: str,
        worksheet_schema: dict[str, Any]
    ) -> list[MobilePricingRow]:
        """
        Reads the Mobile SMS + Voice pricing worksheet.

        Currency-specific physical column positions are ignored.
        Columns are resolved by accepted header aliases.

        'not supported' prices are represented as None.
        """

        self._require_open_workbook()

        if not worksheet_name.strip():
            raise ValueError(
                "Mobile SMS + Voice worksheet name cannot be empty."
            )

        worksheet_data = (
            self._workbook_service.read_worksheet(
                worksheet_name
            )
        )

        header_indexes = (
            self._workbook_service
            .get_header_indexes_with_aliases(
                worksheet_data=worksheet_data,
                worksheet_schema=worksheet_schema
            )
        )

        pricing_rows: list[MobilePricingRow] = []

        all_other_row_number = worksheet_schema.get(
            "all_other_countries_row"
        )

        if all_other_row_number is not None:
            all_other_row_index = (
                all_other_row_number - 1
            )

            if (
                all_other_row_index < 0
                or all_other_row_index
                >= len(worksheet_data.index)
            ):
                raise ValueError(
                    f"Configured All Other Countries row "
                    f"{all_other_row_number} is outside "
                    f"worksheet '{worksheet_name}'."
                )

            all_other_worksheet_row = (
                worksheet_data.iloc[
                    all_other_row_index
                ]
            )

            try:
                all_other_pricing_row = (
                    self._create_mobile_pricing_row(
                        worksheet_row=(
                            all_other_worksheet_row
                        ),
                        header_indexes=header_indexes
                    )
                )

            except ValueError as error:
                raise ValueError(
                    f"Invalid All Other Countries Mobile pricing "
                    f"in worksheet '{worksheet_name}', Excel row "
                    f"{all_other_row_number}. {error}"
                ) from error

            pricing_rows.append(
                all_other_pricing_row
            )

        data_start_row_number = worksheet_schema[
            "data_start_row"
        ]

        data_start_row_index = (
            data_start_row_number - 1
        )

        if (
            data_start_row_index < 0
            or data_start_row_index
            >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured data start row "
                f"{data_start_row_number} is outside "
                f"worksheet '{worksheet_name}'."
            )

        for dataframe_row_index in range(
            data_start_row_index,
            len(worksheet_data.index)
        ):
            worksheet_row = worksheet_data.iloc[
                dataframe_row_index
            ]

            country = self._normalize_text_value(
                worksheet_row.iloc[
                    header_indexes["country"]
                ]
            )

            iso2 = self._normalize_text_value(
                worksheet_row.iloc[
                    header_indexes["iso2"]
                ]
            )

            if not country and not iso2:
                continue

            try:
                pricing_row = (
                    self._create_mobile_pricing_row(
                        worksheet_row=worksheet_row,
                        header_indexes=header_indexes
                    )
                )

            except ValueError as error:
                excel_row_number = (
                    dataframe_row_index + 1
                )

                raise ValueError(
                    f"Invalid Mobile SMS + Voice pricing data "
                    f"in worksheet '{worksheet_name}', "
                    f"Excel row {excel_row_number}. "
                    f"{error}"
                ) from error

            pricing_rows.append(
                pricing_row
            )

        if not pricing_rows:
            raise RuntimeError(
                f"No Mobile SMS + Voice pricing rows were found "
                f"in worksheet '{worksheet_name}' of workbook "
                f"'{self.workbook_path.name}'."
            )

        return pricing_rows

    def _read_whatsapp_pricing(
        self,
        worksheet_name: str,
        worksheet_schema: dict[str, Any]
    ) -> WhatsAppPricing:
        """
        Reads the WhatsApp worksheet and extracts the single
        universal pricing row where Market is 'Other'.

        The position of the Other row is deliberately dynamic
        because additional markets may be inserted into the
        source workbook over time.
        """

        self._require_open_workbook()

        if not worksheet_name.strip():
            raise ValueError(
                "WhatsApp worksheet name cannot be empty."
            )

        worksheet_data = (
            self._workbook_service.read_worksheet(
                worksheet_name
            )
        )

        header_indexes = (
            self._workbook_service.get_header_indexes(
                worksheet_data=worksheet_data,
                worksheet_schema=worksheet_schema
            )
        )

        required_fields = {
            "market",
            "iso2",
            "baseline_price",
            "enterprise_price"
        }

        missing_fields = (
            required_fields
            - header_indexes.keys()
        )

        if missing_fields:
            missing_field_list = ", ".join(
                sorted(
                    missing_fields
                )
            )

            raise ValueError(
                "Cannot read WhatsApp pricing because "
                f"required field index(es) are missing: "
                f"{missing_field_list}."
            )

        all_other_market_value = (
            str(
                worksheet_schema.get(
                    "all_other_market_value",
                    "Other"
                )
            ).strip()
        )

        if not all_other_market_value:
            raise ValueError(
                "WhatsApp All Other market value "
                "cannot be empty."
            )

        data_start_row_number = (
            worksheet_schema[
                "data_start_row"
            ]
        )

        data_start_row_index = (
            data_start_row_number - 1
        )

        if (
            data_start_row_index < 0
            or data_start_row_index
            >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured data start row "
                f"{data_start_row_number} is outside "
                f"worksheet '{worksheet_name}'."
            )

        matching_rows: list[
            tuple[int, pd.Series]
        ] = []

        for dataframe_row_index in range(
            data_start_row_index,
            len(worksheet_data.index)
        ):
            worksheet_row = worksheet_data.iloc[
                dataframe_row_index
            ]

            market = self._normalize_text_value(
                worksheet_row.iloc[
                    header_indexes[
                        "market"
                    ]
                ]
            )

            if (
                market.casefold()
                != all_other_market_value.casefold()
            ):
                continue

            matching_rows.append(
                (
                    dataframe_row_index,
                    worksheet_row
                )
            )

        if not matching_rows:
            raise ValueError(
                f"WhatsApp market "
                f"'{all_other_market_value}' was not found "
                f"in worksheet '{worksheet_name}'."
            )

        if len(matching_rows) > 1:
            matching_excel_rows = ", ".join(
                str(
                    dataframe_row_index + 1
                )
                for dataframe_row_index, _
                in matching_rows
            )

            raise ValueError(
                f"WhatsApp market "
                f"'{all_other_market_value}' matched "
                f"multiple rows in worksheet "
                f"'{worksheet_name}': "
                f"{matching_excel_rows}."
            )

        dataframe_row_index, worksheet_row = (
            matching_rows[0]
        )

        try:
            return self._create_whatsapp_pricing(
                worksheet_row=worksheet_row,
                header_indexes=header_indexes
            )

        except ValueError as error:
            excel_row_number = (
                dataframe_row_index + 1
            )

            raise ValueError(
                f"Invalid WhatsApp pricing data in "
                f"worksheet '{worksheet_name}', "
                f"Excel row {excel_row_number}. "
                f"{error}"
            ) from error

    def _read_viber_pricing(
        self,
        worksheet_name: str,
        worksheet_schema: dict[str, Any]
    ) -> ViberPricingData:
        """
        Reads Viber source pricing.

        Business rule:

            All Others:
                displayed worksheet prices are authoritative.

            Individual countries:
                only Cost and DM source fields are retained.
                Displayed C:F prices are deliberately ignored.
        """

        self._require_open_workbook()

        if not worksheet_name.strip():
            raise ValueError(
                "Viber worksheet name cannot be empty."
            )

        worksheet_data = (
            self._workbook_service.read_worksheet(
                worksheet_name
            )
        )

        header_indexes = (
            self._workbook_service.get_header_indexes(
                worksheet_data=worksheet_data,
                worksheet_schema=worksheet_schema
            )
        )

        required_fields = {
            "country",
            "iso2",

            "displayed_transactional_otp_price",
            "displayed_promotional_price",
            "displayed_session_chat_price",
            "displayed_international_price",

            "transactional_otp_cost",
            "promotional_cost",
            "session_chat_cost",
            "international_cost",

            "baseline_dm",
            "enterprise_dm"
        }

        missing_fields = (
            required_fields
            - header_indexes.keys()
        )

        if missing_fields:
            missing_field_list = ", ".join(
                sorted(
                    missing_fields
                )
            )

            raise ValueError(
                "Cannot read Viber pricing because "
                f"required field index(es) are missing: "
                f"{missing_field_list}."
            )

        # ==================================================
        # ALL OTHERS
        # ==================================================

        all_other_row_number = (
            worksheet_schema[
                "all_other_countries_row"
            ]
        )

        all_other_row_index = (
            all_other_row_number - 1
        )

        if (
            all_other_row_index < 0
            or all_other_row_index
            >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured Viber All Others row "
                f"{all_other_row_number} is outside "
                f"worksheet '{worksheet_name}'."
            )

        all_other_worksheet_row = (
            worksheet_data.iloc[
                all_other_row_index
            ]
        )

        try:
            all_other_pricing = (
                self._create_viber_all_other_pricing(
                    worksheet_row=(
                        all_other_worksheet_row
                    ),
                    header_indexes=header_indexes
                )
            )

        except ValueError as error:
            raise ValueError(
                f"Invalid Viber All Others pricing "
                f"in worksheet '{worksheet_name}', "
                f"Excel row {all_other_row_number}. "
                f"{error}"
            ) from error

        # ==================================================
        # COUNTRY ROWS
        # ==================================================

        data_start_row_number = (
            worksheet_schema[
                "data_start_row"
            ]
        )

        data_start_row_index = (
            data_start_row_number - 1
        )

        if (
            data_start_row_index < 0
            or data_start_row_index
            >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured Viber data start row "
                f"{data_start_row_number} is outside "
                f"worksheet '{worksheet_name}'."
            )

        country_rows: list[
            ViberCountryPricingRow
        ] = []

        for dataframe_row_index in range(
            data_start_row_index,
            len(worksheet_data.index)
        ):
            worksheet_row = worksheet_data.iloc[
                dataframe_row_index
            ]

            country = self._normalize_text_value(
                worksheet_row.iloc[
                    header_indexes[
                        "country"
                    ]
                ]
            )

            iso2 = self._normalize_text_value(
                worksheet_row.iloc[
                    header_indexes[
                        "iso2"
                    ]
                ]
            )

            # Completely empty rows / worksheet tail.
            if not country and not iso2:
                continue

            try:
                country_pricing_row = (
                    self._create_viber_country_pricing_row(
                        worksheet_row=worksheet_row,
                        header_indexes=header_indexes
                    )
                )

            except ValueError as error:
                excel_row_number = (
                    dataframe_row_index + 1
                )

                raise ValueError(
                    f"Invalid Viber country pricing data "
                    f"in worksheet '{worksheet_name}', "
                    f"Excel row {excel_row_number}. "
                    f"{error}"
                ) from error

            country_rows.append(
                country_pricing_row
            )

        if not country_rows:
            raise RuntimeError(
                f"No Viber country pricing rows were found "
                f"in worksheet '{worksheet_name}' of workbook "
                f"'{self.workbook_path.name}'."
            )

        return ViberPricingData(
            all_other=all_other_pricing,
            countries=country_rows
        )

    def _read_phone_id_suite_pricing(
        self,
        worksheet_name: str,
        worksheet_schema: dict
    ) -> PhoneIdSuitePricingData:
        """
        Reads Phone ID Suite pricing.

        Source structure:

            Row 13:
                Headers

            Row 14 onward:
                Countries

            Later:
                blank rows may appear

            Dynamic row:
                All other countries

            Everything below All other countries:
                ignored completely

        Special source rules:

            n/a
                Means that the specific subproduct is
                unavailable for that country.

            Brazil (full response including DOB)
            United States (full response including DOB)
                Must be ignored.

            All other countries
                Terminates the pricing table.
        """

        worksheet_data = (
            self._workbook_service
            .read_worksheet(
                worksheet_name
            )
        )

        header_indexes = (
            self._workbook_service
            .get_header_indexes_in_range(
                worksheet_data=(
                    worksheet_data
                ),
                worksheet_schema=(
                    worksheet_schema
                )
            )
        )

        data_start_row_number = (
            worksheet_schema[
                "data_start_row"
            ]
        )

        data_start_index = (
            data_start_row_number - 1
        )

        if (
            data_start_index < 0
            or data_start_index
            >= len(
                worksheet_data.index
            )
        ):
            raise ValueError(
                f"Configured Phone ID Suite data start "
                f"row {data_start_row_number} is outside "
                f"worksheet '{worksheet_name}'."
            )

        country_column_index = (
            header_indexes[
                "country"
            ]
        )

        iso2_column_index = (
            header_indexes[
                "iso2"
            ]
        )

        all_other_country_value = (
            str(
                worksheet_schema[
                    "all_other_country_value"
                ]
            )
            .strip()
        )

        if not all_other_country_value:
            raise ValueError(
                "Phone ID Suite All Others country value "
                "cannot be empty."
            )

        excluded_country_values = {
            str(
                country_name
            )
            .strip()
            .casefold()
            for country_name
            in worksheet_schema.get(
                "excluded_country_values",
                []
            )
            if str(
                country_name
            ).strip()
        }

        # ==================================================
        # FIND ALL OTHER COUNTRIES
        #
        # We locate the row first.
        #
        # This is important because everything BELOW that row
        # is unrelated information and must never be treated
        # as country pricing.
        # ==================================================

        matching_all_other_indexes = []

        for row_index in range(
            data_start_index,
            len(
                worksheet_data.index
            )
        ):
            country_value = (
                worksheet_data.iloc[
                    row_index,
                    country_column_index
                ]
            )

            normalized_country = (
                self._normalize_phone_id_text(
                    country_value
                )
            )

            if (
                normalized_country.casefold()
                == all_other_country_value.casefold()
            ):
                matching_all_other_indexes.append(
                    row_index
                )

        if not matching_all_other_indexes:
            raise ValueError(
                f"Could not find "
                f"'{all_other_country_value}' "
                f"in worksheet '{worksheet_name}'."
            )

        if (
            len(
                matching_all_other_indexes
            )
            != 1
        ):
            raise ValueError(
                f"Expected exactly one "
                f"'{all_other_country_value}' row in "
                f"worksheet '{worksheet_name}', but found "
                f"{len(matching_all_other_indexes)}."
            )

        all_other_index = (
            matching_all_other_indexes[
                0
            ]
        )

        # ==================================================
        # READ ALL OTHERS
        # ==================================================

        all_other_source_row = (
            worksheet_data.iloc[
                all_other_index
            ]
        )

        all_other = (
            self._create_phone_id_suite_pricing_row(
                source_row=(
                    all_other_source_row
                ),
                header_indexes=(
                    header_indexes
                ),
                worksheet_schema=(
                    worksheet_schema
                ),
                excel_row_number=(
                    all_other_index + 1
                ),
                allow_blank_iso2=True
            )
        )

        all_other_price_fields = [
            "phone_id_standard",
            "phone_id_contact",
            "phone_id_contact_match",
            "phone_id_number_deactivation",
            "phone_id_porting_history",
            "phone_id_porting_status",
            "phone_id_sim_swap",
            "phone_id_subscriber_status",
            "phone_id_cfd",
            "phone_id_age_verify",
            "phone_id_breached_data",
            "phone_id_active_call_status"
        ]

        for pricing_field in (
            all_other_price_fields
        ):
            if (
                getattr(
                    all_other,
                    pricing_field
                )
                is None
            ):
                raise ValueError(
                    f"All other countries must contain "
                    f"a numeric price for every Phone ID "
                    f"Suite product. Field "
                    f"'{pricing_field}' is unavailable at "
                    f"worksheet row "
                    f"{all_other_index + 1}."
                )

        # ==================================================
        # READ COUNTRY ROWS
        #
        # Critical:
        #
        #     only rows BEFORE All Other Countries
        #
        # are ever processed.
        #
        # Anything below All Others is ignored.
        # ==================================================

        countries: list[
            PhoneIdSuitePricingRow
        ] = []

        seen_iso2: set[str] = set()

        for row_index in range(
            data_start_index,
            all_other_index
        ):
            source_row = (
                worksheet_data.iloc[
                    row_index
                ]
            )

            country_value = (
                source_row.iloc[
                    country_column_index
                ]
            )

            iso2_value = (
                source_row.iloc[
                    iso2_column_index
                ]
            )

            country = (
                self._normalize_phone_id_text(
                    country_value
                )
            )

            iso2 = (
                self._normalize_phone_id_text(
                    iso2_value
                )
            )

            # ----------------------------------------------
            # Completely blank line.
            #
            # The source contains blank rows before
            # All Other Countries.
            # ----------------------------------------------

            if (
                not country
                and not iso2
            ):
                continue

            # ----------------------------------------------
            # Ignore the special DOB variants.
            # ----------------------------------------------

            if (
                country.casefold()
                in excluded_country_values
            ):
                continue

            # ----------------------------------------------
            # A real country row must contain both Country
            # and ISO2.
            # ----------------------------------------------

            if not country:
                raise ValueError(
                    f"Phone ID Suite worksheet "
                    f"'{worksheet_name}' row "
                    f"{row_index + 1} contains an ISO2 "
                    f"but no country."
                )

            if not iso2:
                raise ValueError(
                    f"Phone ID Suite worksheet "
                    f"'{worksheet_name}' row "
                    f"{row_index + 1} contains country "
                    f"'{country}' but no ISO2."
                )

            normalized_iso2 = (
                iso2.upper()
            )

            # ----------------------------------------------
            # After excluding the Brazil / US DOB variants,
            # ISO2 should again be unique.
            # ----------------------------------------------

            if (
                normalized_iso2
                in seen_iso2
            ):
                raise ValueError(
                    f"Duplicate Phone ID Suite ISO2 "
                    f"'{normalized_iso2}' found at "
                    f"worksheet row "
                    f"{row_index + 1}."
                )

            pricing_row = (
                self._create_phone_id_suite_pricing_row(
                    source_row=source_row,
                    header_indexes=(
                        header_indexes
                    ),
                    worksheet_schema=(
                        worksheet_schema
                    ),
                    excel_row_number=(
                        row_index + 1
                    ),
                    allow_blank_iso2=False
                )
            )

            seen_iso2.add(
                normalized_iso2
            )

            countries.append(
                pricing_row
            )

        if not countries:
            raise RuntimeError(
                f"No Phone ID Suite country pricing "
                f"was found in worksheet "
                f"'{worksheet_name}'."
            )

        return PhoneIdSuitePricingData(
            all_other=all_other,
            countries=countries
        )

    def _read_phone_id_live_status_pricing(
        self,
        worksheet_name: str,
        worksheet_schema: dict
    ) -> PhoneIdLiveStatusPricingData:
        """
        Reads Phone ID Live Status source pricing.

        Structure:

            Row 13:
                headers

            Row 14:
                All Others

            Row 15 onward:
                countries
        """

        worksheet_data = (
            self._workbook_service
            .read_worksheet(
                worksheet_name
            )
        )

        # ==================================================
        # HEADERS
        # ==================================================

        header_indexes = (
            self._workbook_service
            .get_header_indexes_in_range(
                worksheet_data=(
                    worksheet_data
                ),
                worksheet_schema=(
                    worksheet_schema
                )
            )
        )

        # ==================================================
        # CONFIGURED ROWS
        # ==================================================

        all_other_row_number = (
            worksheet_schema[
                "all_other_countries_row"
            ]
        )

        data_start_row_number = (
            worksheet_schema[
                "data_start_row"
            ]
        )

        all_other_index = (
            all_other_row_number - 1
        )

        data_start_index = (
            data_start_row_number - 1
        )

        if (
            all_other_index < 0
            or all_other_index
            >= len(
                worksheet_data.index
            )
        ):
            raise ValueError(
                f"Configured Phone ID Live Status "
                f"All Others row "
                f"{all_other_row_number} is outside "
                f"worksheet '{worksheet_name}'."
            )

        if (
            data_start_index < 0
            or data_start_index
            >= len(
                worksheet_data.index
            )
        ):
            raise ValueError(
                f"Configured Phone ID Live Status "
                f"data start row "
                f"{data_start_row_number} is outside "
                f"worksheet '{worksheet_name}'."
            )

        # ==================================================
        # ALL OTHERS
        # ==================================================

        all_other_source_row = (
            worksheet_data.iloc[
                all_other_index
            ]
        )

        all_other = (
            self._create_phone_id_live_status_pricing_row(
                source_row=(
                    all_other_source_row
                ),
                header_indexes=(
                    header_indexes
                ),
                worksheet_name=(
                    worksheet_name
                ),
                excel_row_number=(
                    all_other_row_number
                ),
                allow_blank_iso2=True
            )
        )

        # ==================================================
        # COUNTRY ROWS
        # ==================================================

        countries: list[
            PhoneIdLiveStatusPricingRow
        ] = []

        seen_iso2: set[str] = set()

        country_column_index = (
            header_indexes[
                "country"
            ]
        )

        iso2_column_index = (
            header_indexes[
                "iso2"
            ]
        )

        for row_index in range(
            data_start_index,
            len(
                worksheet_data.index
            )
        ):
            source_row = (
                worksheet_data.iloc[
                    row_index
                ]
            )

            country = (
                self._normalize_phone_id_text(
                    source_row.iloc[
                        country_column_index
                    ]
                )
            )

            iso2 = (
                self._normalize_phone_id_text(
                    source_row.iloc[
                        iso2_column_index
                    ]
                )
            )

            # ----------------------------------------------
            # Completely blank rows are ignored.
            # ----------------------------------------------

            if (
                not country
                and not iso2
            ):
                continue

            if not country:
                raise ValueError(
                    f"Phone ID Live Status worksheet "
                    f"'{worksheet_name}' row "
                    f"{row_index + 1} contains an ISO2 "
                    f"but no country."
                )

            if not iso2:
                raise ValueError(
                    f"Phone ID Live Status worksheet "
                    f"'{worksheet_name}' row "
                    f"{row_index + 1} contains country "
                    f"'{country}' but no ISO2."
                )

            normalized_iso2 = (
                iso2.upper()
            )

            if (
                normalized_iso2
                in seen_iso2
            ):
                raise ValueError(
                    f"Duplicate Phone ID Live Status "
                    f"ISO2 '{normalized_iso2}' found "
                    f"at worksheet row "
                    f"{row_index + 1}."
                )

            pricing_row = (
                self._create_phone_id_live_status_pricing_row(
                    source_row=source_row,
                    header_indexes=(
                        header_indexes
                    ),
                    worksheet_name=(
                        worksheet_name
                    ),
                    excel_row_number=(
                        row_index + 1
                    ),
                    allow_blank_iso2=False
                )
            )

            countries.append(
                pricing_row
            )

            seen_iso2.add(
                normalized_iso2
            )

        if not countries:
            raise RuntimeError(
                f"No Phone ID Live Status country "
                f"pricing was found in worksheet "
                f"'{worksheet_name}'."
            )

        return PhoneIdLiveStatusPricingData(
            all_other=all_other,
            countries=countries
        )

    @staticmethod
    def _normalize_text_value(
        value: object
    ) -> str:
        """
        Converts a worksheet value into clean text.

        Blank or missing worksheet values become an empty string.

        Args:
            value:
                Raw worksheet cell value.

        Returns:
            Clean text value.
        """

        if value is None or pd.isna(value):
            return ""

        return str(value).strip()

    @staticmethod
    def _convert_price_to_decimal(
        value: object,
        field_name: str
    ) -> Decimal:
        """
        Converts a worksheet price value into Decimal.

        Args:
            value:
                Raw worksheet price value.

            field_name:
                Logical field name used in validation errors.

        Returns:
            Price represented as Decimal.

        Raises:
            ValueError:
                If the price is blank, Boolean, non-numeric,
                infinite or otherwise invalid.
        """

        if value is None or pd.isna(value):
            raise ValueError(
                f"Pricing value '{field_name}' cannot be blank."
            )

        if isinstance(value, bool):
            raise ValueError(
                f"Pricing value '{field_name}' must be numeric."
            )

        if isinstance(value, float):
            normalized_value = format(
                value,
                ".15g"
            )
        else:
            normalized_value = (
                str(value)
                .strip()
                .replace(",", "")
            )

        if not normalized_value:
            raise ValueError(
                f"Pricing value '{field_name}' cannot be blank."
            )

        try:
            decimal_value = Decimal(
                normalized_value
            )

        except InvalidOperation as error:
            raise ValueError(
                f"Pricing value '{field_name}' must be numeric. "
                f"Received: '{value}'."
            ) from error

        if not decimal_value.is_finite():
            raise ValueError(
                f"Pricing value '{field_name}' must be finite."
            )

        return decimal_value

    @staticmethod
    def _convert_optional_voice_inbound_price(
        value: object,
        field_name: str
    ) -> Decimal | None:
        """
        Converts a Voice inbound price into Decimal.

        The Voice source workbook may explicitly contain
        'not supported'. That value is represented as None so the
        generation layer can later apply the product-specific
        fallback rule.

        Blank inbound values are also represented as None.
        """

        if value is None or pd.isna(value):
            return None

        normalized_value = str(
            value
        ).strip()

        if not normalized_value:
            return None

        if normalized_value.casefold() == (
            "not supported"
        ):
            return None

        return PricingDataService._convert_price_to_decimal(
            value=value,
            field_name=field_name
        )

    @staticmethod
    def _convert_optional_mobile_price(
        value: object,
        field_name: str
    ) -> Decimal | None:
        """
        Converts one Mobile-product price to Decimal.

        Blank cells and 'not supported' values become None.
        Other non-numeric values remain errors.
        """

        if value is None or pd.isna(value):
            return None

        normalized_value = str(
            value
        ).strip()

        if not normalized_value:
            return None

        if (
            normalized_value.casefold()
            == "not supported"
        ):
            return None

        return PricingDataService._convert_price_to_decimal(
            value=value,
            field_name=field_name
        )

    @staticmethod
    def _convert_phone_id_suite_price(
        worksheet_value,
        unavailable_values: list[str],
        country: str,
        product_name: str,
        excel_row_number: int
    ) -> Decimal | None:
        """
        Converts one Phone ID Suite source price.

        Numeric value:
            Decimal

        n/a:
            None

        Upon request:
            None

        Blank:
            None

        Other non-numeric values:
            Error

        Negative:
            Error

        Blank pricing is treated as unavailable because the
        EUR and BRL Phone ID Suite sources use blank cells for
        some unavailable country/product combinations.

        All Others remains protected separately by
        _read_phone_id_suite_pricing(), which requires every
        All Others product price to be numeric.
        """

        if worksheet_value is None:
            normalized_text = ""

        else:
            try:
                if pd.isna(
                    worksheet_value
                ):
                    normalized_text = ""

                else:
                    normalized_text = (
                        str(
                            worksheet_value
                        )
                        .strip()
                    )

            except (
                TypeError,
                ValueError
            ):
                normalized_text = (
                    str(
                        worksheet_value
                    )
                    .strip()
                )

        # ==================================================
        # BLANK
        #
        # Phone ID Suite workbooks are not completely
        # consistent across currencies:
        #
        #     USD:
        #         commonly uses "n/a"
        #
        #     EUR / BRL:
        #         may use a blank cell
        #
        # Both represent an unavailable product for that
        # country.
        #
        # All Others is validated separately and must still
        # contain numeric pricing for every product.
        # ==================================================

        if not normalized_text:
            return None

        # ==================================================
        # CONFIGURED UNAVAILABLE VALUES
        #
        # Current configured values:
        #
        #     n/a
        #     Upon request
        #
        # Matching is case-insensitive and ignores surrounding
        # whitespace.
        # ==================================================

        normalized_unavailable_values = {
            str(
                value
            )
            .strip()
            .casefold()
            for value
            in unavailable_values
            if str(
                value
            ).strip()
        }

        if (
            normalized_text.casefold()
            in normalized_unavailable_values
        ):
            return None

        # ==================================================
        # NUMERIC PRICE
        # ==================================================

        try:
            price = Decimal(
                normalized_text
            )

        except (
            InvalidOperation,
            ValueError
        ) as error:
            raise ValueError(
                f"Invalid Phone ID Suite price "
                f"'{normalized_text}' for "
                f"'{country}' / '{product_name}' "
                f"at worksheet row "
                f"{excel_row_number}."
            ) from error

        if not price.is_finite():
            raise ValueError(
                f"Phone ID Suite price for "
                f"'{country}' / '{product_name}' "
                f"must be finite."
            )

        if price < Decimal("0"):
            raise ValueError(
                f"Phone ID Suite price for "
                f"'{country}' / '{product_name}' "
                f"cannot be negative."
            )

        return price

    @staticmethod
    def _convert_phone_id_live_status_price(
        worksheet_value,
        country: str,
        price_type: str,
        excel_row_number: int
    ) -> Decimal:
        """
        Converts one Phone ID Live Status price to Decimal.

        Live Status currently requires numeric pricing.
        Blank, n/a, Upon request or any other non-numeric
        source value is rejected.
        """

        if worksheet_value is None:
            normalized_text = ""

        else:
            try:
                import pandas as pd

                if pd.isna(
                    worksheet_value
                ):
                    normalized_text = ""

                else:
                    normalized_text = (
                        str(
                            worksheet_value
                        )
                        .strip()
                    )

            except (
                TypeError,
                ValueError
            ):
                normalized_text = (
                    str(
                        worksheet_value
                    )
                    .strip()
                )

        if not normalized_text:
            raise ValueError(
                f"Phone ID Live Status "
                f"{price_type} is blank for "
                f"'{country}' at worksheet row "
                f"{excel_row_number}."
            )

        try:
            price = Decimal(
                normalized_text
            )

        except (
            InvalidOperation,
            ValueError
        ) as error:
            raise ValueError(
                f"Invalid Phone ID Live Status "
                f"{price_type} "
                f"'{normalized_text}' for "
                f"'{country}' at worksheet row "
                f"{excel_row_number}."
            ) from error

        if not price.is_finite():
            raise ValueError(
                f"Phone ID Live Status "
                f"{price_type} for "
                f"'{country}' must be finite."
            )

        if price < Decimal("0"):
            raise ValueError(
                f"Phone ID Live Status "
                f"{price_type} for "
                f"'{country}' cannot be negative."
            )

        return price

    def _require_open_workbook(self) -> None:
        """
        Confirms that the workbook is still open.

        Raises:
            RuntimeError:
                If the workbook was closed after this service
                was created.
        """

        if not self._workbook_service.is_open:
            raise RuntimeError(
                "The pricing workbook is closed."
            )

    @staticmethod
    def _normalize_phone_id_text(
        worksheet_value
    ) -> str:
        """
        Converts a Phone ID worksheet text cell into a clean
        string.
        """

        if worksheet_value is None:
            return ""

        try:
            import pandas as pd

            if pd.isna(
                worksheet_value
            ):
                return ""

        except (
            TypeError,
            ValueError
        ):
            pass

        return str(
            worksheet_value
        ).strip()

    @staticmethod
    def _is_blank_pricing_row(
        worksheet_row: pd.Series,
        header_indexes: dict[str, int]
    ) -> bool:
        """
        Determines whether the relevant cells in a pricing row are
        all blank.

        The All Other Countries row is not considered blank because
        it contains pricing values even though Country and ISO2 are
        empty.

        Args:
            worksheet_row:
                Raw pandas worksheet row.

            header_indexes:
                Logical field-to-column mapping.

        Returns:
            True when every relevant field is blank.
        """

        relevant_fields = (
            "country",
            "iso2",
            "baseline_price",
            "enterprise_price"
        )

        relevant_values: list[object] = []

        for field_name in relevant_fields:
            if field_name not in header_indexes:
                continue

            relevant_values.append(
                worksheet_row.iloc[
                    header_indexes[field_name]
                ]
            )

        return all(
            value is None
            or pd.isna(value)
            or (
                isinstance(value, str)
                and not value.strip()
            )
            for value in relevant_values
        )

    @staticmethod
    def _is_blank_voice_pricing_row(
        worksheet_row: pd.Series,
        header_indexes: dict[str, int]
    ) -> bool:
        """
        Determines whether a worksheet row contains no usable
        Voice pricing data.

        Country is deliberately excluded from the check because
        Voice worksheets may contain footer or informational text
        in the Country column after the pricing table.

        A valid All Other Countries row is retained because it
        contains pricing values even when Country and ISO2 are blank.

        A real country row with an ISO2 or pricing data is also
        retained and will proceed through normal validation.
        """

        relevant_fields = (
            "iso2",
            "baseline_mobile_price",
            "baseline_landline_price",
            "baseline_inbound_price",
            "enterprise_mobile_price",
            "enterprise_landline_price",
            "enterprise_inbound_price",
            "number_type"
        )

        relevant_values: list[object] = []

        for field_name in relevant_fields:
            if field_name not in header_indexes:
                continue

            relevant_values.append(
                worksheet_row.iloc[
                    header_indexes[field_name]
                ]
            )

        return all(
            value is None
            or pd.isna(value)
            or (
                isinstance(value, str)
                and not value.strip()
            )
            for value in relevant_values
        )

    def _create_voice_verify_pricing_row(
        self,
        worksheet_row: pd.Series,
        header_indexes: dict[str, int]
    ) -> VoicePricingRow:
        """
        Converts one Voice Verify worksheet row into a
        VoicePricingRow.

        Voice Verify contains Mobile and Landline pricing but does
        not contain inbound pricing or number-type information.
        """

        required_fields = {
            "country",
            "iso2",
            "baseline_mobile_price",
            "baseline_landline_price",
            "enterprise_mobile_price",
            "enterprise_landline_price"
        }

        missing_fields = (
            required_fields
            - header_indexes.keys()
        )

        if missing_fields:
            missing_field_list = ", ".join(
                sorted(missing_fields)
            )

            raise ValueError(
                "Cannot create VoicePricingRow because required "
                f"field index(es) are missing: "
                f"{missing_field_list}."
            )

        country = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes["country"]
            ]
        )

        iso2 = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes["iso2"]
            ]
        )

        baseline_mobile_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_mobile_price"
                    ]
                ],
                "baseline_mobile_price"
            )
        )

        baseline_landline_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_landline_price"
                    ]
                ],
                "baseline_landline_price"
            )
        )

        enterprise_mobile_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_mobile_price"
                    ]
                ],
                "enterprise_mobile_price"
            )
        )

        enterprise_landline_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_landline_price"
                    ]
                ],
                "enterprise_landline_price"
            )
        )

        return VoicePricingRow(
            country=country,
            iso2=iso2,
            baseline_mobile_price=(
                baseline_mobile_price
            ),
            baseline_landline_price=(
                baseline_landline_price
            ),
            enterprise_mobile_price=(
                enterprise_mobile_price
            ),
            enterprise_landline_price=(
                enterprise_landline_price
            )
        )

    def _create_voice_api_pricing_row(
        self,
        worksheet_row: pd.Series,
        header_indexes: dict[str, int]
    ) -> VoicePricingRow:
        """
        Converts one Voice API worksheet row into VoicePricingRow.

        'not supported' inbound values become None.

        Number Type is retained exactly as source data so that the
        generation layer can later select the appropriate row.
        """

        required_fields = {
            "country",
            "iso2",
            "baseline_mobile_price",
            "baseline_landline_price",
            "baseline_inbound_price",
            "enterprise_mobile_price",
            "enterprise_landline_price",
            "enterprise_inbound_price",
            "number_type"
        }

        missing_fields = (
            required_fields
            - header_indexes.keys()
        )

        if missing_fields:
            missing_field_list = ", ".join(
                sorted(missing_fields)
            )

            raise ValueError(
                "Cannot create VoicePricingRow because required "
                f"Voice API field index(es) are missing: "
                f"{missing_field_list}."
            )

        country = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes["country"]
            ]
        )

        iso2 = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes["iso2"]
            ]
        )

        baseline_mobile_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_mobile_price"
                    ]
                ],
                "baseline_mobile_price"
            )
        )

        baseline_landline_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_landline_price"
                    ]
                ],
                "baseline_landline_price"
            )
        )

        baseline_inbound_price = (
            self._convert_optional_voice_inbound_price(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_inbound_price"
                    ]
                ],
                "baseline_inbound_price"
            )
        )

        enterprise_mobile_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_mobile_price"
                    ]
                ],
                "enterprise_mobile_price"
            )
        )

        enterprise_landline_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_landline_price"
                    ]
                ],
                "enterprise_landline_price"
            )
        )

        enterprise_inbound_price = (
            self._convert_optional_voice_inbound_price(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_inbound_price"
                    ]
                ],
                "enterprise_inbound_price"
            )
        )

        number_type = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes[
                    "number_type"
                ]
            ]
        )

        return VoicePricingRow(
            country=country,
            iso2=iso2,
            baseline_mobile_price=(
                baseline_mobile_price
            ),
            baseline_landline_price=(
                baseline_landline_price
            ),
            enterprise_mobile_price=(
                enterprise_mobile_price
            ),
            enterprise_landline_price=(
                enterprise_landline_price
            ),
            baseline_inbound_price=(
                baseline_inbound_price
            ),
            enterprise_inbound_price=(
                enterprise_inbound_price
            ),
            number_type=number_type
        )

    def _create_voice_verify_tts_pricing_row(
        self,
        worksheet_row: pd.Series,
        header_indexes: dict[str, int]
    ) -> VoicePricingRow:
        """
        Converts one Voice Verify + TTS worksheet row into
        VoicePricingRow.

        Blank or 'not supported' inbound prices become None.
        """

        required_fields = {
            "country",
            "iso2",
            "baseline_mobile_price",
            "baseline_landline_price",
            "baseline_inbound_price",
            "enterprise_mobile_price",
            "enterprise_landline_price",
            "enterprise_inbound_price"
        }

        missing_fields = (
            required_fields
            - header_indexes.keys()
        )

        if missing_fields:
            missing_field_list = ", ".join(
                sorted(missing_fields)
            )

            raise ValueError(
                "Cannot create VoicePricingRow because required "
                f"Voice Verify + TTS field index(es) are missing: "
                f"{missing_field_list}."
            )

        country = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes["country"]
            ]
        )

        iso2 = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes["iso2"]
            ]
        )

        baseline_mobile_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_mobile_price"
                    ]
                ],
                "baseline_mobile_price"
            )
        )

        baseline_landline_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_landline_price"
                    ]
                ],
                "baseline_landline_price"
            )
        )

        baseline_inbound_price = (
            self._convert_optional_voice_inbound_price(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_inbound_price"
                    ]
                ],
                "baseline_inbound_price"
            )
        )

        enterprise_mobile_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_mobile_price"
                    ]
                ],
                "enterprise_mobile_price"
            )
        )

        enterprise_landline_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_landline_price"
                    ]
                ],
                "enterprise_landline_price"
            )
        )

        enterprise_inbound_price = (
            self._convert_optional_voice_inbound_price(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_inbound_price"
                    ]
                ],
                "enterprise_inbound_price"
            )
        )

        return VoicePricingRow(
            country=country,
            iso2=iso2,
            baseline_mobile_price=(
                baseline_mobile_price
            ),
            baseline_landline_price=(
                baseline_landline_price
            ),
            enterprise_mobile_price=(
                enterprise_mobile_price
            ),
            enterprise_landline_price=(
                enterprise_landline_price
            ),
            baseline_inbound_price=(
                baseline_inbound_price
            ),
            enterprise_inbound_price=(
                enterprise_inbound_price
            )
        )

    def _create_toll_free_voice_pricing_row(
        self,
        worksheet_row: pd.Series,
        header_indexes: dict[str, int]
    ) -> VoicePricingRow:
        """
        Converts one Toll-Free Voice worksheet row into
        VoicePricingRow.

        Unlike Voice API and Voice Verify + TTS, Toll-Free Voice
        requires numeric inbound pricing for every row.
        """

        required_fields = {
            "country",
            "iso2",
            "baseline_mobile_price",
            "baseline_landline_price",
            "baseline_inbound_price",
            "enterprise_mobile_price",
            "enterprise_landline_price",
            "enterprise_inbound_price"
        }

        missing_fields = (
            required_fields
            - header_indexes.keys()
        )

        if missing_fields:
            missing_field_list = ", ".join(
                sorted(missing_fields)
            )

            raise ValueError(
                "Cannot create VoicePricingRow because required "
                f"Toll-Free Voice field index(es) are missing: "
                f"{missing_field_list}."
            )

        country = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes["country"]
            ]
        )

        iso2 = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes["iso2"]
            ]
        )

        baseline_mobile_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_mobile_price"
                    ]
                ],
                "baseline_mobile_price"
            )
        )

        baseline_landline_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_landline_price"
                    ]
                ],
                "baseline_landline_price"
            )
        )

        baseline_inbound_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_inbound_price"
                    ]
                ],
                "baseline_inbound_price"
            )
        )

        enterprise_mobile_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_mobile_price"
                    ]
                ],
                "enterprise_mobile_price"
            )
        )

        enterprise_landline_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_landline_price"
                    ]
                ],
                "enterprise_landline_price"
            )
        )

        enterprise_inbound_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_inbound_price"
                    ]
                ],
                "enterprise_inbound_price"
            )
        )

        return VoicePricingRow(
            country=country,
            iso2=iso2,
            baseline_mobile_price=(
                baseline_mobile_price
            ),
            baseline_landline_price=(
                baseline_landline_price
            ),
            enterprise_mobile_price=(
                enterprise_mobile_price
            ),
            enterprise_landline_price=(
                enterprise_landline_price
            ),
            baseline_inbound_price=(
                baseline_inbound_price
            ),
            enterprise_inbound_price=(
                enterprise_inbound_price
            )
        )

    def _create_mobile_pricing_row(
        self,
        worksheet_row: pd.Series,
        header_indexes: dict[str, int]
    ) -> MobilePricingRow:
        """
        Converts one Mobile SMS + Voice worksheet row into
        MobilePricingRow.

        'not supported' pricing values become None.
        """

        required_fields = {
            "country",
            "iso2",
            "baseline_sms_outbound_price",
            "baseline_sms_inbound_price",
            "baseline_voice_outbound_price",
            "baseline_voice_inbound_price",
            "enterprise_sms_outbound_price",
            "enterprise_sms_inbound_price",
            "enterprise_voice_outbound_price",
            "enterprise_voice_inbound_price"
        }

        missing_fields = (
            required_fields
            - header_indexes.keys()
        )

        if missing_fields:
            missing_field_list = ", ".join(
                sorted(
                    missing_fields
                )
            )

            raise ValueError(
                "Cannot create MobilePricingRow because required "
                f"field index(es) are missing: "
                f"{missing_field_list}."
            )

        country = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes["country"]
            ]
        )

        iso2 = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes["iso2"]
            ]
        )

        price_fields = (
            "baseline_sms_outbound_price",
            "baseline_sms_inbound_price",
            "baseline_voice_outbound_price",
            "baseline_voice_inbound_price",
            "enterprise_sms_outbound_price",
            "enterprise_sms_inbound_price",
            "enterprise_voice_outbound_price",
            "enterprise_voice_inbound_price"
        )

        prices: dict[
            str,
            Decimal | None
        ] = {}

        for field_name in price_fields:
            prices[field_name] = (
                self._convert_optional_mobile_price(
                    worksheet_row.iloc[
                        header_indexes[
                            field_name
                        ]
                    ],
                    field_name
                )
            )

        return MobilePricingRow(
            country=country,
            iso2=iso2,

            baseline_sms_outbound_price=(
                prices[
                    "baseline_sms_outbound_price"
                ]
            ),

            baseline_sms_inbound_price=(
                prices[
                    "baseline_sms_inbound_price"
                ]
            ),

            baseline_voice_outbound_price=(
                prices[
                    "baseline_voice_outbound_price"
                ]
            ),

            baseline_voice_inbound_price=(
                prices[
                    "baseline_voice_inbound_price"
                ]
            ),

            enterprise_sms_outbound_price=(
                prices[
                    "enterprise_sms_outbound_price"
                ]
            ),

            enterprise_sms_inbound_price=(
                prices[
                    "enterprise_sms_inbound_price"
                ]
            ),

            enterprise_voice_outbound_price=(
                prices[
                    "enterprise_voice_outbound_price"
                ]
            ),

            enterprise_voice_inbound_price=(
                prices[
                    "enterprise_voice_inbound_price"
                ]
            )
        )

    def _create_local_pricing_row(
        self,
        worksheet_row: pd.Series,
        header_indexes: dict[str, int],
        worksheet_schema: dict[str, Any]
    ) -> PricingRow:
        """
        Converts one Local pricing worksheet row into PricingRow.

        Country suffix processing is controlled by schemas.json.
        ISO2 is blank because Local worksheets do not contain it.
        """

        required_fields = {
            "country",
            "baseline_price",
            "enterprise_price"
        }

        missing_fields = (
            required_fields
            - header_indexes.keys()
        )

        if missing_fields:
            missing_field_list = ", ".join(
                sorted(missing_fields)
            )

            raise ValueError(
                "Cannot create local PricingRow because required "
                f"field index(es) are missing: "
                f"{missing_field_list}."
            )

        raw_country = worksheet_row.iloc[
            header_indexes["country"]
        ]

        if raw_country is None or pd.isna(raw_country):
            raise ValueError(
                "Local pricing country cannot be blank."
            )

        country_processing = worksheet_schema.get(
            "country_name_processing",
            {}
        )

        country = (
            WorkbookService.normalize_local_country_name(
                worksheet_value=raw_country,
                removable_suffix=(
                    country_processing.get(
                        "remove_suffix",
                        " - Local Companies"
                    )
                ),
                trim_whitespace=(
                    country_processing.get(
                        "trim_whitespace",
                        True
                    )
                )
            )
        )

        if not country:
            raise ValueError(
                "Local pricing country cannot be blank."
            )

        baseline_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes["baseline_price"]
                ],
                "baseline_price"
            )
        )

        enterprise_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes["enterprise_price"]
                ],
                "enterprise_price"
            )
        )

        return PricingRow(
            country=country,
            iso2="",
            baseline_price=baseline_price,
            enterprise_price=enterprise_price
        )

    def _create_pricing_row(
        self,
        worksheet_row: pd.Series,
        header_indexes: dict[str, int]
    ) -> PricingRow:
        """
        Converts one standard-pricing worksheet row into a
        PricingRow business object.

        Args:
            worksheet_row:
                One raw pandas worksheet row.

            header_indexes:
                Mapping from logical field names to DataFrame
                column indexes.

        Returns:
            Converted PricingRow.

        Raises:
            ValueError:
                If required logical fields or price values are
                missing or invalid.
        """

        required_fields = {
            "country",
            "iso2",
            "baseline_price",
            "enterprise_price"
        }

        missing_fields = (
            required_fields
            - header_indexes.keys()
        )

        if missing_fields:
            missing_field_list = ", ".join(
                sorted(missing_fields)
            )

            raise ValueError(
                "Cannot create PricingRow because required "
                f"field index(es) are missing: "
                f"{missing_field_list}."
            )

        country = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes["country"]
            ]
        )

        iso2 = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes["iso2"]
            ]
        )

        baseline_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_price"
                    ]
                ],
                "baseline_price"
            )
        )

        enterprise_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_price"
                    ]
                ],
                "enterprise_price"
            )
        )

        return PricingRow(
            country=country,
            iso2=iso2,
            baseline_price=baseline_price,
            enterprise_price=enterprise_price
        )

    def _create_whatsapp_pricing(
        self,
        worksheet_row: pd.Series,
        header_indexes: dict[str, int]
    ) -> WhatsAppPricing:
        """
        Converts the WhatsApp 'Other' worksheet row into
        WhatsAppPricing.
        """

        required_fields = {
            "market",
            "iso2",
            "baseline_price",
            "enterprise_price"
        }

        missing_fields = (
            required_fields
            - header_indexes.keys()
        )

        if missing_fields:
            missing_field_list = ", ".join(
                sorted(
                    missing_fields
                )
            )

            raise ValueError(
                "Cannot create WhatsAppPricing because "
                f"required field index(es) are missing: "
                f"{missing_field_list}."
            )

        market = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes[
                    "market"
                ]
            ]
        )

        iso2 = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes[
                    "iso2"
                ]
            ]
        )

        baseline_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_price"
                    ]
                ],
                "baseline_price"
            )
        )

        enterprise_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_price"
                    ]
                ],
                "enterprise_price"
            )
        )

        return WhatsAppPricing(
            market=market,
            iso2=iso2,
            baseline_price=baseline_price,
            enterprise_price=enterprise_price
        )

    def _create_viber_all_other_pricing(
        self,
        worksheet_row: pd.Series,
        header_indexes: dict[str, int]
    ) -> ViberAllOtherPricing:
        """
        Converts the Viber All Others row.

        Displayed C:F worksheet prices are the authoritative
        source for this row.
        """

        transactional_otp_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "displayed_transactional_otp_price"
                    ]
                ],
                "displayed_transactional_otp_price"
            )
        )

        promotional_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "displayed_promotional_price"
                    ]
                ],
                "displayed_promotional_price"
            )
        )

        session_chat_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "displayed_session_chat_price"
                    ]
                ],
                "displayed_session_chat_price"
            )
        )

        international_price = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "displayed_international_price"
                    ]
                ],
                "displayed_international_price"
            )
        )

        return ViberAllOtherPricing(
            transactional_otp_price=(
                transactional_otp_price
            ),
            promotional_price=(
                promotional_price
            ),
            session_chat_price=(
                session_chat_price
            ),
            international_price=(
                international_price
            )
        )

    def _create_viber_country_pricing_row(
        self,
        worksheet_row: pd.Series,
        header_indexes: dict[str, int]
    ) -> ViberCountryPricingRow:
        """
        Converts one individual Viber country row.

        Displayed C:F prices are deliberately ignored.
        Only Cost and DM source fields are retained.
        """

        country = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes[
                    "country"
                ]
            ]
        )

        iso2 = self._normalize_text_value(
            worksheet_row.iloc[
                header_indexes[
                    "iso2"
                ]
            ]
        )

        if not country:
            raise ValueError(
                "Viber country cannot be blank."
            )

        if not iso2:
            raise ValueError(
                f"Viber ISO2 cannot be blank for "
                f"country '{country}'."
            )

        transactional_otp_cost = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "transactional_otp_cost"
                    ]
                ],
                "transactional_otp_cost"
            )
        )

        promotional_cost = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "promotional_cost"
                    ]
                ],
                "promotional_cost"
            )
        )

        session_chat_cost = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "session_chat_cost"
                    ]
                ],
                "session_chat_cost"
            )
        )

        international_cost = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "international_cost"
                    ]
                ],
                "international_cost"
            )
        )

        baseline_dm = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "baseline_dm"
                    ]
                ],
                "baseline_dm"
            )
        )

        enterprise_dm = (
            self._convert_price_to_decimal(
                worksheet_row.iloc[
                    header_indexes[
                        "enterprise_dm"
                    ]
                ],
                "enterprise_dm"
            )
        )

        return ViberCountryPricingRow(
            country=country,
            iso2=iso2,

            transactional_otp_cost=(
                transactional_otp_cost
            ),

            promotional_cost=(
                promotional_cost
            ),

            session_chat_cost=(
                session_chat_cost
            ),

            international_cost=(
                international_cost
            ),

            baseline_dm=baseline_dm,
            enterprise_dm=enterprise_dm
        )

    def _create_phone_id_suite_pricing_row(
        self,
        source_row,
        header_indexes: dict[str, int],
        worksheet_schema: dict,
        excel_row_number: int,
        allow_blank_iso2: bool
    ) -> PhoneIdSuitePricingRow:
        """
        Converts one Phone ID Suite worksheet row into the
        immutable source model.
        """

        country = (
            self._normalize_phone_id_text(
                source_row.iloc[
                    header_indexes[
                        "country"
                    ]
                ]
            )
        )

        iso2 = (
            self._normalize_phone_id_text(
                source_row.iloc[
                    header_indexes[
                        "iso2"
                    ]
                ]
            )
        )

        if not country:
            raise ValueError(
                f"Phone ID Suite row "
                f"{excel_row_number} has no country."
            )

        if (
            not allow_blank_iso2
            and not iso2
        ):
            raise ValueError(
                f"Phone ID Suite row "
                f"{excel_row_number} for "
                f"'{country}' has no ISO2."
            )

        unavailable_values = [
            str(
                value
            ).strip()
            for value
            in worksheet_schema.get(
                "unavailable_values",
                [
                    "n/a",
                    "Upon request"
                ]
            )
            if str(
                value
            ).strip()
        ]

        return PhoneIdSuitePricingRow(
            country=country,
            iso2=iso2.upper(),

            phone_id_standard=(
                self._convert_phone_id_suite_price(
                    worksheet_value=(
                        source_row.iloc[
                            header_indexes[
                                "phone_id_standard"
                            ]
                        ]
                    ),
                    unavailable_values=(
                        unavailable_values
                    ),
                    country=country,
                    product_name=(
                        "Phone ID Standard"
                    ),
                    excel_row_number=(
                        excel_row_number
                    )
                )
            ),

            phone_id_contact=(
                self._convert_phone_id_suite_price(
                    worksheet_value=(
                        source_row.iloc[
                            header_indexes[
                                "phone_id_contact"
                            ]
                        ]
                    ),
                    unavailable_values=(
                        unavailable_values
                    ),
                    country=country,
                    product_name=(
                        "Phone ID Contact"
                    ),
                    excel_row_number=(
                        excel_row_number
                    )
                )
            ),

            phone_id_contact_match=(
                self._convert_phone_id_suite_price(
                    worksheet_value=(
                        source_row.iloc[
                            header_indexes[
                                "phone_id_contact_match"
                            ]
                        ]
                    ),
                    unavailable_values=(
                        unavailable_values
                    ),
                    country=country,
                    product_name=(
                        "Phone ID Contact Match"
                    ),
                    excel_row_number=(
                        excel_row_number
                    )
                )
            ),

            phone_id_number_deactivation=(
                self._convert_phone_id_suite_price(
                    worksheet_value=(
                        source_row.iloc[
                            header_indexes[
                                "phone_id_number_deactivation"
                            ]
                        ]
                    ),
                    unavailable_values=(
                        unavailable_values
                    ),
                    country=country,
                    product_name=(
                        "Phone ID Number Deactivation"
                    ),
                    excel_row_number=(
                        excel_row_number
                    )
                )
            ),

            phone_id_porting_history=(
                self._convert_phone_id_suite_price(
                    worksheet_value=(
                        source_row.iloc[
                            header_indexes[
                                "phone_id_porting_history"
                            ]
                        ]
                    ),
                    unavailable_values=(
                        unavailable_values
                    ),
                    country=country,
                    product_name=(
                        "Phone ID Porting History"
                    ),
                    excel_row_number=(
                        excel_row_number
                    )
                )
            ),

            phone_id_porting_status=(
                self._convert_phone_id_suite_price(
                    worksheet_value=(
                        source_row.iloc[
                            header_indexes[
                                "phone_id_porting_status"
                            ]
                        ]
                    ),
                    unavailable_values=(
                        unavailable_values
                    ),
                    country=country,
                    product_name=(
                        "Phone ID Porting Status"
                    ),
                    excel_row_number=(
                        excel_row_number
                    )
                )
            ),

            phone_id_sim_swap=(
                self._convert_phone_id_suite_price(
                    worksheet_value=(
                        source_row.iloc[
                            header_indexes[
                                "phone_id_sim_swap"
                            ]
                        ]
                    ),
                    unavailable_values=(
                        unavailable_values
                    ),
                    country=country,
                    product_name=(
                        "Phone ID SIM Swap"
                    ),
                    excel_row_number=(
                        excel_row_number
                    )
                )
            ),

            phone_id_subscriber_status=(
                self._convert_phone_id_suite_price(
                    worksheet_value=(
                        source_row.iloc[
                            header_indexes[
                                "phone_id_subscriber_status"
                            ]
                        ]
                    ),
                    unavailable_values=(
                        unavailable_values
                    ),
                    country=country,
                    product_name=(
                        "Phone ID Subscriber Status"
                    ),
                    excel_row_number=(
                        excel_row_number
                    )
                )
            ),

            phone_id_cfd=(
                self._convert_phone_id_suite_price(
                    worksheet_value=(
                        source_row.iloc[
                            header_indexes[
                                "phone_id_cfd"
                            ]
                        ]
                    ),
                    unavailable_values=(
                        unavailable_values
                    ),
                    country=country,
                    product_name=(
                        "Phone ID CFD"
                    ),
                    excel_row_number=(
                        excel_row_number
                    )
                )
            ),

            phone_id_age_verify=(
                self._convert_phone_id_suite_price(
                    worksheet_value=(
                        source_row.iloc[
                            header_indexes[
                                "phone_id_age_verify"
                            ]
                        ]
                    ),
                    unavailable_values=(
                        unavailable_values
                    ),
                    country=country,
                    product_name=(
                        "Phone ID Age Verify"
                    ),
                    excel_row_number=(
                        excel_row_number
                    )
                )
            ),

            phone_id_breached_data=(
                self._convert_phone_id_suite_price(
                    worksheet_value=(
                        source_row.iloc[
                            header_indexes[
                                "phone_id_breached_data"
                            ]
                        ]
                    ),
                    unavailable_values=(
                        unavailable_values
                    ),
                    country=country,
                    product_name=(
                        "Phone ID Breached Data"
                    ),
                    excel_row_number=(
                        excel_row_number
                    )
                )
            ),

            phone_id_active_call_status=(
                self._convert_phone_id_suite_price(
                    worksheet_value=(
                        source_row.iloc[
                            header_indexes[
                                "phone_id_active_call_status"
                            ]
                        ]
                    ),
                    unavailable_values=(
                        unavailable_values
                    ),
                    country=country,
                    product_name=(
                        "Phone ID Active Call Status"
                    ),
                    excel_row_number=(
                        excel_row_number
                    )
                )
            )
        )

    def _create_phone_id_live_status_pricing_row(
        self,
        source_row,
        header_indexes: dict[str, int],
        worksheet_name: str,
        excel_row_number: int,
        allow_blank_iso2: bool
    ) -> PhoneIdLiveStatusPricingRow:
        """
        Converts one Phone ID Live Status source row.
        """

        country = (
            self._normalize_phone_id_text(
                source_row.iloc[
                    header_indexes[
                        "country"
                    ]
                ]
            )
        )

        iso2 = (
            self._normalize_phone_id_text(
                source_row.iloc[
                    header_indexes[
                        "iso2"
                    ]
                ]
            )
        )

        if not country:
            raise ValueError(
                f"Phone ID Live Status worksheet "
                f"'{worksheet_name}' row "
                f"{excel_row_number} has no country."
            )

        if (
            not allow_blank_iso2
            and not iso2
        ):
            raise ValueError(
                f"Phone ID Live Status worksheet "
                f"'{worksheet_name}' row "
                f"{excel_row_number} for "
                f"'{country}' has no ISO2."
            )

        mobile_price = (
            self._convert_phone_id_live_status_price(
                worksheet_value=(
                    source_row.iloc[
                        header_indexes[
                            "mobile_price"
                        ]
                    ]
                ),
                country=country,
                price_type=(
                    "Mobile Price"
                ),
                excel_row_number=(
                    excel_row_number
                )
            )
        )

        landline_price = (
            self._convert_phone_id_live_status_price(
                worksheet_value=(
                    source_row.iloc[
                        header_indexes[
                            "landline_price"
                        ]
                    ]
                ),
                country=country,
                price_type=(
                    "Landline Price"
                ),
                excel_row_number=(
                    excel_row_number
                )
            )
        )

        return PhoneIdLiveStatusPricingRow(
            country=country,
            iso2=iso2.upper(),
            mobile_price=(
                mobile_price
            ),
            landline_price=(
                landline_price
            )
        )

    