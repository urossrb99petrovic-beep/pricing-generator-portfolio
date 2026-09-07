from dataclasses import dataclass

from app.models.generated_pricing_row import (
    GeneratedPricingRow
)


@dataclass(frozen=True)
class GeneratedPhoneIdSuitePricing:
    """
    Generated Phone ID Suite pricing grouped by
    subproduct ID.

    Example:

        {
            "PHONE_ID_STANDARD": [
                GeneratedPricingRow(...),
                ...
            ],

            "PHONE_ID_CONTACT": [
                GeneratedPricingRow(...),
                ...
            ]
        }

    Only selected subproducts are included.
    """

    rows_by_subproduct: dict[
        str,
        list[GeneratedPricingRow]
    ]