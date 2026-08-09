from pathlib import Path
from types import TracebackType
from typing import Any, Self

import pandas as pd


class WorkbookService:
    """
    Opens and reads a Pricing Generator source workbook.

    One WorkbookService instance represents one opened workbook.
    Multiple worksheets can be read before the workbook is closed.
    """

    SUPPORTED_EXTENSIONS = {
        ".xlsb",
        ".xlsx",
        ".xlsm"
    }

    EXCEL_ENGINES = {
        ".xlsx": "openpyxl",
        ".xlsm": "openpyxl",
        ".xlsb": "calamine",
    }

    LOCAL_COUNTRY_WORKSHEET = "Local SMS"
    LOCAL_COUNTRY_SUFFIX = " - Local Companies"


    def __init__(
        self,
        workbook_path: Path
    ) -> None:
        """
        Validates and opens a pricing workbook.

        Args:
            workbook_path:
                Path to the source pricing workbook.

        Raises:
            FileNotFoundError:
                If the workbook does not exist.

            ValueError:
                If the path is not a file or its format is
                unsupported.

            RuntimeError:
                If the workbook cannot be opened.
        """

        self._validate_workbook_path(
            workbook_path
        )

        self._workbook_path = workbook_path.resolve()
        self._excel_file: pd.ExcelFile | None = None

        self._open_workbook()

    @property
    def workbook_path(self) -> Path:
        """
        Returns the absolute path of the opened workbook.
        """

        return self._workbook_path

    @property
    def sheet_names(self) -> list[str]:
        """
        Returns the names of all worksheets in the workbook.

        Raises:
            RuntimeError:
                If the workbook has already been closed.
        """

        excel_file = self._require_open_workbook()

        return list(excel_file.sheet_names)

    @property
    def is_open(self) -> bool:
        """
        Indicates whether the workbook is currently open.
        """

        return self._excel_file is not None

    def read_worksheet(
        self,
        worksheet_name: str
    ) -> pd.DataFrame:
        """
        Reads one worksheet from the already opened workbook.

        Args:
            worksheet_name:
                Name of the worksheet to read.

        Returns:
            Raw worksheet contents as a pandas DataFrame.

        Raises:
            ValueError:
                If the worksheet name is empty or the worksheet
                does not exist.

            RuntimeError:
                If the workbook has been closed or the worksheet
                cannot be read.
        """

        if not worksheet_name.strip():
            raise ValueError(
                "Worksheet name cannot be empty."
            )

        excel_file = self._require_open_workbook()

        if worksheet_name not in excel_file.sheet_names:
            raise ValueError(
                f"Worksheet '{worksheet_name}' does not exist "
                f"in workbook '{self._workbook_path.name}'."
            )

        try:
            worksheet_data = excel_file.parse(
                sheet_name=worksheet_name,
                header=None,
                keep_default_na=False
            )

        except Exception as error:
            raise RuntimeError(
                f"Could not read worksheet "
                f"'{worksheet_name}' from workbook "
                f"'{self._workbook_path.name}'. "
                f"Reason: {error}"
            ) from error

        return worksheet_data

    def get_header_indexes(
        self,
        worksheet_data: pd.DataFrame,
        worksheet_schema: dict[str, Any]
    ) -> dict[str, int]:
        """
        Finds configured worksheet columns by their header names.

        Args:
            worksheet_data:
                Raw worksheet contents.

            worksheet_schema:
                Worksheet schema loaded from schemas.json.

        Returns:
            Mapping from logical field names to DataFrame column
            indexes.

            Example:
                {
                    "country": 0,
                    "baseline_price": 4,
                    "enterprise_price": 6
                }

        Raises:
            ValueError:
                If the configured header row is invalid or one or
                more required headers cannot be found.
        """

        header_row_number = worksheet_schema[
            "header_row"
        ]

        header_row_index = header_row_number - 1

        if (
            header_row_index < 0
            or header_row_index >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured header row "
                f"{header_row_number} is outside the worksheet."
            )

        header_values = worksheet_data.iloc[
            header_row_index
        ]

        header_positions: dict[str, list[int]] = {}

        for column_index, header_value in enumerate(
            header_values
        ):
            if pd.isna(header_value):
                continue

            normalized_header = str(
             header_value
            ).strip()

            if not normalized_header:
                continue

            header_positions.setdefault(
                normalized_header,
                []
            ).append(column_index)

        required_headers = worksheet_schema[
            "required_headers"
        ]

        resolved_indexes: dict[str, int] = {}
        missing_headers: list[str] = []
        duplicate_headers: list[str] = []

        for logical_name, required_header in (
            required_headers.items()
        ):
            matching_indexes = header_positions.get(
                required_header,
                []
            )

            if not matching_indexes:
                missing_headers.append(
                    required_header
                )
                continue

            if len(matching_indexes) > 1:
                duplicate_headers.append(
                    required_header
                )
                continue

            resolved_indexes[
                logical_name
            ] = matching_indexes[0]

        if missing_headers:
            missing_header_list = ", ".join(
                f"'{header}'"
                for header in missing_headers
            )

            raise ValueError(
                f"Missing required worksheet header(s): "
                f"{missing_header_list}."
            )

        if duplicate_headers:
            duplicate_header_list = ", ".join(
                f"'{header}'"
                for header in duplicate_headers
            )

            raise ValueError(
                f"Duplicate required worksheet header(s): "
                f"{duplicate_header_list}."
            )

        return resolved_indexes

    def get_local_countries(
        self,
        local_worksheet_schema: dict[str, Any]
    ) -> list[str]:
        """
        Returns the available Local SMS country names using the
        configured local worksheet schema.

        Args:
            local_worksheet_schema:
                Local pricing worksheet schema loaded from
                schemas.json.

        Returns:
            Clean, unique local country names in workbook order.

        Raises:
            ValueError:
                If the configured worksheet structure is invalid.

            RuntimeError:
                If no valid local countries can be extracted.
        """

        worksheet_data = self.read_worksheet(
            self.LOCAL_COUNTRY_WORKSHEET
        )

        header_indexes = self.get_header_indexes(
            worksheet_data,
            local_worksheet_schema
        )

        country_column_index = header_indexes[
            "country"
        ]

        data_start_row_number = (
            local_worksheet_schema[
                "data_start_row"
            ]
        )

        data_start_row_index = (
            data_start_row_number - 1
        )

        if (
            data_start_row_index < 0
            or data_start_row_index
            >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured data start row "
                f"{data_start_row_number} is outside "
                f"worksheet "
                f"'{self.LOCAL_COUNTRY_WORKSHEET}'."
            )

        country_name_processing = (
            local_worksheet_schema.get(
                "country_name_processing",
                {}
            )
        )

        removable_suffix = (
            country_name_processing.get(
                "remove_suffix",
                self.LOCAL_COUNTRY_SUFFIX
            )
        )

        trim_whitespace = (
            country_name_processing.get(
                "trim_whitespace",
                True
            )
        )

        country_column = worksheet_data.iloc[
            data_start_row_index:,
            country_column_index
        ]

        local_countries: list[str] = []
        seen_countries: set[str] = set()

        for worksheet_value in country_column:
            if pd.isna(worksheet_value):
                continue

            country_name = self.normalize_local_country_name(
                worksheet_value=worksheet_value,
                removable_suffix=removable_suffix,
                trim_whitespace=trim_whitespace
            )

            if not country_name:
                continue

            if country_name in seen_countries:
                continue

            seen_countries.add(country_name)
            local_countries.append(country_name)

        if not local_countries:
            raise RuntimeError(
                f"No local countries were found in worksheet "
                f"'{self.LOCAL_COUNTRY_WORKSHEET}' of workbook "
                f"'{self._workbook_path.name}'."
            )

        return local_countries

    def close(self) -> None:
        """
        Closes the workbook if it is currently open.
        """

        if self._excel_file is not None:
            self._excel_file.close()
            self._excel_file = None

    def __enter__(self) -> Self:
        """
        Returns this service when used in a with statement.
        """

        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        traceback: TracebackType | None
    ) -> None:
        """
        Closes the workbook when leaving a with statement.
        """

        self.close()

    @staticmethod
    def normalize_local_country_name(
        worksheet_value: object,
        removable_suffix: str = " - Local Companies",
        trim_whitespace: bool = True
    ) -> str:
        """
        Converts a local worksheet value into a clean country name.

        Args:
            worksheet_value:
                Raw country value read from the worksheet.

            removable_suffix:
                Suffix removed when it appears at the end of the
                country value.

            trim_whitespace:
                Whether surrounding whitespace should be removed.

        Returns:
            Clean country name.
        """

        country_name = str(
            worksheet_value
        )

        if trim_whitespace:
            country_name = country_name.strip()

        if (
            removable_suffix
            and country_name.endswith(
                removable_suffix
            )
        ):
            country_name = country_name[
                :-len(removable_suffix)
            ]

            if trim_whitespace:
                country_name = country_name.strip()

        return country_name

    def _open_workbook(self) -> None:
        """
        Opens the workbook using pandas and the Calamine engine.

        Raises:
            RuntimeError:
                If the workbook cannot be opened.
        """

        try:
            self._excel_file = pd.ExcelFile(
                self._workbook_path,
                engine=self.EXCEL_ENGINES[self._workbook_path.suffix.lower()]
            )

        except Exception as error:
            raise RuntimeError(
                f"Could not open pricing workbook "
                f"'{self._workbook_path.name}'. "
                f"Reason: {error}"
            ) from error

    def _require_open_workbook(
        self
    ) -> pd.ExcelFile:
        """
        Returns the opened workbook parser.

        Raises:
            RuntimeError:
                If the workbook has already been closed.
        """

        if self._excel_file is None:
            raise RuntimeError(
                "The pricing workbook is closed."
            )

        return self._excel_file

    @classmethod
    def _validate_workbook_path(
        cls,
        workbook_path: Path
    ) -> None:
        """
        Confirms that the workbook exists, is a file and has a
        supported extension.
        """

        if not workbook_path.exists():
            raise FileNotFoundError(
                f"Pricing workbook does not exist: "
                f"{workbook_path}"
            )

        if not workbook_path.is_file():
            raise ValueError(
                f"Pricing workbook path is not a file: "
                f"{workbook_path}"
            )

        workbook_extension = (
            workbook_path.suffix.lower()
        )

        if workbook_extension not in cls.SUPPORTED_EXTENSIONS:
            supported_extensions = ", ".join(
                sorted(cls.SUPPORTED_EXTENSIONS)
            )

            raise ValueError(
                f"Unsupported pricing workbook format "
                f"'{workbook_extension}'. Supported formats: "
                f"{supported_extensions}."
            )
