from pathlib import Path
from typing import Any
from datetime import date
import re

from app.models.application_config import ApplicationConfig
from app.models.generation_request import GenerationRequest
from app.models.generation_result import GenerationResult
from app.services.csv_export_service import CsvExportService
from app.services.generation_engine import GenerationEngine
from app.services.pricing_data_service import (
    PricingDataService
)
from app.services.pricing_generation_service import (
    PricingGenerationService
)
from app.services.workbook_service import WorkbookService
from app.utils.path_resolver import PathResolver
from app.services.logging_service import LoggingService

from app.models.generated_voice_pricing_row import (
    GeneratedVoicePricingRow
)
from app.services.voice_csv_export_service import (
    VoiceCsvExportService
)
from app.services.voice_csv_row_builder import (
    VoiceCsvRowBuilder
)
from app.models.generated_mobile_pricing import (
    GeneratedMobilePricing
)
from app.models.mobile_generation_result import (
    MobileGenerationResult
)
from app.services.mobile_csv_export_service import (
    MobileCsvExportService
)
from app.models.generated_viber_pricing_row import (
    GeneratedViberPricingRow
)

from app.services.viber_csv_row_builder import (
    ViberCsvRowBuilder
)

from app.services.viber_csv_export_service import (
    ViberCsvExportService
)
from app.models.generated_phone_id_suite_pricing import (
    GeneratedPhoneIdSuitePricing
)

from app.models.phone_id_suite_generation_result import (
    PhoneIdSuiteGenerationResult
)



