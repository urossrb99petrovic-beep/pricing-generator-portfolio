import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


APPLICATION_ROOT = (
    Path(__file__).resolve().parent.parent
)

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(APPLICATION_ROOT)
    )


from app.ui.main_window import MainWindow


class TestMainWindowGenerationReset(
    unittest.TestCase
):

    def test_successful_generation_resets_all_user_selections(
        self
    ) -> None:
        """
        v1.3.1 regression test.

        After successful generation the application must
        remain open, clear all user selections and return
        to the Home page.
        """

        window = MainWindow.__new__(
            MainWindow
        )

        window._selected_currency = "USD"
        window._selected_product_name = (
            "Phone ID Suite"
        )
        window._selected_product = {
            "product_id": "PHONE_ID_SUITE"
        }

        window._selected_pricing_type = (
            "Baseline"
        )

        window._selected_sender_ids = {
            "US": "TOLL_FREE"
        }

        window._selected_local_countries = [
            "United States"
        ]

        window._selected_product_options = {
            "example": "value"
        }

        window._selected_subproducts = [
            "PHONE_ID_STANDARD",
            "PHONE_ID_SIM_SWAP"
        ]

        window._options_frame = Mock()

        # Cached workbook data must remain available.
        window._local_country_cache = {
            "USD": [
                "United States",
                "Canada"
            ]
        }

        window.show_home = Mock()

        window._reset_after_successful_generation()

        self.assertIsNone(
            window._selected_currency
        )

        self.assertIsNone(
            window._selected_product_name
        )

        self.assertIsNone(
            window._selected_product
        )

        self.assertIsNone(
            window._selected_pricing_type
        )

        self.assertEqual(
            window._selected_sender_ids,
            {}
        )

        self.assertEqual(
            window._selected_local_countries,
            []
        )

        self.assertEqual(
            window._selected_product_options,
            {}
        )

        self.assertEqual(
            window._selected_subproducts,
            []
        )

        self.assertIsNone(
            window._options_frame
        )

        # Cache is deliberately retained.
        self.assertEqual(
            window._local_country_cache,
            {
                "USD": [
                    "United States",
                    "Canada"
                ]
            }
        )

        window.show_home.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()