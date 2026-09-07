from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class WhatsAppPricing:
    """
    Source pricing extracted from the WhatsApp workbook.

    WhatsApp uses the single 'Other' market price for every
    country, so only one source pricing object is required.
    """

    market: str
    iso2: str
    baseline_price: Decimal
    enterprise_price: Decimal