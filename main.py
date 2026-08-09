import sys
from pathlib import Path

import customtkinter as ctk

from app.models.application_config import ApplicationConfig
from app.services.configuration_service import ConfigurationService
from app.services.logging_service import LoggingService
from app.ui.main_window import MainWindow
from app.utils.path_resolver import PathResolver


CONFIGURATION_VERSION = "1.0.0"


def start_application(
    project_root: Path | None = None,
    configuration_version: str = CONFIGURATION_VERSION,
) -> tuple[ApplicationConfig, PathResolver, LoggingService]:
    """Load configuration and initialize the application's shared services."""
    project_root = project_root or Path(__file__).resolve().parent
    path_resolver = PathResolver(project_root=project_root)
    configuration_directory = path_resolver.get_configuration_directory(
        configuration_version
    )
    application_config = ConfigurationService().load_configuration(
        configuration_directory
    )
    logging_service = LoggingService(
        project_root=project_root,
        logging_config=application_config.settings["logging"],
        application_version=application_config.settings["application_version"],
    )
    return application_config, path_resolver, logging_service


def main() -> int:
    try:
        application_config, path_resolver, logging_service = start_application()
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        window = MainWindow(
            application_config=application_config,
            path_resolver=path_resolver,
            logging_service=logging_service,
        )
        window.mainloop()
    except (FileNotFoundError, NotADirectoryError, ValueError) as error:
        print(f"Pricing Generator could not start. Reason: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
