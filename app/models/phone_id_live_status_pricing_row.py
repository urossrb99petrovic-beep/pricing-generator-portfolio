from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PhoneIdLiveStatusPricingRow:
    """
    Source pricing for one Phone ID Live Status destination.
    """

    country: str
    iso2: str
    mobile_price: Decimal
    landline_price: Decimal