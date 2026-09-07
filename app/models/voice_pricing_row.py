from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class VoicePricingRow:
    country: str
    iso2: str

    baseline_mobile_price: Decimal
    baseline_landline_price: Decimal

    enterprise_mobile_price: Decimal
    enterprise_landline_price: Decimal

    baseline_inbound_price: Decimal | None = None
    enterprise_inbound_price: Decimal | None = None

    number_type: str | None = None