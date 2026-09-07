# Verification record

Verified on Linux / Python 3.12 using the final portfolio source and bundled fictional workbooks.

- 141 unittest tests passed, including 306 end-to-end configuration scenarios.
- Standalone demo completed 306 scenarios and generated 357 CSVs.
- 27 selected example CSVs cover all 14 enabled products.
- 12 XLSX files open through the application Calamine reader across USD/EUR/BRL.
- Workbook layouts visually reviewed across all 16 distinct sheets in the USD set; equivalent layouts used for EUR/BRL.
- Public source and documentation scanned for workspace paths, Windows user paths, username placeholders and credential assignments; none found in the final scan.
- No production workbooks, executables, build paths or runtime logs included.

Not executed here: interactive Windows GUI, Excel COM fallback, packaged executable build, and the remote GitHub Actions matrix. GitHub Actions is configured to run after upload.

The test suite retains 25 self-contained original modules plus one new integration module. Historical tests tied to production workbooks and older configuration directories are not shipped.
