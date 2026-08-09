import re
from pathlib import Path


class PathResolver:
    """
    Converts configured path patterns into real filesystem paths.
    """

    PROJECT_ROOT_PLACEHOLDER = "{project_root}"
    CURRENCY_PLACEHOLDER = "{currency}"
    USER_DOWNLOADS_VALUE = "USER_DOWNLOADS"

    PLACEHOLDER_PATTERN = r"\{[^{}]+\}"

    def __init__(
        self,
        project_root: Path
    ) -> None:
        """
        Creates a PathResolver.

        Args:
            project_root:
                Root folder of the Pricing Generator project.

        Raises:
            FileNotFoundError:
                If the project root does not exist.

            NotADirectoryError:
                If the project root is not a directory.
        """

        self._validate_project_root(project_root)

        self._project_root = project_root.resolve()

    @property
    def project_root(self) -> Path:
        """
        Returns the absolute project-root path.
        """

        return self._project_root

    def resolve_path(
        self,
        path_pattern: str,
        currency: str | None = None
    ) -> Path:
        """
        Converts a configured path pattern into a real path.

        Args:
            path_pattern:
                Configured path containing supported placeholders
                or a supported special path value.

            currency:
                Currency used to replace the {currency} placeholder.

        Returns:
            Resolved filesystem path.

        Raises:
            ValueError:
                If the path pattern is empty, requires a missing
                currency or contains an unsupported placeholder.
        """

        self._validate_path_pattern(path_pattern)

        if path_pattern == self.USER_DOWNLOADS_VALUE:
            return Path.home() / "Downloads"

        resolved_path = path_pattern.replace(
            self.PROJECT_ROOT_PLACEHOLDER,
            str(self._project_root)
        )

        if self.CURRENCY_PLACEHOLDER in resolved_path:
            if currency is None:
                raise ValueError(
                    "Currency is required to resolve a path "
                    "containing '{currency}'."
                )

            resolved_path = resolved_path.replace(
                self.CURRENCY_PLACEHOLDER,
                currency
            )

        self._validate_resolved_path(resolved_path)

        return Path(resolved_path)

    @staticmethod
    def _validate_project_root(
        project_root: Path
    ) -> None:
        """
        Confirms that the project root exists and is a directory.
        """

        if not project_root.exists():
            raise FileNotFoundError(
                f"Project root does not exist: {project_root}"
            )

        if not project_root.is_dir():
            raise NotADirectoryError(
                f"Project root is not a directory: {project_root}"
            )

    @staticmethod
    def _validate_path_pattern(
        path_pattern: str
    ) -> None:
        """
        Confirms that the configured path pattern is not empty.

        Args:
            path_pattern:
                Configured path to validate.

        Raises:
            ValueError:
                If the path pattern is empty or contains only
                whitespace.
        """

        if not path_pattern.strip():
            raise ValueError(
                "Path pattern cannot be empty."
            )

    def get_configuration_directory(
        self,
        configuration_version: str
    ) -> Path:
        """
        Returns the configuration directory for a specific version.

        Args:
            configuration_version:
                Configuration version folder name.

        Returns:
            Resolved configuration directory.

        Raises:
            ValueError:
                If the configuration version is empty.
        """

        if not configuration_version.strip():
            raise ValueError(
                "Configuration version cannot be empty."
            )

        return self.resolve_path(
            (
                "{project_root}/Administration/"
                f"Configuration/{configuration_version}"
            )
        )

    def get_pricing_workbook_path(
        self,
        folder_pattern: str,
        filename: str,
        currency: str
    ) -> Path:
        """
        Returns the pricing workbook path for the selected currency.

        Args:
            folder_pattern:
                Configured folder pattern for pricing workbooks.

            filename:
                Pricing workbook filename.

            currency:
                Selected pricing currency.

        Returns:
            Resolved pricing workbook path.

        Raises:
            ValueError:
                If filename or currency is empty.
        """

        if not filename.strip():
            raise ValueError(
                "Pricing workbook filename cannot be empty."
            )

        if not currency.strip():
            raise ValueError(
                "Currency cannot be empty."
            )

        workbook_directory = self.resolve_path(
            folder_pattern,
            currency=currency
        )

        return workbook_directory / filename

    @classmethod
    def _validate_resolved_path(
        cls,
        resolved_path: str
    ) -> None:
        """
        Confirms that no unsupported placeholders remain after
        path resolution.

        Args:
            resolved_path:
                Path text after supported placeholders have been
                replaced.

        Raises:
            ValueError:
                If one or more unresolved placeholders remain.
        """

        unresolved_placeholders = re.findall(
            cls.PLACEHOLDER_PATTERN,
            resolved_path
        )

        if unresolved_placeholders:
            placeholder_list = ", ".join(
                f"'{placeholder}'"
                for placeholder in unresolved_placeholders
            )

            raise ValueError(
                "Unsupported or unresolved path placeholder(s): "
                f"{placeholder_list}."
            )