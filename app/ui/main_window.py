from typing import Any

import customtkinter as ctk

from app.models.application_config import ApplicationConfig
from app.ui.home_frame import HomeFrame
from app.ui.options_frame import OptionsFrame
from app.services.workbook_service import WorkbookService
from app.utils.path_resolver import PathResolver

from tkinter import messagebox

from app.controllers.pricing_generator_controller import (
    PricingGeneratorController
)
from app.models.generation_request import GenerationRequest

from app.utils.file_opener import FileOpener

import sys
from pathlib import Path
from app.services.logging_service import LoggingService


class MainWindow(ctk.CTk):
    """
    Main application window and wizard page manager.
    """

    WINDOW_WIDTH = 760
    WINDOW_HEIGHT = 600

    MINIMUM_WIDTH = 680
    MINIMUM_HEIGHT = 540

    def __init__(
        self,
        application_config: ApplicationConfig,
        path_resolver: PathResolver,
        logging_service: LoggingService
    ) -> None:
        """
        Creates and configures the main application window.

        Args:
            application_config:
                Loaded Pricing Generator configuration.
        """

        super().__init__()

        self._application_config = application_config
        self._path_resolver = path_resolver
        self._controller = PricingGeneratorController(
            application_config=application_config,
            path_resolver=path_resolver,
            logging_service=logging_service
        )

        self._selected_currency: str | None = None
        self._selected_product_name: str | None = None
        self._selected_product: dict[str, Any] | None = None
        self._selected_pricing_type: str | None = None
        self._selected_sender_ids: dict[str, str] = {}
        self._selected_local_countries: list[str] = []
        self._selected_product_options: dict[str, str] = {}
        self._selected_subproducts: list[str] = []
        self._local_country_cache: dict[
            str,
            list[str]
        ] = {}

        self._products_by_display_name = (
            self._build_product_mapping()
        )

        self.title(
            application_config.settings[
                "application_name"
            ]
        )

        self.geometry(
            f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}"
        )

        self.minsize(
            self.MINIMUM_WIDTH,
            self.MINIMUM_HEIGHT
        )

        self.resizable(
            width=True,
            height=True
        )

        self._active_frame: ctk.CTkFrame | None = None
        self._options_frame: OptionsFrame | None = None

        self._configure_window_grid()
        self._create_content_container()
        self._center_window()
        self.title(
            self._application_config.settings[
                "application_name"
            ]
        )

        self._set_window_icon()

        self.show_home()

    def _set_window_icon(self) -> None:
        """
        Sets the Pricing Generator window icon.

        Supports both source execution and the packaged
        PyInstaller executable.
        """

        if getattr(
            sys,
            "frozen",
            False
        ):
            icon_path = (
                Path(sys._MEIPASS)
                / "assets"
                / "pricing_generator.ico"
            )
        else:
            icon_path = (
                Path(__file__).resolve()
                .parent.parent.parent
                / "assets"
                / "pricing_generator.ico"
            )

        if icon_path.exists():
            self.iconbitmap(
                str(icon_path)
            )

    def show_home(self) -> None:
        """
        Displays the first page of the wizard.
        """

        currencies = self._application_config.settings[
            "supported_currencies"
        ]

        product_names = list(
            self._products_by_display_name.keys()
        )

        home_frame = HomeFrame(
            parent=self._content_container,
            currencies=currencies,
            products=product_names,
            on_cancel=self.destroy,
            on_next=self._handle_home_next,
            selected_currency=self._selected_currency,
            selected_product=self._selected_product_name
        )

        self._show_frame(home_frame)

    def show_options(self) -> None:
        """
        Displays the second page of the wizard.
        """

        if (
            self._selected_product is None
            or self._selected_product_name is None
        ):
            raise ValueError(
                "A product must be selected before "
                "opening the options page."
            )

        sender_overrides = (
            self._application_config.countries[
                "sender_overrides"
            ]
        )

        local_options_enabled = (
            self._selected_product[
                "local_options"
            ]["enabled"]
        )

        available_local_countries: list[str] = []

        if local_options_enabled:
            available_local_countries = (
                self._load_available_local_countries()
            )

        self._options_frame = OptionsFrame(
            parent=self._content_container,
            product_name=self._selected_product_name,
            product_config=self._selected_product,
            sender_overrides=sender_overrides,
            available_local_countries=(
                available_local_countries
            ),
            on_back=self.show_home,
            on_cancel=self.destroy,
            on_generate=self._handle_generate,
            selected_pricing_type=(
                self._selected_pricing_type
            ),
            selected_sender_ids=(
                self._selected_sender_ids
            ),
            selected_local_countries=(
                self._selected_local_countries
            ),
            selected_product_options=(
                self._selected_product_options
            ),
            selected_subproducts=(
                self._selected_subproducts
            )
        )

        self._show_frame(self._options_frame)

    def _handle_home_next(
        self,
        currency: str,
        product_name: str
    ) -> None:
        """
        Stores Step 1 selections and opens Step 2.
        """

        product_changed = (
            self._selected_product_name is not None
            and self._selected_product_name != product_name
        )

        self._selected_currency = currency
        self._selected_product_name = product_name

        self._selected_product = (
            self._products_by_display_name[
                product_name
            ]
        )

        if product_changed:
            self._selected_pricing_type = None
            self._selected_sender_ids = {}
            self._selected_local_countries = []
            self._selected_product_options = {}

        self.show_options()

    def _handle_generate(
        self,
        pricing_type: str | None,
        sender_ids: dict[str, str],
        local_countries: list[str],
        product_options: dict[str, str],
        selected_subproducts: list[str]
    ) -> None:
        """
        Generates pricing using the current GUI selections.

        Supports:
            - normal single-file products;
            - Mobile multi-file generation;
            - products with or without Pricing Type;
            - products with selectable subproducts.
        """

        self._selected_pricing_type = pricing_type
        self._selected_sender_ids = sender_ids
        self._selected_local_countries = local_countries
        self._selected_product_options = product_options

        self._selected_subproducts = (
            selected_subproducts
        )

        # ==================================================
        # VALIDATE CURRENT GUI SELECTIONS
        # ==================================================

        if self._selected_currency is None:
            messagebox.showerror(
                title="Generation Error",
                message=(
                    "A currency must be selected before "
                    "generating pricing."
                ),
                parent=self
            )
            return

        if self._selected_product is None:
            messagebox.showerror(
                title="Generation Error",
                message=(
                    "A product must be selected before "
                    "generating pricing."
                ),
                parent=self
            )
            return

        # ==================================================
        # BUILD GENERATION REQUEST
        # ==================================================

        request = GenerationRequest(
            currency=self._selected_currency,
            product_id=self._selected_product[
                "product_id"
            ],
            pricing_type=(
                self._selected_pricing_type
            ),
            sender_ids=(
                self._selected_sender_ids.copy()
            ),
            local_countries=(
                self._selected_local_countries.copy()
            ),
            product_options=(
                self._selected_product_options.copy()
            ),
            selected_subproducts=(
                self._selected_subproducts.copy()
            )
        )

        # ==================================================
        # GENERATION START
        # ==================================================

        if self._options_frame is not None:
            self._options_frame.set_generation_in_progress(
                True
            )

        self.configure(
            cursor="wait"
        )

        self.update_idletasks()

        try:
            result, output = (
                self._controller.generate_pricing(
                    request
                )
            )

        except (
            FileNotFoundError,
            FileExistsError,
            NotADirectoryError,
            PermissionError,
            ValueError,
            RuntimeError
        ) as error:

            messagebox.showerror(
                title="Generation Error",
                message=(
                    "Pricing could not be generated.\n\n"
                    f"Reason:\n{error}"
                ),
                parent=self
            )

            return

        finally:
            self.configure(
                cursor=""
            )

            if self._options_frame is not None:
                self._options_frame.set_generation_in_progress(
                    False
                )

            self.update_idletasks()

        # ==================================================
        # OPTIONAL PRICING TYPE TEXT
        # ==================================================

        pricing_type_text = ""

        if result.pricing_type:
            pricing_type_text = (
                f"Pricing Type: "
                f"{result.pricing_type}\n"
            )

        # ==================================================
        # MULTI-FILE OUTPUT
        # ==================================================

        if isinstance(
            output,
            dict
        ):
            output_paths = output

            generated_files_text = "\n".join(
                f"• {output_path.name}"
                for output_path in (
                    output_paths.values()
                )
            )

            row_counts = (
                result.output_row_counts
            )

            row_counts_text = "\n".join(
                (
                    f"• {output_id}: "
                    f"{row_count} rows"
                )
                for output_id, row_count
                in row_counts.items()
            )

            first_output_path = next(
                iter(
                    output_paths.values()
                )
            )

            messagebox.showinfo(
                title="Generation Successful",
                message=(
                    "Pricing was generated successfully.\n\n"
                    f"Product: "
                    f"{result.product_output_name}\n"
                    f"Currency: "
                    f"{result.currency}\n"
                    f"{pricing_type_text}"
                    f"\n"
                    f"Generated Files:\n"
                    f"{generated_files_text}\n\n"
                    f"Rows Generated:\n"
                    f"{row_counts_text}\n\n"
                    f"Location:\n"
                    f"{first_output_path.parent}"
                ),
                parent=self
            )

            if (
                self._application_config.settings[
                    "behaviour"
                ][
                    "open_output_folder_after_generation"
                ]
            ):
                FileOpener.reveal_file(
                    first_output_path
                )

        # ==================================================
        # NORMAL SINGLE-FILE OUTPUT
        # ==================================================

        else:
            output_path = output

            messagebox.showinfo(
                title="Generation Successful",
                message=(
                    "Pricing was generated successfully.\n\n"
                    f"Product: "
                    f"{result.product_output_name}\n"
                    f"Currency: "
                    f"{result.currency}\n"
                    f"{pricing_type_text}"
                    f"Rows Generated: "
                    f"{len(result.rows)}\n\n"
                    f"Output File:\n"
                    f"{output_path.name}\n\n"
                    f"Location:\n"
                    f"{output_path.parent}"
                ),
                parent=self
            )

            if (
                self._application_config.settings[
                    "behaviour"
                ][
                    "open_output_folder_after_generation"
                ]
            ):
                FileOpener.reveal_file(
                    output_path
                )

        self._reset_after_successful_generation()

    def _build_product_mapping(
        self
    ) -> dict[str, dict[str, Any]]:
        """
        Creates a display-name-to-product mapping.

        Only enabled products are included, ordered according
        to display_order.
        """

        configured_products = (
            self._application_config.products[
                "products"
            ]
        )

        enabled_products = [
            product
            for product in configured_products
            if product["enabled"]
        ]

        enabled_products.sort(
            key=lambda product: product["display_order"]
        )

        return {
            product["display_name"]: product
            for product in enabled_products
        }

    def _show_frame(
        self,
        frame: ctk.CTkFrame
    ) -> None:
        """
        Replaces the currently visible page.
        """

        if self._active_frame is not None:
            self._active_frame.destroy()

        self._active_frame = frame

        self._active_frame.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

    def _configure_window_grid(self) -> None:
        """
        Configures the main window resizing.
        """

        self.grid_rowconfigure(
            0,
            weight=1
        )

        self.grid_columnconfigure(
            0,
            weight=1
        )

    def _create_content_container(self) -> None:
        """
        Creates the active-page container.
        """

        self._content_container = ctk.CTkFrame(
            master=self,
            corner_radius=0
        )

        self._content_container.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self._content_container.grid_rowconfigure(
            0,
            weight=1
        )

        self._content_container.grid_columnconfigure(
            0,
            weight=1
        )

    def _center_window(self) -> None:
        """
        Centers the window on the primary screen.
        """

        self.update_idletasks()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        horizontal_position = (
            screen_width - self.WINDOW_WIDTH
        ) // 2

        vertical_position = (
            screen_height - self.WINDOW_HEIGHT
        ) // 2

        self.geometry(
            (
                f"{self.WINDOW_WIDTH}x"
                f"{self.WINDOW_HEIGHT}+"
                f"{horizontal_position}+"
                f"{vertical_position}"
            )
        )

    def _reset_after_successful_generation(
        self
    ) -> None:
        """
        Clears all user selections after successful generation
        and returns the application to a clean Home page.

        Cached workbook-derived data is deliberately retained
        because it is not a user selection.
        """

        # ==================================================
        # STEP 1 SELECTIONS
        # ==================================================

        self._selected_currency = None
        self._selected_product_name = None
        self._selected_product = None

        # ==================================================
        # STEP 2 SELECTIONS
        # ==================================================

        self._selected_pricing_type = None
        self._selected_sender_ids = {}
        self._selected_local_countries = []
        self._selected_product_options = {}
        self._selected_subproducts = []

        # ==================================================
        # OPTIONS PAGE REFERENCE
        # ==================================================

        self._options_frame = None

        # ==================================================
        # RETURN TO CLEAN HOME PAGE
        # ==================================================

        self.show_home()

    def _load_available_local_countries(
        self
    ) -> list[str]:
        """
        Loads Local Country overrides for the selected currency.

        The country list is cached after the first workbook read so
        repeated navigation does not reopen the same workbook.

        Returns:
            Clean country names from the canonical Local SMS sheet.
        """

        if self._selected_currency is None:
            raise ValueError(
                "A currency must be selected before loading "
                "Local Countries."
            )

        cached_countries = (
            self._local_country_cache.get(
                self._selected_currency
            )
        )

        if cached_countries is not None:
            return cached_countries.copy()

        pricing_workbook_settings = (
            self._application_config.settings[
                "pricing_workbook"
            ]
        )

        workbook_path = (
            self._path_resolver.get_pricing_workbook_path(
                folder_pattern=(
                    pricing_workbook_settings[
                        "folder_pattern"
                    ]
                ),
                filename=(
                    pricing_workbook_settings[
                        "filename"
                    ]
                ),
                currency=self._selected_currency
            )
        )

        local_worksheet_schema = (
            self._application_config.schemas[
                "workbook_schemas"
            ][
                "local_pricing_worksheet"
            ]
        )

        with WorkbookService(
            workbook_path
        ) as workbook_service:
            local_countries = (
                workbook_service.get_local_countries(
                    local_worksheet_schema
                )
            )

        self._local_country_cache[
            self._selected_currency
        ] = local_countries

        return local_countries.copy()