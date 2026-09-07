from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ViberAllOtherPricing:
    """
    Displayed Viber pricing from the dedicated All Others row.

    These displayed source prices are authoritative for
    All Others and must NOT be recalculated from Cost / DM.
    """

    transactional_otp_price: Decimal
    promotional_price: Decimal
    session_chat_price: Decimal
    international_price: Decimal