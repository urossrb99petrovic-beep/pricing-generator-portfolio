from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ViberCountryPricingRow:
    """
    Source data for one Viber country.

    Country pricing is calculated later from Cost and the
    selected DM percentage. Displayed worksheet prices are
    deliberately not retained here.
    """

    country: str
    iso2: str

    transactional_otp_cost: Decimal
    promotional_cost: Decimal
    session_chat_cost: Decimal
    international_cost: Decimal

    baseline_dm: Decimal
    enterprise_dm: Decimal
    