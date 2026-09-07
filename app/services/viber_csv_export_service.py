import csv
from pathlib import Path

from app.models.generated_viber_pricing_row import (
    GeneratedViberPricingRow
)
from app.services.viber_csv_row_builder import (
    ViberCsvRowBuilder
)


class ViberCsvExportService:
    """
    Writes generated Viber pricing into its dedicated
    upload CSV format.
    """

    def __init__(
        self,
        row_builder: ViberCsvRowBuilder,
        output_settings: dict
    ) -> None:

        self._row_builder = row_builder
        self._output_settings = output_settings

    def export(
        self,
        pricing_rows: list[
            GeneratedViberPricingRow
        ],
        output_path: Path
    ) -> Path:
        """
        Writes one Viber CSV.

        The output is UTF-8 without BOM.
        """

        if not pricing_rows:
            raise ValueError(
                "Viber pricing rows cannot be empty."
            )

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        overwrite_existing_file = (
            self._output_settings.get(
                "overwrite_existing_file",
                False
            )
        )

        if (
            output_path.exists()
            and not overwrite_existing_file
        ):
            raise FileExistsError(
                f"Output file already exists: "
                f"{output_path}"
            )

        csv_rows = (
            self._row_builder.build_rows(
                pricing_rows
            )
        )

        with output_path.open(
            mode="w",
            encoding="utf-8",
            newline=""
        ) as csv_file:

            writer = csv.writer(
                csv_file,
                delimiter=",",
                quoting=csv.QUOTE_MINIMAL,
                lineterminator="\n"
            )

            writer.writerows(
                csv_rows
            )

        return output_path