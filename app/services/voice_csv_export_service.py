import csv
from pathlib import Path
from typing import Any

from app.models.generated_voice_pricing_row import (
    GeneratedVoicePricingRow
)
from app.services.voice_csv_row_builder import (
    VoiceCsvRowBuilder
)


class VoiceCsvExportService:
    """
    Writes generated Voice pricing to a physical CSV file.

    CSV table construction is delegated to VoiceCsvRowBuilder.
    This service is responsible only for file-system and CSV
    writing behaviour.
    """

    QUOTING_MODES = {
        "minimal": csv.QUOTE_MINIMAL,
        "all": csv.QUOTE_ALL,
        "nonnumeric": csv.QUOTE_NONNUMERIC,
        "none": csv.QUOTE_NONE
    }

    def __init__(
        self,
        voice_csv_row_builder: VoiceCsvRowBuilder,
        output_settings: dict[str, Any]
    ) -> None:
        """
        Creates the Voice CSV export service.

        Args:
            voice_csv_row_builder:
                Builds the Voice CSV table.

            output_settings:
                Output configuration from settings.json.
        """

        self._voice_csv_row_builder = (
            voice_csv_row_builder
        )

        self._encoding = str(
            output_settings.get(
                "encoding",
                "utf-8"
            )
        ).strip()

        self._delimiter = str(
            output_settings.get(
                "delimiter",
                ","
            )
        )

        self._overwrite = bool(
            output_settings.get(
                "overwrite_existing_file",
                True
            )
        )

        configured_quoting = str(
            output_settings.get(
                "quoting",
                "minimal"
            )
        ).strip().casefold()

        if configured_quoting not in self.QUOTING_MODES:
            raise ValueError(
                f"Unsupported CSV quoting mode "
                f"'{configured_quoting}'."
            )

        self._quoting = self.QUOTING_MODES[
            configured_quoting
        ]

        if not self._encoding:
            raise ValueError(
                "Voice CSV encoding cannot be empty."
            )

        if len(self._delimiter) != 1:
            raise ValueError(
                "Voice CSV delimiter must contain "
                "exactly one character."
            )

    def export(
        self,
        generated_rows: list[
            GeneratedVoicePricingRow
        ],
        schema_id: str,
        output_path: Path
    ) -> Path:
        """
        Writes one generated Voice pricing file.

        Args:
            generated_rows:
                Final Voice pricing rows.

            schema_id:
                Voice output schema to use.

            output_path:
                Exact destination CSV path.

        Returns:
            Path to the written CSV file.

        Raises:
            ValueError:
                If the output path is invalid.

            FileExistsError:
                If the file already exists and overwrite is
                disabled.

            NotADirectoryError:
                If the output parent is not a directory.

            PermissionError:
                If the output location cannot be written.
        """

        output_path = Path(
            output_path
        )

        self._validate_output_path(
            output_path
        )

        csv_rows = (
            self._voice_csv_row_builder.build_rows(
                generated_rows=generated_rows,
                schema_id=schema_id
            )
        )

        output_directory = (
            output_path.parent
        )

        output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        if not output_directory.is_dir():
            raise NotADirectoryError(
                f"Voice CSV output location is not "
                f"a directory: "
                f"'{output_directory}'."
            )

        if (
            output_path.exists()
            and not self._overwrite
        ):
            raise FileExistsError(
                f"Voice CSV output file already exists: "
                f"'{output_path}'."
            )

        try:
            with output_path.open(
                mode="w",
                encoding=self._encoding,
                newline=""
            ) as output_file:

                csv_writer = csv.writer(
                    output_file,
                    delimiter=self._delimiter,
                    quoting=self._quoting,
                    lineterminator="\n"
                )

                csv_writer.writerows(
                    csv_rows
                )

        except PermissionError:
            raise PermissionError(
                f"Voice CSV could not be written to "
                f"'{output_path}'. "
                f"The file or folder may be locked or "
                f"you may not have permission to write there."
            )

        return output_path

    @staticmethod
    def _validate_output_path(
        output_path: Path
    ) -> None:
        """
        Validates the requested physical output path.
        """

        if not output_path.name:
            raise ValueError(
                "Voice CSV output filename cannot be empty."
            )

        if (
            output_path.suffix.casefold()
            != ".csv"
        ):
            raise ValueError(
                "Voice output file must use the .csv "
                "extension."
            )