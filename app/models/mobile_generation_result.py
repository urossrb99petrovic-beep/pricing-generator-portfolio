from dataclasses import dataclass

from app.models.generated_mobile_pricing import (
    GeneratedMobilePricing
)


@dataclass(frozen=True)
class MobileGenerationResult:
    """
    Represents one complete Mobile (SMS and Voice)
    generation before/after multi-file export.
    """

    currency: str
    product_id: str
    product_output_name: str
    pricing_type: str
    traffic_type: str
    pricing: GeneratedMobilePricing

    @property
    def output_row_counts(
        self
    ) -> dict[str, int]:
        """
        Returns the number of generated pricing rows in each
        logical Mobile output.
        """

        row_counts = {
            "SMS_OUTBOUND": len(
                self.pricing.sms_outbound_rows
            ),
            "VOICE": len(
                self.pricing.voice_rows
            )
        }

        if (
            self.pricing.sms_inbound_rows
            is not None
        ):
            row_counts[
                "SMS_INBOUND"
            ] = len(
                self.pricing.sms_inbound_rows
            )

        return row_counts

    @property
    def total_rows_generated(
        self
    ) -> int:
        """
        Total pricing rows across all generated files.
        """

        return sum(
            self.output_row_counts.values()
        )