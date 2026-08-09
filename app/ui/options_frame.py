from collections.abc import Callable
from typing import Any
from app.ui.widgets import LocalCountrySelector

import customtkinter as ctk


class OptionsFrame(ctk.CTkFrame):
    """
    Second page of the Pricing Generator wizard.
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
        product_name: str,
        product_config: dict[str, Any],
        sender_overrides: dict[str, Any],
        available_local_countries: list[str],
        on_back: Callable[[], None],
        on_cancel: Callable[[], None],
        on_generate: Callable[
            [str, dict[str, str], list[str]],
            None
        ],
        selected_pricing_type: str | None = None,
        selected_sender_ids: dict[str, str] | None = None,
        selected_local_countries: list[str] |None = None
    ) -> None:
        """
        Creates the product-options page.

        available_local_countries:
            Local countries available for the selected product.

        selected_local_countries:
            Previously selected local-country overrides.
        """
        

        super().__init__(
            master=parent,
            corner_radius=0
        )

        self._product_config = product_config
        self._sender_overrides = sender_overrides
        self._on_generate = on_generate

        self._pricing_type_variable = ctk.StringVar(
            value=selected_pricing_type or ""
        )

        self._sender_variables: dict[
            str,
            ctk.StringVar
        ] = {}

        self._selected_sender_ids = (
            selected_sender_ids or {}
        )

        self._available_local_countries = (
            available_local_countries
        )

        self._selected_local_countries = (
            selected_local_countries or []
        )

        self._local_country_selector: (
            LocalCountrySelector | None
        ) = None

        self._configure_grid()

        self._create_header(
            product_name=product_name
        )

        self._create_options_content()

        self._create_buttons(
            on_back=on_back,
            on_cancel=on_cancel
        )

        self._update_generate_button_state()

    def _configure_grid(self) -> None:
        """
        Configures the page layout.
        """

        self.grid_columnconfigure(
            0,
            weight=1
        )

        self.grid_rowconfigure(
            2,
            weight=1
        )

    def _create_header(
        self,
        product_name: str
    ) -> None:
        """
        Creates the title and selected-product label.
        """

        title_label = ctk.CTkLabel(
            master=self,
            text="Pricing Generator",
            font=ctk.CTkFont(
                size=28,
                weight="bold"
            )
        )

        title_label.grid(
            row=0,
            column=0,
            pady=(35, 5)
        )

        step_label = ctk.CTkLabel(
            master=self,
            text=f"Step 2 of 2 — {product_name}",
            font=ctk.CTkFont(
                size=14
            )
        )

        step_label.grid(
            row=1,
            column=0,
            pady=(0, 20)
        )

    def _create_options_content(self) -> None:
        """
        Creates all options required by the selected product.
        """

        self._options_frame = ctk.CTkScrollableFrame(
            master=self,
            width=500
        )

        self._options_frame.grid(
            row=2,
            column=0,
            padx=40,
            pady=10,
            sticky="nsew"
        )

        self._options_frame.grid_columnconfigure(
            0,
            weight=1
        )

        next_row = self._create_pricing_type_section(
            start_row=0
        )

        sender_options_enabled = (
            self._product_config[
                "sender_options"
            ]["enabled"]
        )

        if sender_options_enabled:
            next_row = self._create_sender_sections(
                start_row=next_row
            )

        local_options_enabled = (
            self._product_config[
                "local_options"
            ]["enabled"]
        )

        if local_options_enabled:
            self._create_local_country_section(
                start_row=next_row
            )

    def _create_pricing_type_section(
        self,
        start_row: int
    ) -> int:
        """
        Creates the mandatory Pricing Type controls.

        Returns:
            Next available grid row.
        """

        pricing_type_label = ctk.CTkLabel(
            master=self._options_frame,
            text="Pricing Type",
            anchor="w",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        pricing_type_label.grid(
            row=start_row,
            column=0,
            padx=25,
            pady=(20, 10),
            sticky="ew"
        )

        current_row = start_row + 1

        for pricing_type in self._product_config[
            "supported_pricing_types"
        ]:
            pricing_type_button = ctk.CTkRadioButton(
                master=self._options_frame,
                text=pricing_type,
                variable=self._pricing_type_variable,
                value=pricing_type,
                command=(
                    self._update_generate_button_state
                )
            )

            pricing_type_button.grid(
                row=current_row,
                column=0,
                padx=25,
                pady=6,
                sticky="w"
            )

            current_row += 1

        return current_row

    def _create_sender_sections(
        self,
        start_row: int
    ) -> int:
        """
        Creates sender-ID controls for supported countries.
        """

        current_row = start_row

        supported_countries = (
            self._product_config[
                "sender_options"
            ]["supported_countries"]
        )

        configured_countries = (
            self._sender_overrides["countries"]
        )

        for country_code in supported_countries:
            country_config = configured_countries[
                country_code
            ]

            section_label = ctk.CTkLabel(
                master=self._options_frame,
                text=(
                    f"{country_config['country_name']} "
                    f"Sender ID"
                ),
                anchor="w",
                font=ctk.CTkFont(
                    size=15,
                    weight="bold"
                )
            )

            section_label.grid(
                row=current_row,
                column=0,
                padx=25,
                pady=(22, 10),
                sticky="ew"
            )

            current_row += 1

            default_sender_id = country_config[
                "default_sender_id"
            ]

            selected_sender_id = (
                self._selected_sender_ids.get(
                    country_code,
                    default_sender_id
                )
            )

            sender_variable = ctk.StringVar(
                value=selected_sender_id
            )

            self._sender_variables[
                country_code
            ] = sender_variable

            for sender_id, sender_config in (
                country_config[
                    "sender_ids"
                ].items()
            ):
                sender_button = ctk.CTkRadioButton(
                    master=self._options_frame,
                    text=sender_config[
                        "display_name"
                    ],
                    variable=sender_variable,
                    value=sender_id
                )

                sender_button.grid(
                    row=current_row,
                    column=0,
                    padx=25,
                    pady=6,
                    sticky="w"
                )

                current_row += 1

        return current_row

    def _create_local_country_section(
        self,
        start_row: int
    ) -> None:
        """
        Creates the optional Local Country override selector.
        """

        self._local_country_selector = (
            LocalCountrySelector(
                parent=self._options_frame,
                available_countries=(
                    self._available_local_countries
                ),
                selected_countries=(
                    self._selected_local_countries
                )
            )
        )

        self._local_country_selector.grid(
            row=start_row,
            column=0,
            padx=25,
            pady=(25, 20),
            sticky="nsew"
        )

    def _get_selected_local_countries(
        self
    ) -> list[str]:
        """
        Returns the currently selected Local Country overrides.
        """

        if self._local_country_selector is None:
            return []

        return (
            self._local_country_selector
            .get_selected_countries()
        )

    def _create_buttons(
        self,
        on_back: Callable[[], None],
        on_cancel: Callable[[], None]
    ) -> None:
        """
        Creates Back, Cancel and Generate buttons.
        """

        button_frame = ctk.CTkFrame(
            master=self,
            fg_color="transparent"
        )

        button_frame.grid(
            row=3,
            column=0,
            padx=40,
            pady=(15, 30),
            sticky="ew"
        )

        button_frame.grid_columnconfigure(
            1,
            weight=1
        )

        back_button = ctk.CTkButton(
            master=button_frame,
            text="< Back",
            command=on_back,
            fg_color="transparent",
            border_width=1
        )

        back_button.grid(
            row=0,
            column=0
        )

        cancel_button = ctk.CTkButton(
            master=button_frame,
            text="Cancel",
            command=on_cancel,
            fg_color="transparent",
            border_width=1
        )

        cancel_button.grid(
            row=0,
            column=2,
            padx=(0, 12)
        )

        self._generate_button = ctk.CTkButton(
            master=button_frame,
            text="Generate",
            command=self._handle_generate,
            state="disabled"
        )

        self._generate_button.grid(
            row=0,
            column=3
        )

    def _update_generate_button_state(self) -> None:
        """
        Enables Generate once Pricing Type is selected.
        """

        pricing_type_selected = bool(
            self._pricing_type_variable.get()
        )

        self._generate_button.configure(
            state=(
                "normal"
                if pricing_type_selected
                else "disabled"
            )
        )

    def _get_selected_sender_ids(
        self
    ) -> dict[str, str]:
        """
        Returns current sender selections by country.
        """

        return {
            country_code: variable.get()
            for country_code, variable
            in self._sender_variables.items()
        }

    def _handle_generate(self) -> None:
        """
        Sends all Step 2 selections to MainWindow.
        """

        self._on_generate(
            self._pricing_type_variable.get(),
            self._get_selected_sender_ids(),
            self._get_selected_local_countries()
        )

    def set_generation_in_progress(
        self,
        is_in_progress: bool
    ) -> None:
        """
        Updates the Generate button while generation is running.

        Args:
            is_in_progress:
                True while generation is running; otherwise False.
        """

        if is_in_progress:
            self._generate_button.configure(
                state="disabled",
                text="Generating..."
            )
            return

        self._generate_button.configure(
            text="Generate"
        )

        self._update_generate_button_state()