class PricingGeneratorController:
    """
    Coordinates GUI generation requests with the pricing
    backend and CSV export.
    """

    def __init__(
        self,
        application_config: ApplicationConfig,
        path_resolver: PathResolver,
        logging_service: LoggingService
    ) -> None:
        """
        Creates the controller.

        Args:
            application_config:
                Loaded application configuration.

            path_resolver:
                Initialized application path resolver.
        """

        self._application_config = application_config
        self._path_resolver = path_resolver
        self._logging_service = logging_service

        self._products_by_id = (
            self._build_product_mapping()
        )

    def generate_pricing(
            self,
            request: GenerationRequest
        ) -> tuple[
            GenerationResult
            | MobileGenerationResult
            | PhoneIdSuiteGenerationResult,
            Path | dict[str, Path]
        ]:
            """
            Generates final pricing, exports the required CSV and
            records the generation attempt.

            SMS products continue to use CsvExportService.

            Voice Verify uses the configured Voice output schema and
            VoiceCsvExportService.

            Logging failures never prevent successful pricing
            generation or hide the original generation error.
            """

            try:
                self._validate_request(
                    request
                )

                product_config = (
                    self._products_by_id[
                        request.product_id
                    ]
                )

                workbook_path = (
                    self._resolve_workbook_path(
                        currency=request.currency,
                        product_config=product_config
                    )
                )

                workbook_schemas = (
                    self._application_config.schemas[
                        "workbook_schemas"
                    ]
                )

                sender_overrides_config = (
                    self._application_config.countries[
                        "sender_overrides"
                    ]
                )

                with WorkbookService(
                    workbook_path
                ) as workbook_service:

                    pricing_data_service = (
                        PricingDataService(
                            workbook_service=workbook_service,
                            workbook_schemas=(
                                workbook_schemas
                            )
                        )
                    )

                    pricing_generation_service = (
                        PricingGenerationService(
                            pricing_data_service=(
                                pricing_data_service
                            ),
                            generation_engine=(
                                GenerationEngine()
                            ),
                            sender_overrides_config=(
                                sender_overrides_config
                            )
                        )
                    )

                    generated_rows = (
                        pricing_generation_service
                        .generate_product_pricing(
                            product_config=product_config,
                            pricing_type=(
                                request.pricing_type
                            ),
                            selected_sender_ids=(
                                request.sender_ids
                            ),
                            selected_local_countries=(
                                request.local_countries
                            ),
                            selected_product_options=(
                                request.product_options
                            ),
                            selected_subproducts=(
                                request.selected_subproducts
                            )
                        )
                    )

                if request.product_id == "MOBILE_SMS_VOICE":
                    if not isinstance(
                        generated_rows,
                        GeneratedMobilePricing
                    ):
                        raise ValueError(
                            "Mobile generation returned an unexpected "
                            "result type."
                        )

                    traffic_type = (
                        request.product_options[
                            "traffic_type"
                        ]
                    )

                    mobile_generation_result = (
                        MobileGenerationResult(
                            currency=request.currency,
                            product_id=request.product_id,
                            product_output_name=(
                                product_config[
                                    "output_name"
                                ]
                            ),
                            pricing_type=request.pricing_type,
                            traffic_type=traffic_type,
                            pricing=generated_rows
                        )
                    )

                    mobile_output_paths = (
                        self._export_mobile_sms_voice(
                            request=request,
                            generation_result=(
                                mobile_generation_result
                            )
                        )
                    )

                    try:
                        self._log_mobile_success(
                            request=request,
                            generation_result=(
                                mobile_generation_result
                            ),
                            output_paths=(
                                mobile_output_paths
                            )
                        )

                    except Exception:
                        # Logging must never turn a successful generation
                        # into a failed generation.
                        pass

                    return (
                        mobile_generation_result,
                        mobile_output_paths
                    )

                # ==================================================
                # PHONE ID SUITE
                #
                # One request can create between 1 and 12 physical
                # SMS-template CSV files.
                # ==================================================

                if request.product_id == "PHONE_ID_SUITE":

                    if not isinstance(
                        generated_rows,
                        GeneratedPhoneIdSuitePricing
                    ):
                        raise ValueError(
                            "Phone ID Suite generation returned an "
                            "unexpected result type."
                        )

                    phone_id_generation_result = (
                        PhoneIdSuiteGenerationResult(
                            currency=request.currency,
                            product_id=request.product_id,
                            product_output_name=(
                                product_config[
                                    "output_name"
                                ]
                            ),
                            pricing_type=None,
                            pricing=generated_rows
                        )
                    )

                    phone_id_output_paths = (
                        self._export_phone_id_suite(
                            request=request,
                            product_config=product_config,
                            generation_result=(
                                phone_id_generation_result
                            )
                        )
                    )

                    try:
                        self._log_phone_id_suite_success(
                            request=request,
                            product_config=product_config,
                            generation_result=(
                                phone_id_generation_result
                            ),
                            output_paths=(
                                phone_id_output_paths
                            )
                        )

                    except Exception:
                        # Logging must never turn successful pricing
                        # generation into a failed generation.
                        pass

                    return (
                        phone_id_generation_result,
                        phone_id_output_paths
                    )

                product_output_name = (
                    product_config[
                        "output_name"
                    ]
                )

                if request.product_id == "VOICE_VERIFY":
                    billing_type = (
                        request.product_options[
                            "billing_type"
                        ]
                    )

                    billing_display_name = (
                        self._get_product_option_display_name(
                            product_config=product_config,
                            option_id="billing_type",
                            selected_value=billing_type
                        )
                    )

                    product_output_name = (
                        f"{product_output_name} - "
                        f"{billing_display_name}"
                    )
                elif request.product_id == "VOICE":
                    traffic_type = (
                        request.product_options[
                            "traffic_type"
                        ]
                    )

                    number_type = (
                        request.product_options[
                            "number_type"
                        ]
                    )

                    traffic_display_name = (
                        self._get_product_option_display_name(
                            product_config=product_config,
                            option_id="traffic_type",
                            selected_value=traffic_type
                        )
                    )

                    number_type_display_name = (
                        self._get_product_option_display_name(
                            product_config=product_config,
                            option_id="number_type",
                            selected_value=number_type
                        )
                    )

                    product_output_name = (
                        f"{product_output_name} - "
                        f"{traffic_display_name} - "
                        f"{number_type_display_name}"
                    )

                elif request.product_id == "VOICE_VERIFY_TTS":
                    traffic_type = (
                        request.product_options[
                            "traffic_type"
                        ]
                    )

                    traffic_display_name = (
                        self._get_product_option_display_name(
                            product_config=product_config,
                            option_id="traffic_type",
                            selected_value=traffic_type
                        )
                    )

                    product_output_name = (
                        f"{product_output_name} - "
                        f"{traffic_display_name}"
                    )

                generation_result = GenerationResult(
                    currency=request.currency,
                    product_id=request.product_id,
                    product_output_name=(
                        product_output_name
                    ),
                    pricing_type=request.pricing_type,
                    rows=generated_rows
                )

                if request.product_id == "VOICE_VERIFY":
                    output_path = (
                        self._export_voice_verify(
                            request=request,
                            product_config=product_config,
                            generation_result=(
                                generation_result
                            )
                        )
                    )

                elif request.product_id == "VOICE":
                    output_path = (
                        self._export_voice(
                            request=request,
                            generation_result=(
                                generation_result
                            )
                        )
                    )

                elif request.product_id == "VOICE_VERIFY_TTS":
                    output_path = (
                        self._export_voice_verify_tts(
                            request=request,
                            generation_result=(
                                generation_result
                            )
                        )
                    )

                elif request.product_id == "TOLL_FREE_VOICE":
                    output_path = (
                        self._export_toll_free_voice(
                            request=request,
                            generation_result=(
                                generation_result
                            )
                        )
                    )

                elif request.product_id == "PHONE_ID_LIVE_STATUS":
                    output_path = (
                        self._export_phone_id_live_status(
                            request=request,
                            generation_result=(
                                generation_result
                            )
                        )
                    )

                elif request.product_id == "VIBER":
                    output_path = (
                        self._export_viber(
                            request=request,
                            generation_result=(
                                generation_result
                            )
                        )
                    )

                else:
                    csv_export_service = CsvExportService(
                        path_resolver=self._path_resolver,
                        output_settings=(
                            self._application_config.settings[
                                "output"
                            ]
                        ),
                        output_csv_schema=(
                            self._application_config.schemas[
                                "output_csv_schema"
                            ]
                        ),
                        country_name_corrections=(
                            self._application_config.countries.get(
                                "country_name_corrections",
                                {}
                            )
                        )
                    )

                    output_path = (
                        csv_export_service.export(
                            generation_result
                        )
                    )

            except Exception as error:
                try:
                    self._logging_service.log_failure(
                        currency=request.currency,
                        product=request.product_id,
                        pricing_type=request.pricing_type,
                        sender_ids=request.sender_ids,
                        local_countries=request.local_countries,
                        error=error
                    )

                except Exception:
                    pass

                raise

            try:
                self._logging_service.log_success(
                    currency=request.currency,
                    product=(
                        generation_result
                        .product_output_name
                    ),
                    pricing_type=request.pricing_type,
                    sender_ids=request.sender_ids,
                    local_countries=request.local_countries,
                    rows_generated=len(
                        generation_result.rows
                    ),
                    output_file=output_path
                )

            except Exception:
                pass

            return (
                generation_result,
                output_path
            )

    def _export_voice_verify(
        self,
        request: GenerationRequest,
        product_config: dict[str, Any],
        generation_result: GenerationResult
    ) -> Path:
        """
        Exports Voice Verify using the schema determined by the
        selected Billing Type.
        """

        billing_type = (
            request.product_options[
                "billing_type"
            ]
        )

        schema_rule = (
            self._application_config.schemas[
                "output_schema_rules"
            ][
                "VOICE_VERIFY"
            ]
        )

        schema_id = (
            schema_rule[
                "mappings"
            ].get(
                billing_type
            )
        )

        if not schema_id:
            raise ValueError(
                f"No Voice Verify output schema is configured "
                f"for billing type '{billing_type}'."
            )

        voice_row_builder = (
            VoiceCsvRowBuilder(
                voice_output_csv_schemas=(
                    self._application_config.schemas[
                        "voice_output_csv_schemas"
                    ]
                ),
                country_name_corrections=(
                    self._application_config.countries.get(
                        "country_name_corrections",
                        {}
                    )
                )
            )
        )

        voice_export_service = (
            VoiceCsvExportService(
                voice_csv_row_builder=(
                    voice_row_builder
                ),
                output_settings=(
                    self._application_config.settings[
                        "output"
                    ]
                )
            )
        )

        output_path = self._build_output_path(
            currency=request.currency,
            product_output_name=(
                generation_result
                .product_output_name
            ),
            pricing_type=request.pricing_type
        )

        voice_rows = generation_result.rows

        if not all(
            isinstance(
                row,
                GeneratedVoicePricingRow
            )
            for row in voice_rows
        ):
            raise ValueError(
                "Voice Verify generation contains an "
                "unexpected row type."
            )

        return voice_export_service.export(
            generated_rows=voice_rows,
            schema_id=schema_id,
            output_path=output_path
        )

    def _export_voice(
        self,
        request: GenerationRequest,
        generation_result: GenerationResult
    ) -> Path:
        """
        Exports Voice API pricing using the output schema
        determined by the selected Traffic Type.

        ONE_WAY:
            voice_one_way

        TWO_WAY:
            voice_two_way
        """

        traffic_type = (
            request.product_options[
                "traffic_type"
            ]
        )

        schema_rule = (
            self._application_config.schemas[
                "output_schema_rules"
            ][
                "VOICE"
            ]
        )

        schema_id = (
            schema_rule[
                "mappings"
            ].get(
                traffic_type
            )
        )

        if not schema_id:
            raise ValueError(
                f"No Voice output schema is configured "
                f"for traffic type '{traffic_type}'."
            )

        voice_rows = (
            generation_result.rows
        )

        if not all(
            isinstance(
                row,
                GeneratedVoicePricingRow
            )
            for row in voice_rows
        ):
            raise ValueError(
                "Voice generation contains an "
                "unexpected row type."
            )

        voice_row_builder = (
            VoiceCsvRowBuilder(
                voice_output_csv_schemas=(
                    self._application_config.schemas[
                        "voice_output_csv_schemas"
                    ]
                ),
                country_name_corrections=(
                    self._application_config.countries.get(
                        "country_name_corrections",
                        {}
                    )
                )
            )
        )

        voice_export_service = (
            VoiceCsvExportService(
                voice_csv_row_builder=(
                    voice_row_builder
                ),
                output_settings=(
                    self._application_config.settings[
                        "output"
                    ]
                )
            )
        )

        output_path = (
            self._build_output_path(
                currency=request.currency,
                product_output_name=(
                    generation_result
                    .product_output_name
                ),
                pricing_type=request.pricing_type
            )
        )

        return (
            voice_export_service.export(
                generated_rows=voice_rows,
                schema_id=schema_id,
                output_path=output_path
            )
        )

    def _export_voice_verify_tts(
        self,
        request: GenerationRequest,
        generation_result: GenerationResult
    ) -> Path:
        """
        Exports Voice Verify + TTS using the Voice schema
        determined by the selected Traffic Type.

        ONE_WAY:
            voice_one_way

        TWO_WAY:
            voice_two_way
        """

        traffic_type = (
            request.product_options[
                "traffic_type"
            ]
        )

        schema_rule = (
            self._application_config.schemas[
                "output_schema_rules"
            ][
                "VOICE_VERIFY_TTS"
            ]
        )

        schema_id = (
            schema_rule[
                "mappings"
            ].get(
                traffic_type
            )
        )

        if not schema_id:
            raise ValueError(
                f"No Voice Verify + TTS output schema is "
                f"configured for traffic type "
                f"'{traffic_type}'."
            )

        voice_rows = (
            generation_result.rows
        )

        if not all(
            isinstance(
                row,
                GeneratedVoicePricingRow
            )
            for row in voice_rows
        ):
            raise ValueError(
                "Voice Verify + TTS generation contains "
                "an unexpected row type."
            )

        voice_row_builder = (
            VoiceCsvRowBuilder(
                voice_output_csv_schemas=(
                    self._application_config.schemas[
                        "voice_output_csv_schemas"
                    ]
                ),
                country_name_corrections=(
                    self._application_config.countries.get(
                        "country_name_corrections",
                        {}
                    )
                )
            )
        )

        voice_export_service = (
            VoiceCsvExportService(
                voice_csv_row_builder=(
                    voice_row_builder
                ),
                output_settings=(
                    self._application_config.settings[
                        "output"
                    ]
                )
            )
        )

        output_path = (
            self._build_output_path(
                currency=request.currency,
                product_output_name=(
                    generation_result
                    .product_output_name
                ),
                pricing_type=request.pricing_type
            )
        )

        return (
            voice_export_service.export(
                generated_rows=voice_rows,
                schema_id=schema_id,
                output_path=output_path
            )
        )

    def _export_toll_free_voice(
        self,
        request: GenerationRequest,
        generation_result: GenerationResult
    ) -> Path:
        """
        Exports Toll-Free Voice using the fixed 2-Way Voice
        output schema.
        """

        schema_rule = (
            self._application_config.schemas[
                "output_schema_rules"
            ][
                "TOLL_FREE_VOICE"
            ]
        )

        schema_id = (
            schema_rule.get(
                "fixed_schema"
            )
        )

        if not schema_id:
            raise ValueError(
                "No fixed Toll-Free Voice output schema "
                "is configured."
            )

        voice_rows = (
            generation_result.rows
        )

        if not all(
            isinstance(
                row,
                GeneratedVoicePricingRow
            )
            for row in voice_rows
        ):
            raise ValueError(
                "Toll-Free Voice generation contains an "
                "unexpected row type."
            )

        voice_row_builder = (
            VoiceCsvRowBuilder(
                voice_output_csv_schemas=(
                    self._application_config.schemas[
                        "voice_output_csv_schemas"
                    ]
                ),
                country_name_corrections=(
                    self._application_config.countries.get(
                        "country_name_corrections",
                        {}
                    )
                )
            )
        )

        voice_export_service = (
            VoiceCsvExportService(
                voice_csv_row_builder=(
                    voice_row_builder
                ),
                output_settings=(
                    self._application_config.settings[
                        "output"
                    ]
                )
            )
        )

        output_path = (
            self._build_output_path(
                currency=request.currency,
                product_output_name=(
                    generation_result
                    .product_output_name
                ),
                pricing_type=request.pricing_type
            )
        )

        return (
            voice_export_service.export(
                generated_rows=voice_rows,
                schema_id=schema_id,
                output_path=output_path
            )
        )

    def _export_mobile_sms_voice(
        self,
        request: GenerationRequest,
        generation_result: MobileGenerationResult
    ) -> dict[str, Path]:
        """
        Exports all files required by one Mobile
        (SMS and Voice) request.

        ONE_WAY:
            SMS Outbound
            Voice 1-Way

        TWO_WAY:
            SMS Outbound
            SMS Inbound
            Voice 2-Way
        """

        traffic_type = (
            generation_result.traffic_type
        )

        voice_schema_id = (
            self._get_mobile_voice_schema_id(
                traffic_type
            )
        )

        sms_export_service = (
            CsvExportService(
                path_resolver=self._path_resolver,
                output_settings=(
                    self._application_config.settings[
                        "output"
                    ]
                ),
                output_csv_schema=(
                    self._application_config.schemas[
                        "output_csv_schema"
                    ]
                ),
                country_name_corrections=(
                    self._application_config.countries.get(
                        "country_name_corrections",
                        {}
                    )
                )
            )
        )

        voice_row_builder = (
            VoiceCsvRowBuilder(
                voice_output_csv_schemas=(
                    self._application_config.schemas[
                        "voice_output_csv_schemas"
                    ]
                ),
                country_name_corrections=(
                    self._application_config.countries.get(
                        "country_name_corrections",
                        {}
                    )
                )
            )
        )

        voice_export_service = (
            VoiceCsvExportService(
                voice_csv_row_builder=(
                    voice_row_builder
                ),
                output_settings=(
                    self._application_config.settings[
                        "output"
                    ]
                )
            )
        )

        mobile_export_service = (
            MobileCsvExportService(
                sms_csv_export_service=(
                    sms_export_service
                ),
                voice_csv_export_service=(
                    voice_export_service
                ),
                output_path_builder=(
                    self._build_output_path
                )
            )
        )

        return (
            mobile_export_service.export(
                generated_pricing=(
                    generation_result.pricing
                ),
                currency=request.currency,
                product_id=request.product_id,
                product_output_name=(
                    generation_result
                    .product_output_name
                ),
                pricing_type=request.pricing_type,
                traffic_type=traffic_type,
                voice_schema_id=voice_schema_id
            )
        )

    def _export_viber(
        self,
        request: GenerationRequest,
        generation_result: GenerationResult
    ) -> Path:
        """
        Exports generated Viber pricing using the dedicated
        Viber upload template.
        """

        if not generation_result.rows:
            raise ValueError(
                "Viber generation returned no pricing rows."
            )

        for row_index, generated_row in enumerate(
            generation_result.rows,
            start=1
        ):
            if not isinstance(
                generated_row,
                GeneratedViberPricingRow
            ):
                raise ValueError(
                    f"Viber generation row {row_index} "
                    f"has an unexpected result type."
                )

        viber_row_builder = (
            ViberCsvRowBuilder(
                output_schema=(
                    self._application_config.schemas[
                        "viber_output_csv_schema"
                    ]
                )
            )
        )

        viber_export_service = (
            ViberCsvExportService(
                row_builder=(
                    viber_row_builder
                ),
                output_settings=(
                    self._application_config.settings[
                        "output"
                    ]
                )
            )
        )

        output_path = (
            self._build_output_path(
                currency=request.currency,
                product_output_name=(
                    generation_result
                    .product_output_name
                ),
                pricing_type=(
                    request.pricing_type
                )
            )
        )

        return (
            viber_export_service.export(
                pricing_rows=(
                    generation_result.rows
                ),
                output_path=output_path
            )
        )

    def _export_phone_id_suite(
        self,
        request: GenerationRequest,
        product_config: dict[str, Any],
        generation_result: PhoneIdSuiteGenerationResult
    ) -> dict[str, Path]:
        """
        Exports every selected Phone ID Suite subproduct as its
        own physical SMS-template CSV file.

        Example:

            PHONE_ID_STANDARD
                -> USD - Phone ID Standard
                - template Aug 2026.csv

            PHONE_ID_SIM_SWAP
                -> USD - Phone ID SIM Swap
                - template Aug 2026.csv
        """

        rows_by_subproduct = (
            generation_result
            .pricing
            .rows_by_subproduct
        )

        if not rows_by_subproduct:
            raise ValueError(
                "Phone ID Suite generation contains no "
                "subproduct outputs."
            )

        # ==================================================
        # CONFIGURED SUBPRODUCTS
        # ==================================================

        configured_subproducts = (
            product_config.get(
                "subproducts",
                []
            )
        )

        subproducts_by_id: dict[
            str,
            dict[str, Any]
        ] = {}

        for subproduct_config in (
            configured_subproducts
        ):
            subproduct_id = (
                str(
                    subproduct_config.get(
                        "product_id",
                        ""
                    )
                )
                .strip()
            )

            if not subproduct_id:
                raise ValueError(
                    "Phone ID Suite contains a configured "
                    "subproduct without a product_id."
                )

            if (
                subproduct_id
                in subproducts_by_id
            ):
                raise ValueError(
                    f"Phone ID Suite contains duplicate "
                    f"subproduct configuration "
                    f"'{subproduct_id}'."
                )

            subproducts_by_id[
                subproduct_id
            ] = subproduct_config

        # ==================================================
        # REUSE EXISTING SMS TEMPLATE EXPORTER
        # ==================================================

        csv_export_service = (
            CsvExportService(
                path_resolver=(
                    self._path_resolver
                ),
                output_settings=(
                    self._application_config.settings[
                        "output"
                    ]
                ),
                output_csv_schema=(
                    self._application_config.schemas[
                        "output_csv_schema"
                    ]
                ),
                country_name_corrections=(
                    self._application_config.countries.get(
                        "country_name_corrections",
                        {}
                    )
                )
            )
        )

        output_paths: dict[
            str,
            Path
        ] = {}

        # ==================================================
        # EXPORT EACH SELECTED SUBPRODUCT
        # ==================================================

        for (
            subproduct_id,
            generated_rows
        ) in rows_by_subproduct.items():

            subproduct_config = (
                subproducts_by_id.get(
                    subproduct_id
                )
            )

            if subproduct_config is None:
                raise ValueError(
                    f"Generated Phone ID Suite subproduct "
                    f"'{subproduct_id}' does not exist in "
                    f"product configuration."
                )

            product_output_name = (
                str(
                    subproduct_config.get(
                        "output_name",
                        ""
                    )
                )
                .strip()
            )

            if not product_output_name:
                raise ValueError(
                    f"Phone ID Suite subproduct "
                    f"'{subproduct_id}' has no output_name."
                )

            if not generated_rows:
                raise ValueError(
                    f"Phone ID Suite subproduct "
                    f"'{subproduct_id}' contains no "
                    f"generated pricing rows."
                )

            # ----------------------------------------------
            # CsvExportService already knows how to produce
            # the required SMS upload template.
            #
            # Each subproduct is wrapped in a normal
            # GenerationResult only for physical export.
            # ----------------------------------------------

            export_result = (
                GenerationResult(
                    currency=request.currency,
                    product_id=subproduct_id,
                    product_output_name=(
                        product_output_name
                    ),
                    pricing_type=None,
                    rows=generated_rows
                )
            )

            output_path = (
                csv_export_service.export(
                    export_result
                )
            )

            output_paths[
                subproduct_id
            ] = output_path

        if not output_paths:
            raise RuntimeError(
                "Phone ID Suite did not export any files."
            )

        return output_paths

    def _export_phone_id_live_status(
        self,
        request: GenerationRequest,
        generation_result: GenerationResult
    ) -> Path:
        """
        Exports Phone ID Live Status using the existing
        Voice Verify Per Transaction output schema.

        Live Status contains:

            Mobile Price
            Landline Price

        and therefore maps directly to
        GeneratedVoicePricingRow.
        """

        schema_rule = (
            self._application_config.schemas[
                "output_schema_rules"
            ][
                "PHONE_ID_LIVE_STATUS"
            ]
        )

        schema_id = (
            schema_rule.get(
                "fixed_schema"
            )
        )

        if not schema_id:
            raise ValueError(
                "No fixed Phone ID Live Status output "
                "schema is configured."
            )

        voice_rows = (
            generation_result.rows
        )

        if not voice_rows:
            raise ValueError(
                "Phone ID Live Status generation "
                "returned no pricing rows."
            )

        for row_index, generated_row in enumerate(
            voice_rows,
            start=1
        ):
            if not isinstance(
                generated_row,
                GeneratedVoicePricingRow
            ):
                raise ValueError(
                    f"Phone ID Live Status row "
                    f"{row_index} has an unexpected "
                    f"result type."
                )

        voice_row_builder = (
            VoiceCsvRowBuilder(
                voice_output_csv_schemas=(
                    self._application_config.schemas[
                        "voice_output_csv_schemas"
                    ]
                ),
                country_name_corrections=(
                    self._application_config.countries.get(
                        "country_name_corrections",
                        {}
                    )
                )
            )
        )

        voice_export_service = (
            VoiceCsvExportService(
                voice_csv_row_builder=(
                    voice_row_builder
                ),
                output_settings=(
                    self._application_config.settings[
                        "output"
                    ]
                )
            )
        )

        output_path = (
            self._build_output_path(
                currency=request.currency,
                product_output_name=(
                    generation_result
                    .product_output_name
                ),
                pricing_type=None
            )
        )

        return (
            voice_export_service.export(
                generated_rows=voice_rows,
                schema_id=schema_id,
                output_path=output_path
            )
        )

    @staticmethod
    def _get_product_option_display_name(
        product_config: dict[str, Any],
        option_id: str,
        selected_value: str
    ) -> str:
        """
        Returns the user-facing display name for one configured
        product-option value.

        Example:

            PER_TRANSACTION
            → Per Transaction
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
                    == selected_value
                ):
                    return str(
                        value_config[
                            "display_name"
                        ]
                    )

        raise ValueError(
            f"Could not resolve display name for "
            f"product option '{option_id}' value "
            f"'{selected_value}'."
        )

    def _get_mobile_voice_schema_id(
        self,
        traffic_type: str
    ) -> str:
        """
        Resolves the configured Voice output schema for Mobile
        (SMS and Voice).

        Configuration examples:

            ONE_WAY
            -> voice_output_csv_schemas.voice_one_way

            TWO_WAY
            -> voice_output_csv_schemas.voice_two_way
        """

        mobile_definitions = (
            self._application_config.schemas.get(
                "multi_output_definitions",
                {}
            ).get(
                "MOBILE_SMS_VOICE"
            )
        )

        if not isinstance(
            mobile_definitions,
            dict
        ):
            raise ValueError(
                "Mobile multi-output configuration is missing."
            )

        traffic_definition = (
            mobile_definitions.get(
                traffic_type
            )
        )

        if not isinstance(
            traffic_definition,
            list
        ):
            raise ValueError(
                f"No Mobile output definition is configured "
                f"for traffic type '{traffic_type}'."
            )

        for output_definition in (
            traffic_definition
        ):
            if (
                output_definition.get(
                    "output_id"
                )
                != "VOICE"
            ):
                continue

            schema_source = str(
                output_definition.get(
                    "schema_source",
                    ""
                )
            ).strip()

            expected_prefix = (
                "voice_output_csv_schemas."
            )

            if not schema_source.startswith(
                expected_prefix
            ):
                raise ValueError(
                    "Mobile Voice output has an invalid "
                    f"schema_source '{schema_source}'."
                )

            schema_id = (
                schema_source[
                    len(expected_prefix):
                ]
            ).strip()

            if not schema_id:
                raise ValueError(
                    "Mobile Voice output schema ID "
                    "cannot be empty."
                )

            if (
                schema_id
                not in
                self._application_config.schemas[
                    "voice_output_csv_schemas"
                ]
            ):
                raise ValueError(
                    f"Mobile Voice output schema "
                    f"'{schema_id}' does not exist."
                )

            return schema_id

        raise ValueError(
            f"No Mobile Voice output is configured "
            f"for traffic type '{traffic_type}'."
        )

    def _log_mobile_success(
        self,
        request: GenerationRequest,
        generation_result: MobileGenerationResult,
        output_paths: dict[str, Path]
    ) -> None:
        """
        Logs each physical Mobile output using the existing
        production logging format.

        One Generate action can therefore create:

            ONE_WAY:
                2 success log entries

            TWO_WAY:
                3 success log entries
        """

        row_counts = (
            generation_result
            .output_row_counts
        )

        traffic_display_name = (
            "1-Way"
            if generation_result.traffic_type
            == "ONE_WAY"
            else "2-Way"
        )

        product_names = {
            "SMS_OUTBOUND": (
                f"{generation_result.product_output_name} - "
                f"SMS Outbound"
            ),
            "SMS_INBOUND": (
                f"{generation_result.product_output_name} - "
                f"SMS Inbound"
            ),
            "VOICE": (
                f"{generation_result.product_output_name} - "
                f"Voice - {traffic_display_name}"
            )
        }

        for output_id, output_path in (
            output_paths.items()
        ):
            if output_id not in row_counts:
                raise ValueError(
                    f"Mobile output '{output_id}' does not "
                    f"have a row count."
                )

            product_name = (
                product_names.get(
                    output_id
                )
            )

            if product_name is None:
                raise ValueError(
                    f"Unsupported Mobile output "
                    f"'{output_id}'."
                )

            self._logging_service.log_success(
                currency=request.currency,
                product=product_name,
                pricing_type=request.pricing_type,
                sender_ids=request.sender_ids,
                local_countries=request.local_countries,
                rows_generated=(
                    row_counts[
                        output_id
                    ]
                ),
                output_file=output_path
            )

    def _resolve_workbook_path(
        self,
        currency: str,
        product_config: dict[str, Any]
    ) -> Path:
        """
        Resolves the source pricing workbook for one product
        and currency.

        Existing products use the default workbook configured
        in settings.json.

        Products with a configured source_workbook use that
        product-specific workbook instead.
        """

        workbook_settings = (
            self._application_config.settings[
                "pricing_workbook"
            ]
        )

        source_workbook = (
            product_config.get(
                "source_workbook"
            )
        )

        if source_workbook is None:
            workbook_filename = (
                workbook_settings[
                    "filename"
                ]
            )

        else:
            if (
                not isinstance(
                    source_workbook,
                    str
                )
                or not source_workbook.strip()
            ):
                product_id = (
                    product_config.get(
                        "product_id",
                        "UNKNOWN"
                    )
                )

                raise ValueError(
                    f"Product '{product_id}' has an invalid "
                    f"source_workbook configuration."
                )

            workbook_filename = (
                source_workbook.strip()
            )

        return (
            self._path_resolver
            .get_pricing_workbook_path(
                folder_pattern=(
                    workbook_settings[
                        "folder_pattern"
                    ]
                ),
                filename=workbook_filename,
                currency=currency
            )
        )

    def _build_product_mapping(
        self
    ) -> dict[str, dict[str, Any]]:
        """
        Creates a mapping of enabled products by product ID.

        Returns:
            Enabled product configuration by product ID.
        """

        products = (
            self._application_config.products[
                "products"
            ]
        )

        return {
            product["product_id"]: product
            for product in products
            if product["enabled"]
        }

    def _build_output_path(
        self,
        currency: str,
        product_output_name: str,
        pricing_type: str | None
    ) -> Path:
        """
        Builds an output path using the configured filename pattern.

        Products that use a Pricing Type produce filenames such as:

            USD - SMS - Baseline - template Aug 2026.csv

        Products that do not use a Pricing Type produce filenames such as:

            USD - Phone ID Live Status - template Aug 2026.csv

        The configured filename pattern remains the source of truth.
        """

        output_settings = (
            self._application_config.settings[
                "output"
            ]
        )

        output_directory_pattern = str(
            output_settings.get(
                "directory",
                ""
            )
        ).strip()

        if not output_directory_pattern:
            raise ValueError(
                "Output directory cannot be empty."
            )

        output_directory = (
            self._path_resolver.resolve_path(
                output_directory_pattern
            )
        )

        filename_pattern = str(
            output_settings.get(
                "filename_pattern",
                ""
            )
        ).strip()

        if not filename_pattern:
            raise ValueError(
                "Output filename pattern cannot be empty."
            )

        generation_date = date.today()

        # ==================================================
        # PRICING TYPE
        #
        # Existing products:
        #     Baseline / Enterprise
        #
        # Single-pricing products:
        #     None
        #
        # Never convert None into the literal text "None".
        # ==================================================

        normalized_pricing_type = (
            str(
                pricing_type
            ).strip()
            if pricing_type is not None
            else ""
        )

        rendered_filename = (
            filename_pattern
        )

        # ==================================================
        # REMOVE THE PRICING TYPE SEGMENT WHEN NOT USED
        #
        # Our configured pattern contains a section such as:
        #
        #     ... - {pricing_type} - ...
        #
        # For a single-pricing product we remove the preceding
        # separator together with the placeholder.
        #
        # Example:
        #
        #     USD - Phone ID Live Status
        #         - {pricing_type}
        #         - template Aug 2026.csv
        #
        # becomes:
        #
        #     USD - Phone ID Live Status
        #         - template Aug 2026.csv
        # ==================================================

        if not normalized_pricing_type:

            rendered_filename = (
                re.sub(
                    r"\s*-\s*\{pricing_type\}",
                    "",
                    rendered_filename
                )
            )

            # Defensive fallback in case a future filename
            # pattern uses the placeholder without a preceding
            # hyphen.
            rendered_filename = (
                rendered_filename.replace(
                    "{pricing_type}",
                    ""
                )
            )

        # ==================================================
        # PLACEHOLDER REPLACEMENTS
        # ==================================================

        replacements = {
            "{currency}": currency,
            "{product}": (
                product_output_name
            ),
            "{pricing_type}": (
                normalized_pricing_type
            ),
            "{MMM YYYY}": (
                generation_date.strftime(
                    "%b %Y"
                )
            )
        }

        for placeholder, replacement in (
            replacements.items()
        ):
            rendered_filename = (
                rendered_filename.replace(
                    placeholder,
                    replacement
                )
            )

        # ==================================================
        # CLEAN UP SPACING
        #
        # This protects us from accidental double spaces if a
        # future filename pattern places optional values next
        # to separators.
        # ==================================================

        rendered_filename = (
            re.sub(
                r"\s{2,}",
                " ",
                rendered_filename
            )
            .strip()
        )

        # ==================================================
        # CHECK FOR UNKNOWN CONFIGURATION PLACEHOLDERS
        # ==================================================

        unresolved_placeholders = (
            re.findall(
                r"\{[^{}]+\}",
                rendered_filename
            )
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
                f"placeholder(s): "
                f"{unresolved_list}."
            )

        # ==================================================
        # WINDOWS-SAFE FILENAME
        # ==================================================

        invalid_filename_characters = (
            re.compile(
                r'[<>:"/\\|?*]'
            )
        )

        safe_filename = (
            invalid_filename_characters.sub(
                "_",
                rendered_filename
            )
        ).strip()

        if not safe_filename:
            raise ValueError(
                "Rendered output filename cannot be empty."
            )

        if not safe_filename.casefold().endswith(
            ".csv"
        ):
            safe_filename = (
                f"{safe_filename}.csv"
            )

        return (
            output_directory
            / safe_filename
        ).resolve()

    def _log_phone_id_suite_success(
        self,
        request: GenerationRequest,
        product_config: dict[str, Any],
        generation_result: PhoneIdSuiteGenerationResult,
        output_paths: dict[str, Path]
    ) -> None:
        """
        Logs every physical Phone ID Suite output separately.

        Example:

            One request selecting:
                Standard
                Contact
                SIM Swap

            creates:
                3 CSV files
                3 SUCCESS log entries
        """

        row_counts = (
            generation_result
            .output_row_counts
        )

        configured_subproducts = (
            product_config.get(
                "subproducts",
                []
            )
        )

        subproducts_by_id = {
            str(
                subproduct[
                    "product_id"
                ]
            ).strip(): subproduct
            for subproduct
            in configured_subproducts
        }

        for (
            subproduct_id,
            output_path
        ) in output_paths.items():

            if (
                subproduct_id
                not in row_counts
            ):
                raise ValueError(
                    f"Phone ID Suite output "
                    f"'{subproduct_id}' does not have "
                    f"a generated row count."
                )

            subproduct_config = (
                subproducts_by_id.get(
                    subproduct_id
                )
            )

            if subproduct_config is None:
                raise ValueError(
                    f"Phone ID Suite output "
                    f"'{subproduct_id}' does not exist "
                    f"in product configuration."
                )

            product_name = (
                str(
                    subproduct_config.get(
                        "output_name",
                        ""
                    )
                )
                .strip()
            )

            if not product_name:
                raise ValueError(
                    f"Phone ID Suite output "
                    f"'{subproduct_id}' has no "
                    f"output_name."
                )

            self._logging_service.log_success(
                currency=request.currency,
                product=product_name,
                pricing_type=None,
                sender_ids=request.sender_ids,
                local_countries=(
                    request.local_countries
                ),
                rows_generated=(
                    row_counts[
                        subproduct_id
                    ]
                ),
                output_file=output_path
            )

    def _validate_request(
        self,
        request: GenerationRequest
    ) -> None:
        """
        Validates controller-level generation inputs.

        Args:
            request:
                Generation request supplied by the GUI.

        Raises:
            ValueError:
                If currency, product or Pricing Type is invalid.
        """

        if not request.currency.strip():
            raise ValueError(
                "Generation currency cannot be empty."
            )

        supported_currencies = (
            self._application_config.settings[
                "supported_currencies"
            ]
        )

        if (
            request.currency
            not in supported_currencies
        ):
            raise ValueError(
                f"Unsupported generation currency "
                f"'{request.currency}'."
            )

        if not request.product_id.strip():
            raise ValueError(
                "Generation product ID cannot be empty."
            )

        if (
            request.product_id
            not in self._products_by_id
        ):
            raise ValueError(
                f"Unsupported or disabled product "
                f"'{request.product_id}'."
            )

        # ==================================================
        # PRICING TYPE VALIDATION
        # ==================================================

        product_config = (
            self._products_by_id[
                request.product_id
            ]
        )

        supported_pricing_types = (
            product_config.get(
                "supported_pricing_types",
                []
            )
        )

        # --------------------------------------------------
        # Product requires a Pricing Type.
        #
        # Examples:
        # SMS
        # Voice
        # WhatsApp
        # Viber
        # --------------------------------------------------

        if supported_pricing_types:

            if (
                request.pricing_type is None
                or not str(
                    request.pricing_type
                ).strip()
            ):
                raise ValueError(
                    f"Product "
                    f"'{request.product_id}' "
                    f"requires a Pricing Type."
                )

            normalized_pricing_type = (
                str(
                    request.pricing_type
                )
                .strip()
            )

            if (
                normalized_pricing_type
                not in supported_pricing_types
            ):
                raise ValueError(
                    f"Unsupported Pricing Type "
                    f"'{normalized_pricing_type}' "
                    f"for product "
                    f"'{request.product_id}'."
                )

        # --------------------------------------------------
        # Product has one pricing model and therefore does
        # NOT use Pricing Type.
        #
        # Examples:
        # Phone ID Suite
        # Phone ID Live Status
        # --------------------------------------------------

        else:

            if (
                request.pricing_type is not None
                and str(
                    request.pricing_type
                ).strip()
            ):
                raise ValueError(
                    f"Product "
                    f"'{request.product_id}' "
                    f"does not use a Pricing Type."
                )