from collections.abc import Callable
from pathlib import Path

from app.models.generated_mobile_pricing import (
    GeneratedMobilePricing
)
from app.models.generation_result import (
    GenerationResult
)
from app.services.csv_export_service import (
    CsvExportService
)
from app.services.voice_csv_export_service import (
    VoiceCsvExportService
)


class MobileCsvExportService:
    """
    Exports all CSV files required for one Mobile
    (SMS and Voice) generation.

    ONE_WAY:
        SMS_OUTBOUND
        VOICE

    TWO_WAY:
        SMS_OUTBOUND
        SMS_INBOUND
        VOICE

    Existing SMS and Voice exporters are reused.
    """

    def __init__(
        self,
        sms_csv_export_service: CsvExportService,
        voice_csv_export_service: VoiceCsvExportService,
        output_path_builder: Callable[
            [str, str, str],
            Path
        ]
    ) -> None:
        """
        Args:
            sms_csv_export_service:
                Existing production SMS CSV exporter.

            voice_csv_export_service:
                Existing production Voice CSV exporter.

            output_path_builder:
                Function that builds an exact output Path from:

                    currency
                    product_output_name
                    pricing_type
        """

        self._sms_csv_export_service = (
            sms_csv_export_service
        )

        self._voice_csv_export_service = (
            voice_csv_export_service
        )

        self._output_path_builder = (
            output_path_builder
        )

    def export(
        self,
        generated_pricing: GeneratedMobilePricing,
        currency: str,
        product_id: str,
        product_output_name: str,
        pricing_type: str,
        traffic_type: str,
        voice_schema_id: str
    ) -> dict[str, Path]:
        """
        Exports all Mobile files required by the selected
        Traffic Type.

        Returns:
            Mapping of logical output IDs to physical files.

            ONE_WAY example:
                {
                    "SMS_OUTBOUND": Path(...),
                    "VOICE": Path(...)
                }

            TWO_WAY example:
                {
                    "SMS_OUTBOUND": Path(...),
                    "SMS_INBOUND": Path(...),
                    "VOICE": Path(...)
                }
        """

        if traffic_type not in {
            "ONE_WAY",
            "TWO_WAY"
        }:
            raise ValueError(
                f"Unsupported Mobile traffic type "
                f"'{traffic_type}'."
            )

        if not voice_schema_id.strip():
            raise ValueError(
                "Mobile Voice schema ID cannot be empty."
            )

        output_paths: dict[
            str,
            Path
        ] = {}

        # -------------------------------------------------
        # SMS Outbound
        # -------------------------------------------------

        sms_outbound_result = (
            GenerationResult(
                currency=currency,
                product_id=product_id,
                product_output_name=(
                    f"{product_output_name} - "
                    f"SMS Outbound"
                ),
                pricing_type=pricing_type,
                rows=(
                    generated_pricing
                    .sms_outbound_rows
                )
            )
        )

        output_paths[
            "SMS_OUTBOUND"
        ] = (
            self._sms_csv_export_service
            .export(
                sms_outbound_result
            )
        )

        # -------------------------------------------------
        # SMS Inbound — 2-Way only
        # -------------------------------------------------

        if traffic_type == "TWO_WAY":
            sms_inbound_rows = (
                generated_pricing
                .sms_inbound_rows
            )

            if sms_inbound_rows is None:
                raise ValueError(
                    "Mobile 2-Way generation does not "
                    "contain SMS Inbound rows."
                )

            sms_inbound_result = (
                GenerationResult(
                    currency=currency,
                    product_id=product_id,
                    product_output_name=(
                        f"{product_output_name} - "
                        f"SMS Inbound"
                    ),
                    pricing_type=pricing_type,
                    rows=sms_inbound_rows
                )
            )

            output_paths[
                "SMS_INBOUND"
            ] = (
                self._sms_csv_export_service
                .export(
                    sms_inbound_result
                )
            )

        else:
            if (
                generated_pricing
                .sms_inbound_rows
                is not None
            ):
                raise ValueError(
                    "Mobile 1-Way generation unexpectedly "
                    "contains SMS Inbound rows."
                )

        # -------------------------------------------------
        # Voice
        # -------------------------------------------------

        if traffic_type == "ONE_WAY":
            traffic_display_name = (
                "1-Way"
            )

        else:
            traffic_display_name = (
                "2-Way"
            )

        voice_output_name = (
            f"{product_output_name} - "
            f"Voice - "
            f"{traffic_display_name}"
        )

        voice_output_path = (
            self._output_path_builder(
                currency,
                voice_output_name,
                pricing_type
            )
        )

        output_paths[
            "VOICE"
        ] = (
            self._voice_csv_export_service
            .export(
                generated_rows=(
                    generated_pricing
                    .voice_rows
                ),
                schema_id=voice_schema_id,
                output_path=(
                    voice_output_path
                )
            )
        )

        return output_paths