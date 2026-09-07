from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MobilePricingRow:
    country: str
    iso2: str

    baseline_sms_outbound_price: Decimal | None
    baseline_sms_inbound_price: Decimal | None
    baseline_voice_outbound_price: Decimal | None
    baseline_voice_inbound_price: Decimal | None

    enterprise_sms_outbound_price: Decimal | None
    enterprise_sms_inbound_price: Decimal | None
    enterprise_voice_outbound_price: Decimal | None
    enterprise_voice_inbound_price: Decimal | None