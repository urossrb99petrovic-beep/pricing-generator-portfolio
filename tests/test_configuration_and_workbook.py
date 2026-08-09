from pathlib import Path
import unittest

from app.services.configuration_service import ConfigurationService
from app.services.pricing_data_service import PricingDataService
from app.services.workbook_service import WorkbookService


ROOT = Path(__file__).resolve().parents[1]
CONFIGURATION = ROOT / "Administration" / "Configuration" / "1.0.0"


class SyntheticDemoTests(unittest.TestCase):
    def test_configuration_loads(self) -> None:
        config = ConfigurationService().load_configuration(CONFIGURATION)
        self.assertEqual(config.settings["default_currency"], "USD")
        self.assertEqual(len(config.products["products"]), 2)

    def test_synthetic_workbook_is_readable(self) -> None:
        config = ConfigurationService().load_configuration(CONFIGURATION)
        workbook_path = ROOT / "demo_data" / "USD" / "Synthetic Pricing.xlsx"
        with WorkbookService(workbook_path) as workbook:
            service = PricingDataService(
                workbook_service=workbook,
                workbook_schemas=config.schemas["workbook_schemas"],
            )
            rows = service.get_sms_pricing()

        self.assertGreaterEqual(len(rows), 4)
        self.assertEqual(rows[1].iso2, "US")


if __name__ == "__main__":
    unittest.main()
