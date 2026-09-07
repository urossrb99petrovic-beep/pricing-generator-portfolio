from dataclasses import dataclass

from app.models.viber_all_other_pricing import (
    ViberAllOtherPricing
)
from app.models.viber_country_pricing_row import (
    ViberCountryPricingRow
)


@dataclass(frozen=True)
class ViberPricingData:
    """
    Complete Viber source pricing.

    All Others uses displayed pricing.
    Individual countries use Cost + DM source data.
    """

    all_other: ViberAllOtherPricing
    countries: list[ViberCountryPricingRow]