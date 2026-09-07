from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PhoneIdSuitePricingRow:
    """
    Source pricing for one Phone ID Suite country.

    A price of None means that the particular Phone ID
    subproduct is unavailable for this country.

    In the source workbook unavailable pricing is written:

        n/a
    """

    country: str
    iso2: str

    phone_id_standard: Decimal | None
    phone_id_contact: Decimal | None
    phone_id_contact_match: Decimal | None
    phone_id_number_deactivation: Decimal | None
    phone_id_porting_history: Decimal | None
    phone_id_porting_status: Decimal | None
    phone_id_sim_swap: Decimal | None
    phone_id_subscriber_status: Decimal | None
    phone_id_cfd: Decimal | None
    phone_id_age_verify: Decimal | None
    phone_id_breached_data: Decimal | None
    phone_id_active_call_status: Decimal | None