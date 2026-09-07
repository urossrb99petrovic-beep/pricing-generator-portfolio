from dataclasses import dataclass

from app.models.generated_pricing_row import (
    GeneratedPricingRow
)
from app.models.generated_voice_pricing_row import (
    GeneratedVoicePricingRow
)
from app.models.generated_viber_pricing_row import (
    GeneratedViberPricingRow
)


@dataclass(frozen=True)
class GenerationResult:
    """
    Represents successfully generated pricing before CSV export.
    """

    currency: str
    product_id: str
    product_output_name: str
    pricing_type: str | None

    rows: (
        list[GeneratedPricingRow]
        | list[GeneratedVoicePricingRow]
        | list[GeneratedViberPricingRow]
    )