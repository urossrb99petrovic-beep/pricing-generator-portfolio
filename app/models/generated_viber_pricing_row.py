from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class GeneratedViberPricingRow:
    """
    Final calculated Viber pricing for one output row.

    transactional_otp_price is later written to both:
        viber-otp
        viber-tran
    """

    country: str
    iso2: str

    transactional_otp_price: Decimal
    promotional_price: Decimal
    international_price: Decimal
    session_chat_price: Decimal