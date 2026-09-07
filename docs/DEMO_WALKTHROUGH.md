# Product demonstration walkthrough

Start with USD. All numbers below are fictional fixture values, in the selected workbook currency. Run `python demo.py` to exercise the complete matrix automatically, or use the desktop app for these demonstrations.

| Step | Selection | What to inspect |
| --- | --- | --- |
| 1 | SMS, Baseline, default senders | US price is 0.0480; six destinations plus the default row |
| 2 | SMS, Baseline, US 10DLC | US becomes 0.0950; other destinations retain base prices |
| 3 | Local SMS, Baseline, US 10DLC, local US | US becomes 0.0690 because the local rule applies last |
| 4 | Premium SMS and Local Premium SMS | Compare their independent source prices and local overrides |
| 5 | SMS Marketing, Enterprise | No sender or local selections; its own marketing sheet |
| 6 | Voice Verify, each billing choice | Compare the transaction and per-minute template layouts |
| 7 | Voice, each traffic and number choice | Four option combinations; inspect inbound handling for Serbia |
| 8 | Voice Verify + TTS, both traffic choices | Compare outbound-only and two-way exports |
| 9 | Toll-Free Voice | Inbound and outbound mobile/landline columns |
| 10 | Mobile, 1-Way then 2-Way | Two versus three outputs; Serbia has no inbound price and is omitted where required |
| 11 | WhatsApp, Baseline | One default pricing row (0.0440); country-specific source rows are intentionally ignored |
| 12 | Viber, Baseline then Enterprise | Four categories; country price = cost / (1 - selected margin), rounded to four decimals; default row uses displayed prices |
| 13 | Phone ID Suite, select all | Twelve files. Standard is required; unavailable values are omitted independently per subproduct |
| 14 | Phone ID Live Status | Mobile/landline prices; no Baseline/Enterprise selection |

For Phone ID SIM Swap, the UK fixture is unavailable and should not appear in that export. The default Phone ID price remains numeric for every subproduct.

Repeat with EUR and BRL to demonstrate workbook routing and currency-specific Mobile header aliases. These values differ by design; the generator selects an existing currency workbook rather than converting rates.

After a successful desktop generation, click OK and verify that the app remains open on a clean Home page. Cancel still exits. A rejected request should retain the selections for correction.

## Inspecting results

Use a text editor to see exact CSV headers and empty fields. Spreadsheet applications may reinterpret decimal formatting and blank cells. The files retain the product-specific v1.3.1 templates rather than flattening all products into one generic CSV.

The full showcase writes `demo_output/showcase/manifest.json`, with each request and its output paths. Each scenario has a separate directory, so multiple sender/traffic choices do not overwrite one another.

## Maintaining the fictional fixtures

Open the relevant workbook in `demo_data/<currency>`. Preserve sheet names, header rows, grouped headers and default-row positions, then edit numeric prices or recognized availability markers. Save and close Excel before running tests.

`fixture_manifest.json` records the shipped fixture values; update it and the numerical contract tests if intentionally changing those examples. Do not replace demo workbooks with real commercial files in the public repository.
