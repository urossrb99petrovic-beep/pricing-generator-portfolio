import json
from pathlib import Path
from typing import Any

from app.models.application_config import ApplicationConfig


class ConfigurationService:
    """
    Loads the Pricing Generator configuration files.
    """

    SETTINGS_FILE = "settings.json"
    PRODUCTS_FILE = "products.json"
    COUNTRIES_FILE = "countries.json"
    SCHEMAS_FILE = "schemas.json"

    SETTINGS_REQUIRED_KEYS = [
        "configuration_version",
        "application_name",
        "application_version",
        "template_version",
        "supported_currencies",
        "default_currency",
        "pricing_workbook",
        "output",
        "logging",
        "behaviour"
    ]

    COUNTRIES_REQUIRED_KEYS = [
        "configuration_version",
        "country_name_corrections",
        "sender_overrides"
    ]

    PRODUCTS_REQUIRED_KEYS = [
        "configuration_version",
        "products"
    ]

    SCHEMAS_REQUIRED_KEYS = [
        "configuration_version",
        "workbook_schemas",
        "output_csv_schema",
        "price_selection"
    ]

    def load_configuration(
        self,
        configuration_directory: Path
    ) -> ApplicationConfig:
        """
        Loads all Pricing Generator configuration files.

        Args:
            configuration_directory:
                Folder containing the configuration JSON files.

        Returns:
            Loaded application configuration.
        """

        self._validate_configuration_directory(
            configuration_directory
        )

        settings_path = configuration_directory / self.SETTINGS_FILE
        products_path = configuration_directory / self.PRODUCTS_FILE
        countries_path = configuration_directory / self.COUNTRIES_FILE
        schemas_path = configuration_directory / self.SCHEMAS_FILE

        required_files = [
            settings_path,
            products_path,
            countries_path,
            schemas_path
        ]

        self._validate_required_files(required_files)

        settings = self._load_json_file(settings_path)
        products = self._load_json_file(products_path)
        countries = self._load_json_file(countries_path)
        schemas = self._load_json_file(schemas_path)

        configuration_files = {
            self.SETTINGS_FILE: settings,
            self.PRODUCTS_FILE: products,
            self.COUNTRIES_FILE: countries,
            self.SCHEMAS_FILE: schemas
        }

        self._validate_configuration_versions(
            configuration_directory,
            configuration_files
        )

        self._validate_required_keys(
            self.SETTINGS_FILE,
            settings,
            self.SETTINGS_REQUIRED_KEYS
        )

        self._validate_required_keys(
            self.PRODUCTS_FILE,
            products,
            self.PRODUCTS_REQUIRED_KEYS
        )

        self._validate_required_keys(
            self.COUNTRIES_FILE,
            countries,
            self.COUNTRIES_REQUIRED_KEYS
        )

        self._validate_required_keys(
            self.SCHEMAS_FILE,
            schemas,
            self.SCHEMAS_REQUIRED_KEYS
        )

        return ApplicationConfig(
            settings=settings,
            products=products,
            countries=countries,
            schemas=schemas
        )

    @staticmethod
    def _validate_configuration_directory(
        configuration_directory: Path
    ) -> None:
        """
        Confirms that the configuration directory exists and is a folder.

        Args:
            configuration_directory:
                Folder containing the configuration JSON files.

        Raises:
            FileNotFoundError:
                If the configuration path does not exist.

            NotADirectoryError:
                If the configuration path is not a folder.
        """

        if not configuration_directory.exists():
            raise FileNotFoundError(
                "Configuration directory does not exist: "
                f"{configuration_directory}"
            )

        if not configuration_directory.is_dir():
            raise NotADirectoryError(
                "Configuration path is not a directory: "
                f"{configuration_directory}"
            )

    @staticmethod
    def _validate_required_files(
        required_files: list[Path]
    ) -> None:
        """
        Confirms that all required configuration files exist.

        Args:
            required_files:
                Paths to the required configuration files.

        Raises:
            FileNotFoundError:
                If one or more required files are missing.
        """

        missing_files = [
            file_path.name
            for file_path in required_files
            if not file_path.is_file()
        ]

        if missing_files:
            missing_file_list = ", ".join(missing_files)

            raise FileNotFoundError(
                "Missing required configuration file(s): "
                f"{missing_file_list}"
            )

    @staticmethod
    def _validate_configuration_versions(
        configuration_directory: Path,
        configuration_files: dict[str, dict[str, Any]]
    ) -> None:
        """
        Confirms that every configuration file declares the version
        represented by the configuration folder name.

        Args:
            configuration_directory:
                Versioned folder containing the configuration files.

            configuration_files:
                Loaded configuration data, grouped by filename.

        Raises:
            ValueError:
                If a version is missing, invalid or does not match
                the configuration folder version.
        """

        expected_version = configuration_directory.name

        for file_name, file_data in configuration_files.items():
            if "configuration_version" not in file_data:
                raise ValueError(
                    f"Missing 'configuration_version' in "
                    f"'{file_name}'."
                )

            file_version = file_data["configuration_version"]

            if not isinstance(file_version, str):
                raise ValueError(
                    f"'configuration_version' in '{file_name}' "
                    f"must be a string."
                )

            if not file_version.strip():
                raise ValueError(
                    f"'configuration_version' in '{file_name}' "
                    f"cannot be empty."
                )

            if file_version != expected_version:
                raise ValueError(
                    f"Configuration version mismatch in "
                    f"'{file_name}'. Expected "
                    f"'{expected_version}', but found "
                    f"'{file_version}'."
                )

    @staticmethod
    def _validate_required_keys(
        file_name: str,
        file_data: dict[str, Any],
        required_keys: list[str]
    ) -> None:
        """
        Confirms that a configuration file contains all required
        top-level keys.

        Args:
            file_name:
                Name of the configuration file being validated.

            file_data:
                Loaded configuration data.

            required_keys:
                Names of the required top-level keys.

        Raises:
            ValueError:
                If one or more required keys are missing.
        """

        missing_keys = [
            key
            for key in required_keys
            if key not in file_data
        ]

        if missing_keys:
            missing_key_list = ", ".join(
                f"'{key}'"
                for key in missing_keys
            )

            raise ValueError(
                f"Missing required key(s) in '{file_name}': "
                f"{missing_key_list}."
            )

    @staticmethod
    def _load_json_file(file_path: Path) -> dict[str, Any]:
        """
        Reads one JSON file and returns its contents as a dictionary.

        Args:
            file_path:
                Path to the JSON file.

        Returns:
            Parsed JSON content.

        Raises:
            ValueError:
                If the file contains invalid JSON or its root value
                is not a JSON object.
        """

        try:
            with file_path.open(
                mode="r",
                encoding="utf-8"
            ) as file:
                file_data = json.load(file)

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid JSON in configuration file "
                f"'{file_path.name}'. "
                f"Line {error.lineno}, "
                f"column {error.colno}: "
                f"{error.msg}"
            ) from error

        if not isinstance(file_data, dict):
            raise ValueError(
                f"Configuration file '{file_path.name}' "
                f"must contain a JSON object at its root."
            )

        return file_data