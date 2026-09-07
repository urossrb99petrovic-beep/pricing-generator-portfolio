import csv
from datetime import date
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

from app.models.generated_voice_pricing_row import (
    GeneratedVoicePricingRow
)

from app.models.generation_request import (
    GenerationRequest
)

from app.models.generation_result import (
    GenerationResult
)


class TestPhoneIdLiveStatusControllerExport(
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
                    "output_schema_rules": {
                        "PHONE_ID_LIVE_STATUS": {
                            "fixed_schema": (
                                "voice_verify_transaction"
                            )
                        }
                    },
                    "voice_output_csv_schemas": {
                        "voice_verify_transaction": {
                            "band_definition_row": {
                                "A": "Band1",
                                "B": "Band2",
                                "C": "Band3",
                                "D": "Band4",
                                "E": "Band5",
                                "F": "Band6",
                                "G": "Band1",
                                "H": "Band2",
                                "I": "Band3",
                                "J": "Band4",
                                "K": "Band5",
                                "L": "Band6"
                            },
                            "band_threshold_row": {
                                "A": "0",
                                "G": "0"
                            },
                            "column_header_row": {
                                "A": "Country",
                                "B": "ISO2",
                                "C": "Mobile Band1",
                                "D": "Mobile Band2",
                                "E": "Mobile Band3",
                                "F": "Mobile Band4",
                                "G": "Mobile Band5",
                                "H": "Mobile Band6"
                            }
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

        self.request = GenerationRequest(
            currency="USD",
            product_id=(
                "PHONE_ID_LIVE_STATUS"
            ),
            pricing_type=None
        )

        self.generation_result = (
            GenerationResult(
                currency="USD",
                product_id=(
                    "PHONE_ID_LIVE_STATUS"
                ),
                product_output_name=(
                    "Phone ID Live Status"
                ),
                pricing_type=None,
                rows=[
                    GeneratedVoicePricingRow(
                        country="",
                        iso2="",
                        mobile_price=(
                            Decimal("0.1")
                        ),
                        landline_price=(
                            Decimal("0.1")
                        ),
                        inbound_price=None
                    ),
                    GeneratedVoicePricingRow(
                        country=(
                            "United States"
                        ),
                        iso2="US",
                        mobile_price=(
                            Decimal("0.0022")
                        ),
                        landline_price=(
                            Decimal("0.038")
                        ),
                        inbound_price=None
                    )
                ]
            )
        )

    def tearDown(
        self
    ) -> None:

        self.temp_directory.cleanup()

    def test_output_filename_has_no_pricing_type(
        self
    ) -> None:

        output_path = (
            self.controller
            ._build_output_path(
                currency="USD",
                product_output_name=(
                    "Phone ID Live Status"
                ),
                pricing_type=None
            )
        )

        self.assertEqual(
            output_path.name,
            (
                "USD - Phone ID Live Status - "
                f"template {date.today():%b %Y}.csv"
            )
        )

        self.assertNotIn(
            "None",
            output_path.name
        )

    def test_live_status_requires_voice_rows(
        self
    ) -> None:

        self.assertTrue(
            all(
                isinstance(
                    row,
                    GeneratedVoicePricingRow
                )
                for row in (
                    self.generation_result.rows
                )
            )
        )


if __name__ == "__main__":
    unittest.main()