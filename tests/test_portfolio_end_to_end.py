"""Contract checks using only the bundled fictional workbooks."""
import csv
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

from main import start_application
from demo import scenarios
from app.controllers.pricing_generator_controller import PricingGeneratorController
from app.models.generation_request import GenerationRequest

ROOT = Path(__file__).resolve().parents[1]


class PortfolioEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config, self.resolver, self.logger = start_application(ROOT)
        self.config.settings['output']['directory'] = self.temp.name
        self.controller = PricingGeneratorController(self.config, self.resolver, Mock())

    def generate(self, product, **kw):
        return self.controller.generate_pricing(GenerationRequest('USD', product, **kw))

    def test_all_configured_combinations_generate_valid_csvs(self):
        products = set()
        for request in scenarios(self.config):
            with self.subTest(request=request):
                _, paths = self.controller.generate_pricing(request)
                products.add(request.product_id)
                for path in paths.values() if isinstance(paths, dict) else [paths]:
                    with path.open(encoding='utf-8-sig', newline='') as f:
                        rows = list(csv.reader(f))
                    self.assertGreaterEqual(len(rows), 4)
                    if request.product_id == 'WHATSAPP':
                        self.assertEqual(len(rows), 4)
                        self.assertEqual(rows[3][:2], ['', ''])
                    self.assertTrue(any('Country' in row for row in rows[:3]))
                    self.assertNotIn('None', path.name)
        self.assertEqual(len(products), 14)

    def test_sms_base_sender_and_local_precedence(self):
        base, _ = self.generate('SMS', pricing_type='Baseline')
        self.assertEqual(next(r.price for r in base.rows if r.iso2 == 'US'), Decimal('0.048'))
        sender, _ = self.generate('SMS', pricing_type='Baseline', sender_ids={'US': '10DLC'})
        self.assertEqual(next(r.price for r in sender.rows if r.iso2 == 'US'), Decimal('0.095'))
        local, _ = self.generate('LOCAL_SMS', pricing_type='Baseline', sender_ids={'US': '10DLC'}, local_countries=['United States'])
        self.assertEqual(next(r.price for r in local.rows if r.iso2 == 'US'), Decimal('0.069'))
        self.assertEqual(next(r.price for r in local.rows if r.iso2 == 'CA'), next(r.price for r in base.rows if r.iso2 == 'CA'))

    def test_phone_id_selection_and_unavailable_filtering(self):
        _, paths = self.generate('PHONE_ID_SUITE', selected_subproducts=['PHONE_ID_STANDARD','PHONE_ID_SIM_SWAP'])
        self.assertEqual(len(paths), 2)
        sim = next(path for key,path in paths.items() if 'SIM_SWAP' in key)
        rows = list(csv.reader(sim.open(encoding='utf-8')))
        # UK has an unavailable value for this field; it must not receive a fabricated price.
        self.assertFalse(any('GB' in row[:2] for row in rows[3:]))

    def test_mobile_outputs_depend_on_traffic_direction(self):
        _, one = self.generate('MOBILE_SMS_VOICE', pricing_type='Baseline', product_options={'traffic_type':'ONE_WAY'})
        _, two = self.generate('MOBILE_SMS_VOICE', pricing_type='Baseline', product_options={'traffic_type':'TWO_WAY'})
        self.assertEqual(len(one), 2)
        self.assertEqual(len(two), 3)
        inbound = next(path for key,path in two.items() if 'SMS_INBOUND' in key)
        rows=list(csv.reader(inbound.open(encoding='utf-8')))
        self.assertFalse(any('RS' in row[:2] for row in rows[3:]))

    def test_rejected_request_creates_no_output(self):
        with self.assertRaises(ValueError):
            self.generate('VOICE', pricing_type='Baseline', product_options={'traffic_type':'INVALID'})
        self.assertEqual(list(Path(self.temp.name).glob('*.csv')), [])

    def test_source_workbooks_are_complete(self):
        fixtures=json.loads((ROOT/'demo_data/fixture_manifest.json').read_text())
        self.assertEqual(len(list((ROOT/'demo_data').glob('*/*.xlsx'))),12)
        self.assertEqual(len(fixtures['countries']),6)


if __name__ == '__main__':
    unittest.main()
