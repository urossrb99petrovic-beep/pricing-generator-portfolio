from pathlib import Path
from typing import Any

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
    ) -> tuple[GenerationResult, Path]:
        """
        Generates final pricing, exports it to CSV and records the
        generation attempt in the application log.

        Logging failures never prevent pricing generation from
        succeeding or the original generation error from reaching
        the caller.
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
                    request.currency
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
                        )
                    )
                )

            generation_result = GenerationResult(
                currency=request.currency,
                product_id=request.product_id,
                product_output_name=(
                    product_config["output_name"]
                ),
                pricing_type=request.pricing_type,
                rows=generated_rows
            )

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

            output_path = csv_export_service.export(
                generation_result
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
                    generation_result.product_output_name
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

    def _resolve_workbook_path(
        self,
        currency: str
    ) -> Path:
        """
        Resolves the pricing workbook for one currency.

        Args:
            currency:
                Selected pricing currency.

        Returns:
            Absolute pricing workbook path.
        """

        workbook_settings = (
            self._application_config.settings[
                "pricing_workbook"
            ]
        )

        return (
            self._path_resolver
            .get_pricing_workbook_path(
                folder_pattern=(
                    workbook_settings[
                        "folder_pattern"
                    ]
                ),
                filename=(
                    workbook_settings[
                        "filename"
                    ]
                ),
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

        if not request.pricing_type.strip():
            raise ValueError(
                "Generation pricing type cannot be empty."
            )