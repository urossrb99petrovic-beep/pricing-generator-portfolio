from pathlib import Path
from types import TracebackType
from typing import Any, Self

import pandas as pd


class WorkbookService:
    """
    Opens and reads a Pricing Generator source workbook.

    Normal behaviour:
        Reads the workbook directly from disk using pandas
        and the Calamine engine.

    Excel-open fallback:
        If direct access fails because Excel has locked the
        workbook, the service attaches to the already-open
        Excel workbook and reads its current values.

    A workbook that was already open in Excel is NEVER
    closed by this service.
    """

    SUPPORTED_EXTENSIONS = {
        ".xlsb",
        ".xlsx",
        ".xlsm"
    }

    EXCEL_ENGINE = "calamine"

    LOCAL_COUNTRY_WORKSHEET = "Local SMS"
    LOCAL_COUNTRY_SUFFIX = " - Local Companies"


    def __init__(
        self,
        workbook_path: Path
    ) -> None:
        """
        Validates and opens a pricing workbook.
        """

        self._validate_workbook_path(
            workbook_path
        )

        self._workbook_path = (
            workbook_path.resolve()
        )

        # --------------------------------------------------
        # Normal file-based workbook reader.
        # --------------------------------------------------

        self._excel_file: (
            pd.ExcelFile | None
        ) = None

        # --------------------------------------------------
        # Excel COM fallback.
        #
        # These are populated only when the workbook is
        # already open in Excel and direct file access is
        # blocked.
        # --------------------------------------------------

        self._com_excel = None
        self._com_workbook = None

        self._com_initialized = False

        # True only when Pricing Generator created its own
        # hidden Excel instance as a read-only fallback.
        self._owns_com_excel = False
        self._owns_com_workbook = False

        # Possible values:
        #
        #   "calamine"
        #   "excel_com"
        #   None
        #
        self._backend: str | None = None

        self._open_workbook()


    @property
    def workbook_path(
        self
    ) -> Path:
        """
        Returns the absolute path of the workbook.
        """

        return self._workbook_path


    @property
    def sheet_names(
        self
    ) -> list[str]:
        """
        Returns all worksheet names.
        """

        self._require_open_workbook()

        # --------------------------------------------------
        # Normal Calamine workbook.
        # --------------------------------------------------

        if (
            self._backend == "calamine"
            and self._excel_file is not None
        ):
            return list(
                self._excel_file.sheet_names
            )

        # --------------------------------------------------
        # Workbook already open in Excel.
        # --------------------------------------------------

        if (
            self._backend == "excel_com"
            and self._com_workbook is not None
        ):
            return [
                str(
                    self._com_workbook
                    .Worksheets
                    .Item(index)
                    .Name
                )
                for index in range(
                    1,
                    (
                        self._com_workbook
                        .Worksheets
                        .Count
                    )
                    + 1
                )
            ]

        raise RuntimeError(
            "The pricing workbook is closed."
        )


    @property
    def is_open(
        self
    ) -> bool:
        """
        Indicates whether this service currently has access
        to the workbook.
        """

        if self._backend == "calamine":
            return (
                self._excel_file is not None
            )

        if self._backend == "excel_com":
            return (
                self._com_workbook is not None
            )

        return False


    @property
    def backend(
        self
    ) -> str | None:
        """
        Returns the workbook access method currently in use.

        Mainly useful for testing and diagnostics.
        """

        return self._backend


    def read_worksheet(
        self,
        worksheet_name: str
    ) -> pd.DataFrame:
        """
        Reads one worksheet from the opened workbook.
        """

        if not worksheet_name.strip():
            raise ValueError(
                "Worksheet name cannot be empty."
            )

        self._require_open_workbook()

        if (
            worksheet_name
            not in self.sheet_names
        ):
            raise ValueError(
                f"Worksheet '{worksheet_name}' "
                f"does not exist in workbook "
                f"'{self._workbook_path.name}'."
            )

        # --------------------------------------------------
        # Existing behaviour:
        # read directly from the physical workbook.
        # --------------------------------------------------

        if (
            self._backend == "calamine"
            and self._excel_file is not None
        ):
            try:
                return (
                    self._excel_file.parse(
                        sheet_name=(
                            worksheet_name
                        ),
                        header=None,
                        keep_default_na=False
                    )
                )

            except Exception as error:
                raise RuntimeError(
                    f"Could not read worksheet "
                    f"'{worksheet_name}' from workbook "
                    f"'{self._workbook_path.name}'. "
                    f"Reason: {error}"
                ) from error

        # --------------------------------------------------
        # Excel fallback:
        # read values from the workbook that the user
        # already has open.
        # --------------------------------------------------

        if (
            self._backend == "excel_com"
            and self._com_workbook is not None
        ):
            return (
                self._read_worksheet_from_excel(
                    worksheet_name
                )
            )

        raise RuntimeError(
            "The pricing workbook is closed."
        )


    def get_header_indexes(
        self,
        worksheet_data: pd.DataFrame,
        worksheet_schema: dict[str, Any]
    ) -> dict[str, int]:
        """
        Finds configured worksheet columns by their header names.
        """

        header_row_number = (
            worksheet_schema[
                "header_row"
            ]
        )

        header_row_index = (
            header_row_number - 1
        )

        if (
            header_row_index < 0
            or header_row_index
            >= len(
                worksheet_data.index
            )
        ):
            raise ValueError(
                f"Configured header row "
                f"{header_row_number} is outside "
                f"the worksheet."
            )

        header_values = (
            worksheet_data.iloc[
                header_row_index
            ]
        )

        header_positions: dict[
            str,
            list[int]
        ] = {}

        for (
            column_index,
            header_value
        ) in enumerate(
            header_values
        ):
            if pd.isna(
                header_value
            ):
                continue

            normalized_header = (
                str(
                    header_value
                )
                .strip()
            )

            if not normalized_header:
                continue

            header_positions.setdefault(
                normalized_header,
                []
            ).append(
                column_index
            )

        required_headers = (
            worksheet_schema[
                "required_headers"
            ]
        )

        resolved_indexes: dict[
            str,
            int
        ] = {}

        missing_headers: list[
            str
        ] = []

        duplicate_headers: list[
            str
        ] = []

        for (
            logical_name,
            required_header
        ) in required_headers.items():

            matching_indexes = (
                header_positions.get(
                    required_header,
                    []
                )
            )

            if not matching_indexes:
                missing_headers.append(
                    required_header
                )
                continue

            if len(
                matching_indexes
            ) > 1:
                duplicate_headers.append(
                    required_header
                )
                continue

            resolved_indexes[
                logical_name
            ] = (
                matching_indexes[0]
            )

        if missing_headers:
            missing_header_list = (
                ", ".join(
                    f"'{header}'"
                    for header
                    in missing_headers
                )
            )

            raise ValueError(
                f"Missing required worksheet "
                f"header(s): "
                f"{missing_header_list}."
            )

        if duplicate_headers:
            duplicate_header_list = (
                ", ".join(
                    f"'{header}'"
                    for header
                    in duplicate_headers
                )
            )

            raise ValueError(
                f"Duplicate required worksheet "
                f"header(s): "
                f"{duplicate_header_list}."
            )

        return resolved_indexes


    def get_local_countries(
        self,
        local_worksheet_schema: dict[
            str,
            Any
        ]
    ) -> list[str]:
        """
        Returns the available Local SMS country names.
        """

        worksheet_data = (
            self.read_worksheet(
                self.LOCAL_COUNTRY_WORKSHEET
            )
        )

        header_indexes = (
            self.get_header_indexes(
                worksheet_data,
                local_worksheet_schema
            )
        )

        country_column_index = (
            header_indexes[
                "country"
            ]
        )

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
            >= len(
                worksheet_data.index
            )
        ):
            raise ValueError(
                f"Configured data start row "
                f"{data_start_row_number} "
                f"is outside worksheet "
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

        country_column = (
            worksheet_data.iloc[
                data_start_row_index:,
                country_column_index
            ]
        )

        local_countries: list[
            str
        ] = []

        seen_countries: set[
            str
        ] = set()

        for worksheet_value in (
            country_column
        ):
            if pd.isna(
                worksheet_value
            ):
                continue

            country_name = (
                self.normalize_local_country_name(
                    worksheet_value=(
                        worksheet_value
                    ),
                    removable_suffix=(
                        removable_suffix
                    ),
                    trim_whitespace=(
                        trim_whitespace
                    )
                )
            )

            if not country_name:
                continue

            if (
                country_name
                in seen_countries
            ):
                continue

            seen_countries.add(
                country_name
            )

            local_countries.append(
                country_name
            )

        if not local_countries:
            raise RuntimeError(
                f"No local countries were found "
                f"in worksheet "
                f"'{self.LOCAL_COUNTRY_WORKSHEET}' "
                f"of workbook "
                f"'{self._workbook_path.name}'."
            )

        return local_countries


    def close(
        self
    ) -> None:
        """
        Releases workbook resources.

        Calamine:
            Closes the normal file reader.

        Excel fallback:
            Closes ONLY the hidden read-only workbook created
            by Pricing Generator and quits ONLY that hidden
            Excel instance.

        Any workbook the user already had open is unaffected.
        """

        # --------------------------------------------------
        # Normal file-based workbook.
        # --------------------------------------------------

        if self._excel_file is not None:
            self._excel_file.close()

            self._excel_file = None

        # --------------------------------------------------
        # Hidden Excel read-only fallback.
        # --------------------------------------------------

        if (
            self._com_workbook is not None
            and self._owns_com_workbook
        ):
            try:
                self._com_workbook.Close(
                    SaveChanges=False
                )

            except Exception:
                pass

        self._com_workbook = None

        if (
            self._com_excel is not None
            and self._owns_com_excel
        ):
            try:
                self._com_excel.Quit()

            except Exception:
                pass

        self._com_excel = None

        self._owns_com_workbook = False
        self._owns_com_excel = False

        self._backend = None

        if self._com_initialized:
            try:
                import pythoncom

                pythoncom.CoUninitialize()

            finally:
                self._com_initialized = False


    def __enter__(
        self
    ) -> Self:
        """
        Returns this service when used in a with statement.
        """

        return self


    def __exit__(
        self,
        exception_type: (
            type[BaseException]
            | None
        ),
        exception_value: (
            BaseException
            | None
        ),
        traceback: (
            TracebackType
            | None
        )
    ) -> None:
        """
        Releases workbook resources when leaving a with
        statement.
        """

        self.close()


    @staticmethod
    def normalize_local_country_name(
        worksheet_value: object,
        removable_suffix: (
            str
        ) = " - Local Companies",
        trim_whitespace: bool = True
    ) -> str:
        """
        Converts a local worksheet value into a clean country name.
        """

        country_name = str(
            worksheet_value
        )

        if trim_whitespace:
            country_name = (
                country_name.strip()
            )

        if (
            removable_suffix
            and country_name.endswith(
                removable_suffix
            )
        ):
            country_name = (
                country_name[
                    :-len(
                        removable_suffix
                    )
                ]
            )

            if trim_whitespace:
                country_name = (
                    country_name.strip()
                )

        return country_name


    def _open_workbook(
        self
    ) -> None:
        """
        Opens the workbook.

        First choice:
            pandas + Calamine.

        Fallback:
            If the physical workbook cannot be accessed due
            to a permission/file-lock error, attach to the
            copy already open in Excel.
        """

        try:
            self._excel_file = (
                pd.ExcelFile(
                    self._workbook_path,
                    engine=(
                        self.EXCEL_ENGINE
                    )
                )
            )

            self._backend = (
                "calamine"
            )

            return

        except Exception as error:

            if not self._is_permission_error(
                error
            ):
                raise RuntimeError(
                    f"Could not open pricing "
                    f"workbook "
                    f"'{self._workbook_path.name}'. "
                    f"Reason: {error}"
                ) from error

            direct_access_error = (
                error
            )

        # --------------------------------------------------
        # Direct file access was denied.
        #
        # This usually means Excel currently has the file
        # locked. Open a separate read-only copy through a
        # hidden Excel instance.
        # --------------------------------------------------

        try:
            self._open_read_only_excel_workbook()

        except Exception as excel_error:
            raise RuntimeError(
                f"Could not open pricing workbook "
                f"'{self._workbook_path.name}'. "
                f"Direct file access was denied and "
                f"Excel could not open a read-only copy. "
                f"Direct access reason: "
                f"{direct_access_error}. "
                f"Excel read-only reason: "
                f"{excel_error}"
            ) from direct_access_error


    def _open_read_only_excel_workbook(
        self
    ) -> None:
        """
        Opens the locked workbook in a separate hidden Excel
        instance in read-only mode.

        This does NOT connect to, save, close or otherwise
        interfere with the workbook the user already has open.
        """

        try:
            import pythoncom
            import win32com.client

        except ImportError as error:
            raise RuntimeError(
                "Excel workbook fallback requires "
                "the 'pywin32' package."
            ) from error

        pythoncom.CoInitialize()

        self._com_initialized = True

        excel_application = None
        workbook = None

        try:
            # --------------------------------------------------
            # DispatchEx creates a NEW Excel process rather than
            # attaching to whichever Excel instance happens to
            # be registered as active.
            # --------------------------------------------------

            excel_application = (
                win32com.client.DispatchEx(
                    "Excel.Application"
                )
            )

            excel_application.Visible = False
            excel_application.DisplayAlerts = False
            excel_application.ScreenUpdating = False

            # --------------------------------------------------
            # Disable VBA macros while programmatically opening
            # the pricing workbook.
            #
            # 3 = msoAutomationSecurityForceDisable
            # --------------------------------------------------

            previous_security = (
                excel_application
                .AutomationSecurity
            )

            excel_application.AutomationSecurity = 3

            try:
                workbook = (
                    excel_application
                    .Workbooks
                    .Open(
                        Filename=str(
                            self._workbook_path
                        ),
                        UpdateLinks=0,
                        ReadOnly=True,
                        IgnoreReadOnlyRecommended=True,
                        Notify=False,
                        AddToMru=False
                    )
                )

            finally:
                # Restore the Excel instance's normal security
                # setting immediately after the open operation.
                excel_application.AutomationSecurity = (
                    previous_security
                )

            self._com_excel = (
                excel_application
            )

            self._com_workbook = (
                workbook
            )

            self._owns_com_excel = True
            self._owns_com_workbook = True

            self._backend = (
                "excel_com"
            )

        except Exception as error:

            # --------------------------------------------------
            # Clean up our hidden Excel instance if opening the
            # workbook failed.
            # --------------------------------------------------

            if workbook is not None:
                try:
                    workbook.Close(
                        SaveChanges=False
                    )
                except Exception:
                    pass

            if excel_application is not None:
                try:
                    excel_application.Quit()
                except Exception:
                    pass

            self._com_workbook = None
            self._com_excel = None

            self._owns_com_excel = False
            self._owns_com_workbook = False

            self._backend = None

            self._release_com_initialization()

            raise RuntimeError(
                f"Could not open locked pricing workbook "
                f"'{self._workbook_path.name}' "
                f"in Excel read-only mode. "
                f"Reason: {error}"
            ) from error

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

    def get_header_indexes_in_range(
        self,
        worksheet_data: pd.DataFrame,
        worksheet_schema: dict[str, Any]
    ) -> dict[str, int]:
        """
        Finds configured worksheet headers only within a
        configured Excel column range.

        Used when the same header names may appear elsewhere
        on the same worksheet.

        Example:

            Phone ID Suite pricing table:
                B:O

            Other repeated headers farther right:
                ignored.
        """

        header_row_number = (
            worksheet_schema[
                "header_row"
            ]
        )

        header_row_index = (
            header_row_number - 1
        )

        if (
            header_row_index < 0
            or header_row_index
            >= len(
                worksheet_data.index
            )
        ):
            raise ValueError(
                f"Configured header row "
                f"{header_row_number} is outside "
                f"the worksheet."
            )

        start_column_letter = str(
            worksheet_schema.get(
                "header_start_column",
                ""
            )
        ).strip()

        end_column_letter = str(
            worksheet_schema.get(
                "header_end_column",
                ""
            )
        ).strip()

        if (
            not start_column_letter
            or not end_column_letter
        ):
            raise ValueError(
                "Header start and end columns "
                "must both be configured."
            )

        start_column_index = (
            self._excel_column_to_zero_based_index(
                start_column_letter
            )
        )

        end_column_index = (
            self._excel_column_to_zero_based_index(
                end_column_letter
            )
        )

        if (
            start_column_index
            > end_column_index
        ):
            raise ValueError(
                f"Header start column "
                f"'{start_column_letter}' cannot be "
                f"after end column "
                f"'{end_column_letter}'."
            )

        if (
            end_column_index
            >= len(
                worksheet_data.columns
            )
        ):
            raise ValueError(
                f"Configured header end column "
                f"'{end_column_letter}' is outside "
                f"the worksheet."
            )

        header_values = (
            worksheet_data.iloc[
                header_row_index
            ]
        )

        header_positions: dict[
            str,
            list[int]
        ] = {}

        for column_index in range(
            start_column_index,
            end_column_index + 1
        ):
            header_value = (
                header_values.iloc[
                    column_index
                ]
            )

            if pd.isna(
                header_value
            ):
                continue

            normalized_header = (
                str(
                    header_value
                )
                .strip()
            )

            if not normalized_header:
                continue

            header_positions.setdefault(
                normalized_header,
                []
            ).append(
                column_index
            )

        required_headers = (
            worksheet_schema[
                "required_headers"
            ]
        )

        resolved_indexes: dict[
            str,
            int
        ] = {}

        missing_headers: list[
            str
        ] = []

        duplicate_headers: list[
            str
        ] = []

        for (
            logical_name,
            required_header
        ) in required_headers.items():

            matching_indexes = (
                header_positions.get(
                    required_header,
                    []
                )
            )

            if not matching_indexes:
                missing_headers.append(
                    required_header
                )

                continue

            if (
                len(
                    matching_indexes
                )
                > 1
            ):
                duplicate_headers.append(
                    required_header
                )

                continue

            resolved_indexes[
                logical_name
            ] = matching_indexes[0]

        if missing_headers:
            missing_header_list = (
                ", ".join(
                    f"'{header}'"
                    for header
                    in missing_headers
                )
            )

            raise ValueError(
                f"Missing required worksheet "
                f"header(s) within Excel columns "
                f"{start_column_letter}:"
                f"{end_column_letter}: "
                f"{missing_header_list}."
            )

        if duplicate_headers:
            duplicate_header_list = (
                ", ".join(
                    f"'{header}'"
                    for header
                    in duplicate_headers
                )
            )

            raise ValueError(
                f"Duplicate required worksheet "
                f"header(s) within Excel columns "
                f"{start_column_letter}:"
                f"{end_column_letter}: "
                f"{duplicate_header_list}."
            )

        return resolved_indexes

    def get_grouped_header_indexes(
        self,
        worksheet_data: pd.DataFrame,
        worksheet_schema: dict[str, Any]
    ) -> dict[str, int]:
        """
        Finds worksheet columns that use a two-row grouped header.

        Example:

            Row 1:  Baseline        [merged blank]
            Row 2:  Mobile          Landline

        The blank second cell in the merged Row 1 header is treated
        as belonging to the preceding group.

        Args:
            worksheet_data:
                Raw worksheet contents.

            worksheet_schema:
                Worksheet schema containing header_rows and
                required_headers.

        Returns:
            Mapping from logical field names to DataFrame column
            indexes.

        Raises:
            ValueError:
                If header-row configuration is invalid, a required
                grouped header is missing, or a required grouped
                header matches more than one column.
        """

        header_rows = worksheet_schema.get(
            "header_rows"
        )

        if not header_rows:
            raise ValueError(
                "Grouped worksheet schema must define "
                "'header_rows'."
            )

        group_row_number = header_rows.get(
            "group_row"
        )

        detail_row_number = header_rows.get(
            "detail_row"
        )

        if (
            not isinstance(group_row_number, int)
            or not isinstance(detail_row_number, int)
        ):
            raise ValueError(
                "Grouped worksheet header rows must be integers."
            )

        group_row_index = group_row_number - 1
        detail_row_index = detail_row_number - 1

        for row_number, row_index in (
            (
                group_row_number,
                group_row_index
            ),
            (
                detail_row_number,
                detail_row_index
            )
        ):
            if (
                row_index < 0
                or row_index >= len(
                    worksheet_data.index
                )
            ):
                raise ValueError(
                    f"Configured grouped header row "
                    f"{row_number} is outside the worksheet."
                )

        group_row = worksheet_data.iloc[
            group_row_index
        ]

        detail_row = worksheet_data.iloc[
            detail_row_index
        ]

        header_positions: dict[
            tuple[str, str],
            list[int]
        ] = {}

        current_group = ""

        for column_index in range(
            len(worksheet_data.columns)
        ):
            raw_group_value = group_row.iloc[
                column_index
            ]

            if (
                raw_group_value is None
                or pd.isna(raw_group_value)
            ):
                normalized_group = ""
            else:
                normalized_group = str(
                    raw_group_value
                ).strip()

            if normalized_group:
                current_group = normalized_group

            raw_detail_value = detail_row.iloc[
                column_index
            ]

            if (
                raw_detail_value is None
                or pd.isna(raw_detail_value)
            ):
                normalized_detail = ""
            else:
                normalized_detail = str(
                    raw_detail_value
                ).strip()

            if not current_group:
                continue

            header_key = (
                current_group,
                normalized_detail
            )

            header_positions.setdefault(
                header_key,
                []
            ).append(
                column_index
            )

        required_headers = worksheet_schema.get(
            "required_headers",
            {}
        )

        resolved_indexes: dict[str, int] = {}

        missing_headers: list[str] = []
        duplicate_headers: list[str] = []

        for logical_name, header_definition in (
            required_headers.items()
        ):
            required_group = str(
                header_definition.get(
                    "group",
                    ""
                )
            ).strip()

            required_detail_value = (
                header_definition.get(
                    "detail"
                )
            )

            if required_detail_value is None:
                required_detail = ""
            else:
                required_detail = str(
                    required_detail_value
                ).strip()

            header_key = (
                required_group,
                required_detail
            )

            matching_indexes = (
                header_positions.get(
                    header_key,
                    []
                )
            )

            readable_header = required_group

            if required_detail:
                readable_header = (
                    f"{required_group} / "
                    f"{required_detail}"
                )

            if not matching_indexes:
                missing_headers.append(
                    readable_header
                )
                continue

            if len(matching_indexes) > 1:
                duplicate_headers.append(
                    readable_header
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
                "Missing required grouped worksheet "
                f"header(s): {missing_header_list}."
            )

        if duplicate_headers:
            duplicate_header_list = ", ".join(
                f"'{header}'"
                for header in duplicate_headers
            )

            raise ValueError(
                "Duplicate required grouped worksheet "
                f"header(s): {duplicate_header_list}."
            )

        return resolved_indexes

    def get_header_indexes_with_aliases(
        self,
        worksheet_data: pd.DataFrame,
        worksheet_schema: dict[str, Any]
    ) -> dict[str, int]:
        """
        Finds worksheet columns where each logical field may have
        more than one accepted header name.

        This is useful when equivalent workbooks use different
        currency-specific headers or contain known legacy spelling
        differences.

        Example:

            baseline_price:
                - Baseline Price $
                - Baseline Price (EUR)
                - Baseline Price (BRL)

        Returns:
            Mapping from logical field names to DataFrame column
            indexes.

        Raises:
            ValueError:
                If the header row is invalid, no accepted alias is
                found for a required field, or more than one accepted
                alias is present for the same logical field.
        """

        header_row_number = worksheet_schema[
            "header_row"
        ]

        header_row_index = (
            header_row_number - 1
        )

        if (
            header_row_index < 0
            or header_row_index
            >= len(worksheet_data.index)
        ):
            raise ValueError(
                f"Configured header row "
                f"{header_row_number} is outside the worksheet."
            )

        header_values = worksheet_data.iloc[
            header_row_index
        ]

        header_positions: dict[
            str,
            list[int]
        ] = {}

        for column_index, header_value in enumerate(
            header_values
        ):
            if (
                header_value is None
                or pd.isna(header_value)
            ):
                continue

            normalized_header = str(
                header_value
            ).strip()

            if not normalized_header:
                continue

            normalized_key = (
                normalized_header.casefold()
            )

            header_positions.setdefault(
                normalized_key,
                []
            ).append(
                column_index
            )

        required_headers = worksheet_schema[
            "required_headers"
        ]

        resolved_indexes: dict[str, int] = {}

        missing_fields: list[str] = []
        duplicate_fields: list[str] = []

        for logical_name, configured_aliases in (
            required_headers.items()
        ):
            if isinstance(
                configured_aliases,
                str
            ):
                aliases = [
                    configured_aliases
                ]
            else:
                aliases = list(
                    configured_aliases
                )

            matching_indexes: list[int] = []

            for alias in aliases:
                normalized_alias = str(
                    alias
                ).strip().casefold()

                matching_indexes.extend(
                    header_positions.get(
                        normalized_alias,
                        []
                    )
                )

            matching_indexes = list(
                dict.fromkeys(
                    matching_indexes
                )
            )

            if not matching_indexes:
                missing_fields.append(
                    logical_name
                )
                continue

            if len(matching_indexes) > 1:
                duplicate_fields.append(
                    logical_name
                )
                continue

            resolved_indexes[
                logical_name
            ] = matching_indexes[0]

        if missing_fields:
            missing_field_list = ", ".join(
                f"'{field_name}'"
                for field_name
                in missing_fields
            )

            raise ValueError(
                "Missing required aliased worksheet "
                f"header(s) for field(s): "
                f"{missing_field_list}."
            )

        if duplicate_fields:
            duplicate_field_list = ", ".join(
                f"'{field_name}'"
                for field_name
                in duplicate_fields
            )

            raise ValueError(
                "Multiple accepted worksheet headers were found "
                f"for field(s): {duplicate_field_list}."
            )

        return resolved_indexes

    def _read_worksheet_from_excel(
        self,
        worksheet_name: str
    ) -> pd.DataFrame:
        """
        Reads the current worksheet values directly from the
        already-open Excel workbook.

        Values are read from A1 through the last cell in the
        worksheet's UsedRange so configured Excel row and
        column numbers retain the same positions as they have
        when read through Calamine.
        """

        if self._com_workbook is None:
            raise RuntimeError(
                "Excel workbook connection "
                "is not available."
            )

        try:
            worksheet = (
                self._com_workbook
                .Worksheets
                .Item(
                    worksheet_name
                )
            )

            used_range = (
                worksheet.UsedRange
            )

            last_row = (
                used_range.Row
                + used_range.Rows.Count
                - 1
            )

            last_column = (
                used_range.Column
                + used_range.Columns.Count
                - 1
            )

            # Always start at A1.
            #
            # This is important because all of our schemas
            # refer to real Excel row numbers and column
            # positions.
            data_range = (
                worksheet.Range(
                    worksheet.Cells(
                        1,
                        1
                    ),
                    worksheet.Cells(
                        last_row,
                        last_column
                    )
                )
            )

            raw_values = (
                data_range.Value2
            )

            rows = (
                self._convert_excel_values_to_rows(
                    raw_values
                )
            )

            return pd.DataFrame(
                rows
            )

        except Exception as error:
            raise RuntimeError(
                f"Could not read worksheet "
                f"'{worksheet_name}' from the "
                f"already-open Excel workbook "
                f"'{self._workbook_path.name}'. "
                f"Reason: {error}"
            ) from error


    @staticmethod
    def _convert_excel_values_to_rows(
        raw_values: Any
    ) -> list[list[Any]]:
        """
        Converts Excel COM Value2 results into a format
        suitable for pandas.

        Empty Excel cells become empty strings so behaviour
        stays consistent with our existing parser.
        """

        # One-cell range can be returned as a scalar.
        if not isinstance(
            raw_values,
            tuple
        ):
            return [[
                ""
                if raw_values is None
                else raw_values
            ]]

        # Normal multi-cell Excel range:
        #
        # (
        #     (... row 1 ...),
        #     (... row 2 ...),
        # )
        if (
            raw_values
            and isinstance(
                raw_values[0],
                tuple
            )
        ):
            return [
                [
                    ""
                    if value is None
                    else value
                    for value in row
                ]
                for row in raw_values
            ]

        # Defensive handling for a one-dimensional result.
        return [[
            ""
            if value is None
            else value
            for value
            in raw_values
        ]]


    def _require_open_workbook(
        self
    ) -> None:
        """
        Raises if neither workbook backend is available.
        """

        if not self.is_open:
            raise RuntimeError(
                "The pricing workbook is closed."
            )


    @staticmethod
    def _is_permission_error(
        error: BaseException
    ) -> bool:
        """
        Determines whether an exception chain represents a
        Windows file permission / lock error.

        pandas/Calamine may wrap the original PermissionError,
        so the complete exception chain is checked.
        """

        current_error: (
            BaseException | None
        ) = error

        checked_errors: set[int] = set()

        while current_error is not None:

            error_id = id(
                current_error
            )

            if (
                error_id
                in checked_errors
            ):
                break

            checked_errors.add(
                error_id
            )

            if isinstance(
                current_error,
                PermissionError
            ):
                return True

            errno_value = getattr(
                current_error,
                "errno",
                None
            )

            if errno_value == 13:
                return True

            if (
                "permission denied"
                in str(
                    current_error
                ).lower()
            ):
                return True

            current_error = (
                current_error.__cause__
                or current_error.__context__
            )

        return False



    def _release_com_initialization(
        self
    ) -> None:
        """
        Releases COM initialization when attaching to Excel
        fails before the workbook connection is established.
        """

        if not self._com_initialized:
            return

        try:
            import pythoncom

            pythoncom.CoUninitialize()

        finally:
            self._com_initialized = False

    @staticmethod
    def _excel_column_to_zero_based_index(
        column_letter: str
    ) -> int:
        """
        Converts an Excel column name into a zero-based index.

        Examples:

            A  -> 0
            B  -> 1
            O  -> 14
            AA -> 26
        """

        normalized_column = (
            str(
                column_letter
            )
            .strip()
            .upper()
        )

        if not normalized_column:
            raise ValueError(
                "Excel column cannot be empty."
            )

        column_number = 0

        for character in normalized_column:

            if (
                character < "A"
                or character > "Z"
            ):
                raise ValueError(
                    f"Invalid Excel column "
                    f"'{column_letter}'."
                )

            column_number = (
                column_number
                * 26
                + (
                    ord(character)
                    - ord("A")
                    + 1
                )
            )

        return (
            column_number - 1
        )

    @classmethod
    def _validate_workbook_path(
        cls,
        workbook_path: Path
    ) -> None:
        """
        Confirms that the workbook exists, is a file and has
        a supported extension.
        """

        if not workbook_path.exists():
            raise FileNotFoundError(
                f"Pricing workbook does not "
                f"exist: {workbook_path}"
            )

        if not workbook_path.is_file():
            raise ValueError(
                f"Pricing workbook path is "
                f"not a file: {workbook_path}"
            )

        workbook_extension = (
            workbook_path
            .suffix
            .lower()
        )

        if (
            workbook_extension
            not in cls.SUPPORTED_EXTENSIONS
        ):
            supported_extensions = (
                ", ".join(
                    sorted(
                        cls.SUPPORTED_EXTENSIONS
                    )
                )
            )

            raise ValueError(
                f"Unsupported pricing workbook "
                f"format "
                f"'{workbook_extension}'. "
                f"Supported formats: "
                f"{supported_extensions}."
            )