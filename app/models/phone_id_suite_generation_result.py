from dataclasses import dataclass

from app.models.generated_phone_id_suite_pricing import (
    GeneratedPhoneIdSuitePricing
)


@dataclass(frozen=True)
class PhoneIdSuiteGenerationResult:
    """
    Complete result of one Phone ID Suite generation request.

    One user action can create between 1 and 12 physical
    CSV files.

    pricing:
        Generated pricing grouped by selected subproduct ID.
    """

    currency: str
    product_id: str
    product_output_name: str
    pricing_type: str | None
    pricing: GeneratedPhoneIdSuitePricing

    @property
    def output_row_counts(
        self
    ) -> dict[str, int]:
        """
        Returns the generated row count for every physical
        Phone ID output.

        The count includes the All Others pricing row,
        matching the row-count convention already used by
        generation results elsewhere in the application.
        """

        return {
            subproduct_id: len(
                rows
            )
            for (
                subproduct_id,
                rows
            ) in (
                self.pricing
                .rows_by_subproduct
                .items()
            )
        }