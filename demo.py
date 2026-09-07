"""Run the complete synthetic product catalog without opening the desktop UI."""
import argparse
import itertools
import json
from dataclasses import asdict
from pathlib import Path

from main import start_application
from app.controllers.pricing_generator_controller import PricingGeneratorController
from app.models.generation_request import GenerationRequest


def scenarios(config):
    """Cover every configured choice, sender combination and local subset."""
    for currency in config.settings['supported_currencies']:
        for product in config.products['products']:
            if not product['enabled']:
                continue
            options = product.get('choice_options', [])
            choices = [dict(zip([o['option_id'] for o in options], values))
                       for values in itertools.product(*[[v['value_id'] for v in o['values']] for o in options])]
            senders = [{}]
            if product['sender_options']['enabled']:
                senders = [dict(zip(['US', 'CA'], pair)) for pair in itertools.product(['DSC', 'TOLL_FREE', '10DLC'], ['DSC', 'TOLL_FREE'])]
            locals_ = [[], ['United States', 'Brazil', 'Serbia']] if product['local_options']['enabled'] else [[]]
            subs = [s['product_id'] for s in product.get('subproducts', [])]
            for pricing, choice, sender, local in itertools.product(product['supported_pricing_types'] or [None], choices, senders, locals_):
                yield GenerationRequest(currency, product['product_id'], pricing, sender, local, choice, subs)


def run(output: Path):
    config, resolver, logger = start_application()
    report = []
    for index, request in enumerate(scenarios(config), 1):
        # One directory per scenario preserves different options with the same template name.
        folder = output.resolve() / f'{index:03d}_{request.currency}_{request.product_id}'
        config.settings['output']['directory'] = str(folder)
        result, paths = PricingGeneratorController(config, resolver, logger).generate_pricing(request)
        paths = paths if isinstance(paths, dict) else {'output': paths}
        report.append({'scenario': index, 'request': asdict(request),
                       'files': {k: str(p.relative_to(output.resolve())) for k, p in paths.items()}})
    (output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'{len(report)} scenarios passed; {sum(len(r["files"]) for r in report)} CSV files created in {output.resolve()}')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'demo_output' / 'showcase')
    run(parser.parse_args().output)
