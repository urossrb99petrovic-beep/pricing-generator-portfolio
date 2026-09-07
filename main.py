import sys
from pathlib import Path


from app.services.configuration_service import ConfigurationService
from app.utils.path_resolver import PathResolver
from app.models.application_config import ApplicationConfig

from app.services.logging_service import LoggingService


CONFIGURATION_VERSION = "1.3.1"

def get_project_root() -> Path:
    """
    Returns the Pricing Generator project root.

    Source execution uses the folder containing main.py.

    When running as a packaged executable, the executable is
    placed directly in the project root beside the USD, EUR and
    BRL folders.
    """

    if getattr(
        sys,
        "frozen",
        False
    ):
        return Path(
            sys.executable
        ).resolve().parent

    application_root = (
        Path(__file__).resolve().parent
    )

    return application_root

def start_application(
    project_root: Path | None = None,
    configuration_version: str = CONFIGURATION_VERSION
) -> tuple[ApplicationConfig, PathResolver, LoggingService]:
    """
    Initializes the Pricing Generator application.

    Args:
        project_root:
            Root directory of the project. If None, the project
            root is detected automatically.

        configuration_version:
            Configuration version to load.

    Returns:
        Loaded application configuration.
    """

    if project_root is None:
        project_root = get_project_root()

    path_resolver = PathResolver(
        project_root=project_root
    )

    configuration_directory = (
        path_resolver.get_configuration_directory(
            configuration_version
        )
    )

    configuration_service = ConfigurationService()

    application_config = (
        configuration_service.load_configuration(
            configuration_directory
        )
    )

    logging_service = LoggingService(
        project_root=project_root,
        logging_config=(
            application_config.settings[
                "logging"
            ]
        ),
        application_version=(
            application_config.settings[
                "application_version"
            ]
        )
    )

    return application_config, path_resolver, logging_service


def main() -> int:
    """
    Starts the Pricing Generator application.

    Returns:
        Process exit code.
    """

    import customtkinter as ctk
    from app.ui.main_window import MainWindow

    try:
        application_config, path_resolver, logging_service = (
            start_application()
        )
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        window = MainWindow(
            application_config=application_config,
            path_resolver=path_resolver,
            logging_service=logging_service
        )
        
        window.mainloop()

    except (
        FileNotFoundError,
        NotADirectoryError,
        ValueError
    ) as error:

        print(
            "Pricing Generator could not start.",
            file=sys.stderr
        )

        print(
            f"Reason: {error}",
            file=sys.stderr
        )

        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())