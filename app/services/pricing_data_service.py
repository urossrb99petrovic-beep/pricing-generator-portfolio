from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd

from app.models.pricing_row import PricingRow
from app.services.workbook_service import WorkbookService
from app.models.sender_override_price import (
    SenderOverridePrice
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

    STANDARD_PRICING_SCHEMA = "standard_pricing_worksheet"
    LOCAL_PRICING_SCHEMA = "local_pricing_worksheet"
    SENDER_OVERRIDE_SCHEMA = "sender_override_worksheet"


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