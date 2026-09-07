# Pricing Generator

**A Python desktop application that turns controlled Excel pricing into validated CSV templates.**

Portfolio edition based on the original **v1.3.1** application. Includes **14 products, 3 currencies, 6 demonstration countries**, and a reproducible workbook-to-export test suite. All bundled prices are fictional.

## Why I built it

Business teams needed upload-ready pricing files but did not necessarily know how the source workbooks, product rules, or destination templates worked. Manual preparation took at least five minutes per file and created opportunities for copying the wrong price or choosing an incorrect template.

I built a guided desktop workflow that selects the correct workbook, applies the product-specific rules, validates the data, and creates the required file or group of files. The original business workflow benefited from less manual preparation and less reliance on specialist template knowledge. The five-minute figure is a user-reported manual preparation baseline; this repository does not claim a measured error-reduction percentage or a benchmarked time saving.

## Try it

On Windows with Python 3.11 or 3.12 installed:

1. Download and extract the repository.
2. Double-click **Setup_Windows.bat** once to install dependencies and run the tests.
3. Double-click **Run_Windows.bat** to open the desktop app.
4. Select a currency and product, configure its options, and generate.

Outputs are saved under `demo_output`; audit logs under `demo_logs`. After success, the app clears the selections and returns home so you can generate another product.

For a full demonstration without opening the desktop UI, double-click **Demo_All_Products.bat**. It exercises 306 scenarios and creates 357 CSVs in separate scenario folders, with a JSON manifest explaining each request.

Command-line setup:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe main.py
```

On macOS/Linux use `.venv/bin/python` in place of `.venv\Scripts\python.exe`. The desktop interface requires a graphical session and Tk. The headless demonstration runs with `python demo.py` after dependencies are installed.

## Product coverage

| Product | Features demonstrated |
| --- | --- |
| SMS | Baseline/Enterprise; US DSC, Toll Free and 10DLC; Canada DSC and Toll Free |
| Premium SMS | Separate premium source prices; the same sender options |
| Local SMS | Selected local destinations replace standard prices after sender overrides |
| Local Premium SMS | Local premium overrides with standard premium pricing elsewhere |
| SMS Marketing | Independent marketing prices; no sender or local options |
| Voice Verify | Per Transaction or Per Minute; separate mobile and landline prices |
| Voice | 1-Way/2-Way; US Cloud Numbers/Global Mobile Numbers |
| Voice Verify + TTS | 1-Way/2-Way; inbound handling and fallback behavior |
| Toll-Free Voice | Inbound and outbound mobile/landline prices |
| Mobile (SMS and Voice) | Two files for 1-Way, three for 2-Way; independent availability filtering |
| WhatsApp | Universal fee from the dynamically located Other row |
| Viber | Cost and selected margin produce four message-category prices |
| Phone ID Suite | Required Standard plus 11 optional subproducts, separate CSVs and availability filtering |
| Phone ID Live Status | Single-price mobile/landline output without a pricing-tier selection |

The supplied v1.3.1 catalog calls the toll-free product **Toll-Free Voice** and the live product **Phone ID Live Status**. RCS remains disabled, as in the source release.

**Countries:** United States, Canada, United Kingdom, Germany, Brazil and Serbia. Local pricing is demonstrated for US, Brazil and Serbia. Country coverage is deliberately small; availability flags are fictional demonstrations, not commercial availability statements. WhatsApp deliberately exports only its universal fee row.

See the [feature walkthrough](docs/DEMO_WALKTHROUGH.md), [sample exports](examples/README.md), and [architecture](docs/ARCHITECTURE.md).

## What this project demonstrates

- Excel ingestion with strict schemas, grouped headers and currency-specific header aliases.
- Separate GUI, controller, extraction, rule engine, export and logging layers.
- Decimal arithmetic, deterministic override order and product-specific CSV layouts.
- Multi-file generation and filtering of unavailable data without fabricating prices.
- A reusable synthetic dataset, headless demonstration and automatic test workflow.

This is a software and data-automation project. It does not perform price optimization, elasticity modelling or machine learning.

## Verification

The portfolio suite contains 141 tests, including the full 306-scenario integration matrix. Tests cover real synthetic workbook reads, CSV creation, sender/local precedence, output counts, unavailable products, invalid selections, and the v1.3.1 reset behavior. Twenty-five self-contained original test modules are retained; production-workbook-dependent tests are replaced by bundled-fixture integration tests.

GitHub Actions is configured for Windows and Linux on Python 3.11 and 3.12. Local verification was performed on Linux/Python 3.12. Windows UI interaction, Excel COM fallback and the remote Actions matrix must be verified in their target environments; no packaged Windows executable is included.

## Scope and operating limits

- Demo prices are illustrative independent values for USD/EUR/BRL, not exchange-rate conversions.
- CSVs demonstrate the source template formats. They must not be uploaded to client accounts.
- Existing output names may be overwritten. The showcase isolates each scenario to preserve its outputs.
- Logging is best effort: a log-write failure does not invalidate an otherwise successful export.
- Multi-file exports are not a filesystem transaction. A disk/permission failure during writing can leave files from earlier in that batch.
- The original Windows Excel fallback is retained and requires Excel plus `pywin32` when used. Bundled workbook reads do not require Excel.

## Repository guide

| Location | Purpose |
| --- | --- |
| `app/` | Application layers from v1.3.1 |
| `Administration/Configuration/1.3.1/` | Product catalog, workbook and export schemas, demo paths |
| `demo_data/` | 12 synthetic workbooks and transparent fixture manifest |
| `tests/` | Self-contained unit and integration tests |
| `examples/` | One documented USD demonstration per enabled product |
| `demo.py` | Complete headless scenario runner |
| `docs/` | Walkthrough, architecture and portfolio adaptation notes |

Author: [Uroš Petrović](https://github.com/urosrb99petrovic-beep). License: [MIT](LICENSE).
