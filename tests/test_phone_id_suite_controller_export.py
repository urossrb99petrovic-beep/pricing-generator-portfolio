import csv
import sys
import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock


APPLICATION_ROOT = (
    Path(__file__).resolve().parent.parent
)

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(APPLICATION_ROOT)
    )


from app.controllers.pricing_generator_controller import (
    PricingGeneratorController
)

from app.models.generated_phone_id_suite_pricing import (
    GeneratedPhoneIdSuitePricing
)

from app.models.generated_pricing_row import (
    GeneratedPricingRow
)

from app.models.generation_request import (
    GenerationRequest
)

from app.models.phone_id_suite_generation_result import (
    PhoneIdSuiteGenerationResult
)


class TestPhoneIdSuiteControllerExport(
    unittest.TestCase
):

    def setUp(
        self
    ) -> None:

        self.temp_directory = (
            TemporaryDirectory()
        )

        self.output_directory = Path(
            self.temp_directory.name
        )

        self.path_resolver = Mock()

        self.path_resolver.resolve_path.return_value = (
            self.output_directory
        )

        self.logging_service = Mock()

        self.application_config = (
            SimpleNamespace(
                settings={
                    "output": {
                        "directory": "unused",
                        "filename_pattern": (
                            "{currency} - {product} - "
                            "{pricing_type} - template "
                            "{MMM YYYY}.csv"
                        ),
                        "overwrite_existing_file": True,
                        "encoding": "utf-8",
                        "delimiter": ",",
                        "quoting": "minimal"
                    }
                },
                schemas={
                    "output_csv_schema": {
                        "band_definition_row": {
                            "A": "Band1",
                            "B": "Band2",
                            "C": "Band3",
                            "D": "Band4",
                            "E": "Band5",
                            "F": "Band6"
                        },
                        "band_threshold_row": {
                            "A": "0"
                        },
                        "column_header_row": {
                            "A": "Country",
                            "B": "ISO2",
                            "C": "Band1",
                            "D": "Band2",
                            "E": "Band3",
                            "F": "Band4",
                            "G": "Band5",
                            "H": "Band6"
                        }
                    }
                },
                countries={
                    "country_name_corrections": {}
                },
                products={
                    "products": []
                }
            )
        )

        self.controller = (
            PricingGeneratorController(
                application_config=(
                    self.application_config
                ),
                path_resolver=(
                    self.path_resolver
                ),
                logging_service=(
                    self.logging_service
                )
            )
        )

        self.product_config = {
            "product_id": (
                "PHONE_ID_SUITE"
            ),
            "output_name": (
                "Phone ID Suite"
            ),
            "subproducts": [
                {
                    "product_id": (
                        "PHONE_ID_STANDARD"
                    ),
                    "output_name": (
                        "Phone ID Standard"
                    )
                },
                {
                    "product_id": (
                        "PHONE_ID_SIM_SWAP"
                    ),
                    "output_name": (
                        "Phone ID SIM Swap"
                    )
                }
            ]
        }

        self.request = (
            GenerationRequest(
                currency="USD",
                product_id=(
                    "PHONE_ID_SUITE"
                ),
                pricing_type=None,
                selected_subproducts=[
                    "PHONE_ID_STANDARD",
                    "PHONE_ID_SIM_SWAP"
                ]
            )
        )

        self.generated_pricing = (
            GeneratedPhoneIdSuitePricing(
                rows_by_subproduct={
                    "PHONE_ID_STANDARD": [
                        GeneratedPricingRow(
                            country="",
                            iso2="",
                            price=(
                                Decimal(
                                    "0.0075"
                                )
                            )
                        ),
                        GeneratedPricingRow(
                            country="Argentina",
                            iso2="AR",
                            price=(
                                Decimal(
                                    "0.0075"
                                )
                            )
                        ),
                        GeneratedPricingRow(
                            country="Canada",
                            iso2="CA",
                            price=(
                                Decimal(
                                    "0.01"
                                )
                            )
                        )
                    ],

                    "PHONE_ID_SIM_SWAP": [
                        GeneratedPricingRow(
                            country="",
                            iso2="",
                            price=(
                                Decimal(
                                    "1.0"
                                )
                            )
                        ),
                        GeneratedPricingRow(
                            country="Argentina",
                            iso2="AR",
                            price=(
                                Decimal(
                                    "0.076"
                                )
                            )
                        )
                    ]
                }
            )
        )

        self.generation_result = (
            PhoneIdSuiteGenerationResult(
                currency="USD",
                product_id=(
                    "PHONE_ID_SUITE"
                ),
                product_output_name=(
                    "Phone ID Suite"
                ),
                pricing_type=None,
                pricing=(
                    self.generated_pricing
                )
            )
        )

    def tearDown(
        self
    ) -> None:

        self.temp_directory.cleanup()

    def test_output_row_counts(
        self
    ) -> None:

        self.assertEqual(
            self.generation_result
            .output_row_counts,
            {
                "PHONE_ID_STANDARD": 3,
                "PHONE_ID_SIM_SWAP": 2
            }
        )

    def test_export_creates_one_file_per_subproduct(
        self
    ) -> None:

        output_paths = (
            self.controller
            ._export_phone_id_suite(
                request=self.request,
                product_config=(
                    self.product_config
                ),
                generation_result=(
                    self.generation_result
                )
            )
        )

        self.assertEqual(
            set(
                output_paths.keys()
            ),
            {
                "PHONE_ID_STANDARD",
                "PHONE_ID_SIM_SWAP"
            }
        )

        self.assertTrue(
            output_paths[
                "PHONE_ID_STANDARD"
            ].exists()
        )

        self.assertTrue(
            output_paths[
                "PHONE_ID_SIM_SWAP"
            ].exists()
        )

        self.assertIn(
            "Phone ID Standard",
            output_paths[
                "PHONE_ID_STANDARD"
            ].name
        )

        self.assertIn(
            "Phone ID SIM Swap",
            output_paths[
                "PHONE_ID_SIM_SWAP"
            ].name
        )

        self.assertNotIn(
            "None",
            output_paths[
                "PHONE_ID_STANDARD"
            ].name
        )

    def test_export_uses_sms_template(
        self
    ) -> None:

        output_paths = (
            self.controller
            ._export_phone_id_suite(
                request=self.request,
                product_config=(
                    self.product_config
                ),
                generation_result=(
                    self.generation_result
                )
            )
        )

        standard_path = (
            output_paths[
                "PHONE_ID_STANDARD"
            ]
        )

        with standard_path.open(
            mode="r",
            encoding="utf-8",
            newline=""
        ) as input_file:

            rows = list(
                csv.reader(
                    input_file
                )
            )

        self.assertEqual(
            rows[0],
            [
                "Band1",
                "Band2",
                "Band3",
                "Band4",
                "Band5",
                "Band6"
            ]
        )

        self.assertEqual(
            rows[2][0:3],
            [
                "Country",
                "ISO2",
                "Band1"
            ]
        )

        # All Others
        self.assertEqual(
            rows[3][0:3],
            [
                "",
                "",
                "0.0075"
            ]
        )

        # Argentina
        self.assertEqual(
            rows[4][0:3],
            [
                "Argentina",
                "AR",
                "0.0075"
            ]
        )

    def test_success_logging_writes_one_entry_per_file(
        self
    ) -> None:

        output_paths = {
            "PHONE_ID_STANDARD": (
                self.output_directory
                / "standard.csv"
            ),
            "PHONE_ID_SIM_SWAP": (
                self.output_directory
                / "sim_swap.csv"
            )
        }

        self.controller._log_phone_id_suite_success(
            request=self.request,
            product_config=(
                self.product_config
            ),
            generation_result=(
                self.generation_result
            ),
            output_paths=(
                output_paths
            )
        )

        self.assertEqual(
            self.logging_service
            .log_success
            .call_count,
            2
        )

        calls = (
            self.logging_service
            .log_success
            .call_args_list
        )

        first_call = (
            calls[0].kwargs
        )

        second_call = (
            calls[1].kwargs
        )

        self.assertEqual(
            first_call[
                "product"
            ],
            "Phone ID Standard"
        )

        self.assertEqual(
            first_call[
                "rows_generated"
            ],
            3
        )

        self.assertIsNone(
            first_call[
                "pricing_type"
            ]
        )

        self.assertEqual(
            second_call[
                "product"
            ],
            "Phone ID SIM Swap"
        )

        self.assertEqual(
            second_call[
                "rows_generated"
            ],
            2
        )

    def test_missing_subproduct_config_is_rejected(
        self
    ) -> None:

        invalid_result = (
            PhoneIdSuiteGenerationResult(
                currency="USD",
                product_id=(
                    "PHONE_ID_SUITE"
                ),
                product_output_name=(
                    "Phone ID Suite"
                ),
                pricing_type=None,
                pricing=(
                    GeneratedPhoneIdSuitePricing(
                        rows_by_subproduct={
                            "PHONE_ID_UNKNOWN": [
                                GeneratedPricingRow(
                                    country="",
                                    iso2="",
                                    price=(
                                        Decimal(
                                            "1.0"
                                        )
                                    )
                                )
                            ]
                        }
                    )
                )
            )
        )

        with self.assertRaises(
            ValueError
        ) as error_context:

            (
                self.controller
                ._export_phone_id_suite(
                    request=self.request,
                    product_config=(
                        self.product_config
                    ),
                    generation_result=(
                        invalid_result
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