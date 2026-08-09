from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PricingRow:
    """
    Represents one country-pricing row extracted from a pricing
    worksheet.
    """

    country: str
    iso2: str
    baseline_price: Decimal
    enterprise_price: Decimal