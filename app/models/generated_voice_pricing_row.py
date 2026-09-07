from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class GeneratedVoicePricingRow:
    """
    Represents one final Voice destination-pricing row after
    pricing type and Voice business rules have been applied.
    """

    country: str
    iso2: str

    landline_price: Decimal
    mobile_price: Decimal

    inbound_price: Decimal | None = None