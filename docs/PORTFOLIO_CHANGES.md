# Portfolio adaptation of v1.3.1

- Preserved the 14 enabled products, 12 Phone ID Suite subproducts, disabled RCS entry, pricing rules and output schemas.
- Replaced source workbook paths with 12 bundled synthetic XLSX files across three currencies.
- Used six countries, including deliberate unavailable values and unsupported inbound prices.
- Moved the entry point to the repository root and made GUI imports lazy for headless execution.
- Corrected the `customertkinter` dependency typo and declared Calamine and Windows COM dependencies.
- Added pricing type to demo filenames when applicable to distinguish Baseline and Enterprise outputs.
- Added a visible synthetic-demo label, Windows setup/run scripts, a full scenario runner and selected exports.
- Retained 25 self-contained original test modules and added synthetic end-to-end coverage. Corrected a test that assumed August 2026.
- Excluded older configurations, production executables, personal build specifications, production-dependent tests and runtime logs.

No elasticity, price optimization or cancelled simulator functionality is included. Version 1.3.1 identifies the source application; this repository is its separately documented portfolio adaptation.
