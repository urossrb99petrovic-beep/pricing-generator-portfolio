# Architecture and design notes

## Request lifecycle

1. The interface creates a `GenerationRequest` containing currency, product, pricing type, sender choices, and selected local countries.
2. `PricingGeneratorController` validates the request against enabled products and supported options.
3. `PathResolver` selects the configured currency workbook.
4. `WorkbookService` opens the workbook once and exposes validated worksheet operations.
5. `PricingDataService` converts worksheet cells into typed `PricingRow` and `SenderOverridePrice` values.
6. `PricingGenerationService` loads the inputs required by the selected product.
7. `GenerationEngine` selects base prices and applies relevant overrides in a defined order.
8. `CsvExportService` renders the configured template and writes the completed file.
9. `LoggingService` records success or failure without masking the primary application outcome.

## Separation of concerns

The design keeps five types of change apart:

| Change | Primary location |
|---|---|
| Workbook layout | schema configuration and `PricingDataService` |
| Product availability | product configuration |
| Pricing precedence | `GenerationEngine` |
| CSV template | output schema and `CsvExportService` |
| Desktop presentation | `app/ui` |

This is valuable because operational workbooks and import templates can evolve independently. It also allows domain rules to be tested without opening Excel or starting a desktop window.

## Validation boundaries

- Configuration: required files, keys, versions, types, and cross-file values
- Filesystem: project root, configured placeholders, workbook existence and extension
- Workbook: supported format, required worksheet, header row, headers, duplicate headers, and row values
- Request: supported currency, enabled product, pricing type, sender choice, and local-country selection
- Domain: nonempty inputs, supported price type, unique destination keys, and required override data
- Export: output configuration, filename, delimiter, quoting, price format, destination, and overwrite policy

## Design trade-offs

The application uses explicit rule branches rather than a generic rules engine. For a bounded set of pricing products, this keeps precedence visible and debuggable. If the number of products or rule combinations grew substantially, I would move rule definitions toward validated configuration objects or a rule registry while retaining typed domain tests.

The desktop application is appropriate for a local, workbook-based process and simple deployment to nontechnical users. A multi-user workflow, centralized access control, or concurrent generation would justify moving the same application services behind an internal API or web interface.

## Testing strategy for the synthetic demo

- Unit tests for price selection, null behavior, sender overrides, local overrides, and precedence
- Property-style checks for duplicate destinations and invariant output ordering
- Workbook schema tests using tiny generated `.xlsx` fixtures
- CSV golden-file tests for exact template output
- Controller integration tests covering success and expected failures
- Smoke test that starts the application with the public configuration
