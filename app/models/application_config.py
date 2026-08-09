from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApplicationConfig:
    """
    Holds all configuration data used by the Pricing Generator.

    Each attribute contains the parsed content of one JSON configuration file.
    """

    settings: dict[str, Any]
    products: dict[str, Any]
    countries: dict[str, Any]
    schemas: dict[str, Any]

    @property
    def configuration_version(self) -> str:
        """
        Returns the configuration version from settings.json.
        """

        return str(self.settings["configuration_version"])