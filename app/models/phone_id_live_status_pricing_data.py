from dataclasses import dataclass

from app.models.phone_id_live_status_pricing_row import (
    PhoneIdLiveStatusPricingRow
)


@dataclass(frozen=True)
class PhoneIdLiveStatusPricingData:
    """
    Complete Phone ID Live Status source pricing.

    all_other:
        Fixed All Others row.

    countries:
        Destination-specific rows.
    """

    all_other: PhoneIdLiveStatusPricingRow

    countries: list[
        PhoneIdLiveStatusPricingRow
    ]