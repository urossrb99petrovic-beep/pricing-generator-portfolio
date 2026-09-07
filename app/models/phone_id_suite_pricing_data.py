from dataclasses import dataclass

from app.models.phone_id_suite_pricing_row import (
    PhoneIdSuitePricingRow
)


@dataclass(frozen=True)
class PhoneIdSuitePricingData:
    """
    Complete Phone ID Suite source pricing.

    all_other:
        Dynamic "All other countries" source row.

    countries:
        Actual country pricing rows appearing before
        All Other Countries.
    """

    all_other: PhoneIdSuitePricingRow

    countries: list[
        PhoneIdSuitePricingRow
    ]