from dataclasses import dataclass

from app.models.generated_pricing_row import (
    GeneratedPricingRow
)


@dataclass(frozen=True)
class GenerationResult:
    """
    Represents successfully generated pricing before CSV export.
    """

    currency: str
    product_id: str
    product_output_name: str
    pricing_type: str
    rows: list[GeneratedPricingRow]