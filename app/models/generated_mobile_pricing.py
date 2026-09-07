from dataclasses import dataclass

from app.models.generated_pricing_row import (
    GeneratedPricingRow
)
from app.models.generated_voice_pricing_row import (
    GeneratedVoicePricingRow
)


@dataclass(frozen=True)
class GeneratedMobilePricing:
    """
    Represents all generated outputs for one Mobile
    (SMS and Voice) request.

    ONE_WAY:
        sms_outbound_rows
        voice_rows
        sms_inbound_rows = None

    TWO_WAY:
        sms_outbound_rows
        sms_inbound_rows
        voice_rows
    """

    sms_outbound_rows: list[
        GeneratedPricingRow
    ]

    voice_rows: list[
        GeneratedVoicePricingRow
    ]

    sms_inbound_rows: (
        list[GeneratedPricingRow]
        | None
    ) = None