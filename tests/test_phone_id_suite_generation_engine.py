import sys
import unittest
from decimal import Decimal
from pathlib import Path


APPLICATION_ROOT = (
    Path(__file__).resolve().parent.parent
)

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(APPLICATION_ROOT)
    )


from app.models.generated_phone_id_suite_pricing import (
    GeneratedPhoneIdSuitePricing
)

from app.models.phone_id_suite_pricing_data import (
    PhoneIdSuitePricingData
)

from app.models.phone_id_suite_pricing_row import (
    PhoneIdSuitePricingRow
)

from app.services.generation_engine import (
    GenerationEngine
)


class TestPhoneIdSuiteGenerationEngine(
    unittest.TestCase
):

    def setUp(
        self
    ) -> None:

        self.engine = (
            GenerationEngine()
        )

        self.pricing_data = (
            PhoneIdSuitePricingData(
                all_other=(
                    PhoneIdSuitePricingRow(
                        country=(
                            "All other countries"
                        ),
                        iso2="",
                        phone_id_standard=(
                            Decimal("0.0075")
                        ),
                        phone_id_contact=(
                            Decimal("0.1")
                        ),
                        phone_id_contact_match=(
                            Decimal("1.0")
                        ),
                        phone_id_number_deactivation=(
                            Decimal("1.0")
                        ),
                        phone_id_porting_history=(
                            Decimal("1.0")
                        ),
                        phone_id_porting_status=(
                            Decimal("1.0")
                        ),
                        phone_id_sim_swap=(
                            Decimal("1.0")
                        ),
                        phone_id_subscriber_status=(
                            Decimal("1.0")
                        ),
                        phone_id_cfd=(
                            Decimal("1.0")
                        ),
                        phone_id_age_verify=(
                            Decimal("1.0")
                        ),
                        phone_id_breached_data=(
                            Decimal("0.0635")
                        ),
                        phone_id_active_call_status=(
                            Decimal("1.0")
                        )
                    )
                ),
                countries=[
                    PhoneIdSuitePricingRow(
                        country="Argentina",
                        iso2="AR",
                        phone_id_standard=(
                            Decimal("0.0075")
                        ),
                        phone_id_contact=(
                            Decimal("0.1")
                        ),
                        phone_id_contact_match=(
                            Decimal("0.15")
                        ),
                        phone_id_number_deactivation=(
                            None
                        ),
                        phone_id_porting_history=(
                            Decimal("0.011")
                        ),
                        phone_id_porting_status=(
                            Decimal("0.001")
                        ),
                        phone_id_sim_swap=(
                            Decimal("0.076")
                        ),
                        phone_id_subscriber_status=(
                            None
                        ),
                        phone_id_cfd=None,
                        phone_id_age_verify=None,
                        phone_id_breached_data=(
                            Decimal("0.0635")
                        ),
                        phone_id_active_call_status=(
                            None
                        )
                    ),

                    PhoneIdSuitePricingRow(
                        country="Canada",
                        iso2="CA",
                        phone_id_standard=(
                            Decimal("0.01")
                        ),
                        phone_id_contact=(
                            Decimal("0.11")
                        ),
                        phone_id_contact_match=(
                            Decimal("0.16")
                        ),
                        phone_id_number_deactivation=(
                            Decimal("0.079")
                        ),
                        phone_id_porting_history=(
                            Decimal("0.012")
                        ),
                        phone_id_porting_status=(
                            Decimal("0.002")
                        ),
                        phone_id_sim_swap=(
                            Decimal("0.08")
                        ),
                        phone_id_subscriber_status=(
                            Decimal("0.02")
                        ),
                        phone_id_cfd=(
                            Decimal("0.03")
                        ),
                        phone_id_age_verify=(
                            Decimal("0.04")
                        ),
                        phone_id_breached_data=(
                            Decimal("0.07")
                        ),
                        phone_id_active_call_status=(
                            Decimal("0.05")
                        )
                    )
                ]
            )
        )

        self.pricing_fields = {
            "PHONE_ID_STANDARD": (
                "phone_id_standard"
            ),
            "PHONE_ID_CONTACT": (
                "phone_id_contact"
            ),
            "PHONE_ID_NUMBER_DEACTIVATION": (
                "phone_id_number_deactivation"
            ),
            "PHONE_ID_SUBSCRIBER_STATUS": (
                "phone_id_subscriber_status"
            )
        }

    def test_selected_subproducts_are_generated(
        self
    ) -> None:

        result = (
            self.engine
            .generate_phone_id_suite_pricing(
                pricing_data=(
                    self.pricing_data
                ),
                selected_subproducts=[
                    "PHONE_ID_STANDARD",
                    "PHONE_ID_CONTACT"
                ],
                pricing_fields=(
                    self.pricing_fields
                )
            )
        )

        self.assertIsInstance(
            result,
            GeneratedPhoneIdSuitePricing
        )

        self.assertEqual(
            set(
                result
                .rows_by_subproduct
                .keys()
            ),
            {
                "PHONE_ID_STANDARD",
                "PHONE_ID_CONTACT"
            }
        )

    def test_all_other_is_first_row(
        self
    ) -> None:

        result = (
            self.engine
            .generate_phone_id_suite_pricing(
                pricing_data=(
                    self.pricing_data
                ),
                selected_subproducts=[
                    "PHONE_ID_STANDARD"
                ],
                pricing_fields=(
                    self.pricing_fields
                )
            )
        )

        first_row = (
            result
            .rows_by_subproduct[
                "PHONE_ID_STANDARD"
            ][0]
        )

        self.assertEqual(
            first_row.country,
            ""
        )

        self.assertEqual(
            first_row.iso2,
            ""
        )

        self.assertEqual(
            first_row.price,
            Decimal("0.0075")
        )

    def test_unavailable_country_is_filtered_only_from_that_subproduct(
        self
    ) -> None:

        result = (
            self.engine
            .generate_phone_id_suite_pricing(
                pricing_data=(
                    self.pricing_data
                ),
                selected_subproducts=[
                    "PHONE_ID_STANDARD",
                    (
                        "PHONE_ID_"
                        "NUMBER_DEACTIVATION"
                    )
                ],
                pricing_fields=(
                    self.pricing_fields
                )
            )
        )

        standard_countries = {
            row.country
            for row
            in result.rows_by_subproduct[
                "PHONE_ID_STANDARD"
            ]
        }

        deactivation_countries = {
            row.country
            for row
            in result.rows_by_subproduct[
                "PHONE_ID_NUMBER_DEACTIVATION"
            ]
        }

        self.assertIn(
            "Argentina",
            standard_countries
        )

        self.assertNotIn(
            "Argentina",
            deactivation_countries
        )

        self.assertIn(
            "Canada",
            deactivation_countries
        )

    def test_available_country_price_is_preserved(
        self
    ) -> None:

        result = (
            self.engine
            .generate_phone_id_suite_pricing(
                pricing_data=(
                    self.pricing_data
                ),
                selected_subproducts=[
                    (
                        "PHONE_ID_"
                        "NUMBER_DEACTIVATION"
                    )
                ],
                pricing_fields=(
                    self.pricing_fields
                )
            )
        )

        canada_row = next(
            row
            for row
            in result.rows_by_subproduct[
                "PHONE_ID_NUMBER_DEACTIVATION"
            ]
            if row.iso2 == "CA"
        )

        self.assertEqual(
            canada_row.price,
            Decimal("0.079")
        )

    def test_unselected_subproduct_is_not_generated(
        self
    ) -> None:

        result = (
            self.engine
            .generate_phone_id_suite_pricing(
                pricing_data=(
                    self.pricing_data
                ),
                selected_subproducts=[
                    "PHONE_ID_STANDARD"
                ],
                pricing_fields=(
                    self.pricing_fields
                )
            )
        )

        self.assertNotIn(
            "PHONE_ID_CONTACT",
            result.rows_by_subproduct
        )

    def test_empty_selection_is_rejected(
        self
    ) -> None:

        with self.assertRaises(
            ValueError
        ):
            (
                self.engine
                .generate_phone_id_suite_pricing(
                    pricing_data=(
                        self.pricing_data
                    ),
                    selected_subproducts=[],
                    pricing_fields=(
                        self.pricing_fields
                    )
                )
            )

    def test_missing_pricing_field_mapping_is_rejected(
        self
    ) -> None:

        with self.assertRaises(
            ValueError
        ) as error_context:

            (
                self.engine
                .generate_phone_id_suite_pricing(
                    pricing_data=(
                        self.pricing_data
                    ),
                    selected_subproducts=[
                        "PHONE_ID_STANDARD",
                        "PHONE_ID_UNKNOWN"
                    ],
                    pricing_fields=(
                        self.pricing_fields
                    )
                )
            )

        self.assertIn(
            "PHONE_ID_UNKNOWN",
            str(
                error_context.exception
            )
        )


if __name__ == "__main__":
    unittest.main()