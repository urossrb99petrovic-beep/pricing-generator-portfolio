from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class GeneratedPricingRow:
    """
    Represents one final destination-pricing row after all
    generation rules and overrides have been applied.
    """

    country: str
    iso2: str
    price: Decimal