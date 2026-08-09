import json
from datetime import datetime
from pathlib import Path
from typing import Any
import getpass


class LoggingService:
    """
    Creates structured JSON logs for Pricing Generator
    generation attempts.
    """

    def __init__(
        self,
        project_root: Path,
        logging_config: dict[str, Any],
        application_version: str
    ) -> None:
        """
        Initializes the logging service.

        Args:
            project_root:
                Root directory containing USD, EUR, BRL and
                Administration.

            logging_config:
                Logging section loaded from settings.json.

            application_version:
                Current Pricing Generator application version.
        """

        if not isinstance(project_root, Path):
            raise ValueError(
                "Project root must be a Path."
            )

        if not project_root.exists():
            raise FileNotFoundError(
                f"Project root does not exist: "
                f"{project_root}"
            )

        if not project_root.is_dir():
            raise NotADirectoryError(
                f"Project root is not a directory: "
                f"{project_root}"
            )

        if not isinstance(logging_config, dict):
            raise ValueError(
                "Logging configuration must be a dictionary."
            )

        if not application_version.strip():
            raise ValueError(
                "Application version cannot be empty."
            )

        self._project_root = project_root.resolve()
        self._logging_config = logging_config
        self._application_version = (
            application_version.strip()
        )

    def log_success(
        self,
        *,
        currency: str,
        product: str,
        pricing_type: str,
        sender_ids: dict[str, str],
        local_countries: list[str],
        rows_generated: int,
        output_file: Path
    ) -> Path | None:
        """
        Writes a successful generation log.

        Returns:
            Path to the created log file, or None when
            logging/success logging is disabled.
        """

        if not self._should_log(
            successful=True
        ):
            return None

        timestamp = datetime.now()

        log_data = {
            "timestamp": timestamp.isoformat(
                timespec="seconds"
            ),
            "status": "SUCCESS",
            "requested_by": getpass.getuser(),
            "application_version": (
                self._application_version
            ),
            "currency": currency,
            "product": product,
            "pricing_type": pricing_type,
            "sender_ids": sender_ids.copy(),
            "local_countries": local_countries.copy(),
            "rows_generated": rows_generated,
            "output_file": output_file.name
        }

        return self._write_log(
            log_data=log_data,
            timestamp=timestamp,
            currency=currency,
            product=product,
            status="SUCCESS"
        )

    def log_failure(
        self,
        *,
        currency: str,
        product: str,
        pricing_type: str,
        sender_ids: dict[str, str],
        local_countries: list[str],
        error: Exception
    ) -> Path | None:
        """
        Writes a failed generation log.

        Returns:
            Path to the created log file, or None when
            logging/failure logging is disabled.
        """

        if not self._should_log(
            successful=False
        ):
            return None

        timestamp = datetime.now()

        log_data = {
            "timestamp": timestamp.isoformat(
                timespec="seconds"
            ),
            "status": "FAILED",
            "requested_by": getpass.getuser(),
            "application_version": (
                self._application_version
            ),
            "currency": currency,
            "product": product,
            "pricing_type": pricing_type,
            "sender_ids": sender_ids.copy(),
            "local_countries": local_countries.copy(),
            "error_type": type(error).__name__,
            "error_message": str(error)
        }

        return self._write_log(
            log_data=log_data,
            timestamp=timestamp,
            currency=currency,
            product=product,
            status="FAILED"
        )

    def _should_log(
        self,
        *,
        successful: bool
    ) -> bool:
        """
        Determines whether the requested log type is enabled.
        """

        if not self._logging_config.get(
            "enabled",
            False
        ):
            return False

        if successful:
            return self._logging_config.get(
                "include_successful_generations",
                False
            )

        return self._logging_config.get(
            "include_failed_generations",
            False
        )

    def _write_log(
        self,
        *,
        log_data: dict[str, Any],
        timestamp: datetime,
        currency: str,
        product: str,
        status: str
    ) -> Path:
        """
        Creates the required year/month directories and writes
        one JSON generation log.
        """

        log_directory = self._get_log_directory(
            timestamp
        )

        log_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        safe_product = self._make_filename_safe(
            product
        )

        safe_currency = self._make_filename_safe(
            currency
        )

        filename = (
            f"{timestamp:%Y%m%d_%H%M%S}_"
            f"{safe_product}_"
            f"{safe_currency}_"
            f"{status}.json"
        )

        log_path = (
            log_directory
            / filename
        )

        encoding = self._logging_config.get(
            "encoding",
            "utf-8"
        )

        with log_path.open(
            mode="w",
            encoding=encoding
        ) as log_file:
            json.dump(
                log_data,
                log_file,
                ensure_ascii=False,
                indent=4
            )

        return log_path

    def _get_log_directory(
        self,
        timestamp: datetime
    ) -> Path:
        """
        Resolves the configured log directory and folder
        structure.
        """

        directory_pattern = (
            self._logging_config.get(
                "directory",
                (
                    "{project_root}"
                    "/Administration/Logs"
                )
            )
        )

        resolved_directory = (
            directory_pattern.replace(
                "{project_root}",
                str(self._project_root)
            )
        )

        folder_structure = (
            self._logging_config.get(
                "folder_structure",
                (
                    "{application_version}"
                    "/{year}/{month}"
                )
            )
        )

        resolved_structure = (
            folder_structure
            .replace(
                "{application_version}",
                self._application_version
            )
            .replace(
                "{year}",
                f"{timestamp:%Y}"
            )
            .replace(
                "{month}",
                f"{timestamp:%m}"
            )
        )

        return (
            Path(resolved_directory)
            / Path(resolved_structure)
        )

    @staticmethod
    def _make_filename_safe(
        value: str
    ) -> str:
        """
        Removes characters that cannot safely appear in a
        Windows filename.
        """

        cleaned_value = value.strip()

        invalid_characters = (
            '<>:"/\\|?*'
        )

        for character in invalid_characters:
            cleaned_value = (
                cleaned_value.replace(
                    character,
                    "_"
                )
            )

        return cleaned_value.replace(
            " ",
            "_"
        )