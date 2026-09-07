from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from app.ui.widgets import LocalCountrySelector


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
            [
                str | None,
                dict[str, str],
                list[str],
                dict[str, str],
                list[str]
            ],
            None
        ],
        selected_pricing_type: str | None = None,
        selected_sender_ids: dict[str, str] | None = None,
        selected_local_countries: list[str] | None = None,
        selected_product_options: dict[str, str] | None = None,
        selected_subproducts: list[str] | None = None
    ) -> None:
        """
        Creates the product-options page.

        available_local_countries:
            Local countries available for the selected product.

        selected_local_countries:
            Previously selected local-country overrides.

        selected_product_options:
            Previously selected generic product options.

        selected_subproducts:
            Previously selected subproducts for products such
            as Phone ID Suite.
        """

        super().__init__(
            master=parent,
            corner_radius=0
        )

        self._product_config = product_config
        self._sender_overrides = sender_overrides
        self._on_generate = on_generate

        # ==================================================
        # PRICING TYPE
        # ==================================================

        self._pricing_type_variable = ctk.StringVar(
            value=selected_pricing_type or ""
        )

        # ==================================================
        # SENDER OPTIONS
        # ==================================================

        self._sender_variables: dict[
            str,
            ctk.StringVar
        ] = {}

        self._selected_sender_ids = (
            selected_sender_ids or {}
        )

        # ==================================================
        # GENERIC CHOICE OPTIONS
        # ==================================================

        self._choice_variables: dict[
            str,
            ctk.StringVar
        ] = {}

        self._selected_product_options = (
            selected_product_options or {}
        )

        # ==================================================
        # LOCAL COUNTRIES
        # ==================================================

        self._available_local_countries = (
            available_local_countries
        )

        self._selected_local_countries = (
            selected_local_countries or []
        )

        self._local_country_selector: (
            LocalCountrySelector | None
        ) = None

        # ==================================================
        # SUBPRODUCTS
        #
        # Used by Phone ID Suite.
        # ==================================================

        self._subproduct_variables: dict[
            str,
            ctk.BooleanVar
        ] = {}

        configured_subproducts = (
            self._product_config.get(
                "subproducts",
                []
            )
        )

        # If MainWindow supplied previous selections,
        # preserve them.
        #
        # Otherwise initialize from configuration defaults.
        if selected_subproducts is not None:
            initial_subproducts = list(
                selected_subproducts
            )

        else:
            initial_subproducts = [
                subproduct[
                    "product_id"
                ]
                for subproduct
                in configured_subproducts
                if (
                    subproduct.get(
                        "default_selected",
                        False
                    )
                    or subproduct.get(
                        "required",
                        False
                    )
                )
            ]

        # Required products must always be selected.
        #
        # For Phone ID Suite this guarantees:
        #
        #     PHONE_ID_STANDARD
        #
        # even if incorrect state was somehow supplied
        # by the previous screen.
        for subproduct in configured_subproducts:

            if not subproduct.get(
                "required",
                False
            ):
                continue

            required_id = (
                subproduct[
                    "product_id"
                ]
            )

            if (
                required_id
                not in initial_subproducts
            ):
                initial_subproducts.append(
                    required_id
                )

        self._selected_subproducts = (
            initial_subproducts
        )

        # ==================================================
        # BUILD PAGE
        # ==================================================

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

    def _configure_grid(
        self
    ) -> None:
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
            text=(
                f"Step 2 of 2 — "
                f"{product_name}"
            ),
            font=ctk.CTkFont(
                size=14
            )
        )

        step_label.grid(
            row=1,
            column=0,
            pady=(0, 20)
        )

    def _create_options_content(
        self
    ) -> None:
        """
        Creates all options required by the selected product.

        If the selected product has no configurable options,
        a simple informational message is displayed instead
        of leaving the options area empty.
        """

        self._options_frame = (
            ctk.CTkScrollableFrame(
                master=self,
                width=500
            )
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

        next_row = 0

        # ==================================================
        # DETERMINE AVAILABLE OPTIONS
        # ==================================================

        supported_pricing_types = (
            self._product_config.get(
                "supported_pricing_types",
                []
            )
        )

        choice_options = (
            self._product_config.get(
                "choice_options",
                []
            )
        )

        subproducts = (
            self._product_config.get(
                "subproducts",
                []
            )
        )

        sender_options_enabled = (
            self._product_config[
                "sender_options"
            ][
                "enabled"
            ]
        )

        local_options_enabled = (
            self._product_config[
                "local_options"
            ][
                "enabled"
            ]
        )

        # ==================================================
        # NO OPTIONS REQUIRED
        # ==================================================

        has_configurable_options = (
            bool(
                supported_pricing_types
            )
            or bool(
                choice_options
            )
            or bool(
                subproducts
            )
            or sender_options_enabled
            or local_options_enabled
        )

        if not has_configurable_options:
            self._create_no_options_message()

            return

        # ==================================================
        # PRICING TYPE
        # ==================================================

        if supported_pricing_types:
            next_row = (
                self._create_pricing_type_section(
                    start_row=next_row
                )
            )

        # ==================================================
        # GENERIC CHOICE OPTIONS
        # ==================================================

        if choice_options:
            next_row = (
                self._create_choice_option_sections(
                    start_row=next_row
                )
            )

        # ==================================================
        # SUBPRODUCTS
        # ==================================================

        if subproducts:
            next_row = (
                self._create_subproduct_section(
                    start_row=next_row
                )
            )

        # ==================================================
        # SENDER OPTIONS
        # ==================================================

        if sender_options_enabled:
            next_row = (
                self._create_sender_sections(
                    start_row=next_row
                )
            )

        # ==================================================
        # LOCAL COUNTRY OPTIONS
        # ==================================================

        if local_options_enabled:
            self._create_local_country_section(
                start_row=next_row
            )

    def _create_no_options_message(
        self
    ) -> None:
        """
        Displays guidance when the selected product does not
        require any additional configuration.
        """

        message_label = ctk.CTkLabel(
            master=self._options_frame,
            text=(
                "No additional options required.\n\n"
                "Click Generate to create the pricing file."
            ),
            font=ctk.CTkFont(
                size=16
            ),
            justify="center"
        )

        message_label.grid(
            row=0,
            column=0,
            padx=30,
            pady=(80, 30),
            sticky="ew"
        )

    def _create_pricing_type_section(
        self,
        start_row: int
    ) -> int:
        """
        Creates the Pricing Type controls.

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

        current_row = (
            start_row + 1
        )

        for pricing_type in (
            self._product_config[
                "supported_pricing_types"
            ]
        ):
            pricing_type_button = (
                ctk.CTkRadioButton(
                    master=self._options_frame,
                    text=pricing_type,
                    variable=(
                        self._pricing_type_variable
                    ),
                    value=pricing_type,
                    command=(
                        self
                        ._update_generate_button_state
                    )
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

    def _create_choice_option_sections(
        self,
        start_row: int
    ) -> int:
        """
        Creates generic product-specific option controls.

        The controls are defined by the product's
        choice_options configuration.
        """

        current_row = (
            start_row
        )

        choice_options = (
            self._product_config.get(
                "choice_options",
                []
            )
        )

        for option_config in (
            choice_options
        ):
            option_id = (
                option_config[
                    "option_id"
                ]
            )

            option_label = ctk.CTkLabel(
                master=self._options_frame,
                text=(
                    option_config[
                        "display_name"
                    ]
                ),
                anchor="w",
                font=ctk.CTkFont(
                    size=15,
                    weight="bold"
                )
            )

            option_label.grid(
                row=current_row,
                column=0,
                padx=25,
                pady=(22, 10),
                sticky="ew"
            )

            current_row += 1

            selected_value = (
                self._selected_product_options.get(
                    option_id,
                    ""
                )
            )

            option_variable = (
                ctk.StringVar(
                    value=selected_value
                )
            )

            self._choice_variables[
                option_id
            ] = option_variable

            for value_config in (
                option_config[
                    "values"
                ]
            ):
                option_button = (
                    ctk.CTkRadioButton(
                        master=self._options_frame,
                        text=(
                            value_config[
                                "display_name"
                            ]
                        ),
                        variable=(
                            option_variable
                        ),
                        value=(
                            value_config[
                                "value_id"
                            ]
                        ),
                        command=(
                            self
                            ._update_generate_button_state
                        )
                    )
                )

                option_button.grid(
                    row=current_row,
                    column=0,
                    padx=25,
                    pady=6,
                    sticky="w"
                )

                current_row += 1

        return current_row

    def _create_subproduct_section(
        self,
        start_row: int
    ) -> int:
        """
        Creates selectable product controls for products
        containing configurable subproducts.

        Phone ID Suite uses this section.

        Required non-selectable products such as
        Phone ID Standard are displayed checked and locked.
        """

        section_label = ctk.CTkLabel(
            master=self._options_frame,
            text="Products",
            anchor="w",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        section_label.grid(
            row=start_row,
            column=0,
            padx=25,
            pady=(20, 10),
            sticky="ew"
        )

        current_row = (
            start_row + 1
        )

        configured_subproducts = (
            self._product_config.get(
                "subproducts",
                []
            )
        )

        configured_subproducts = sorted(
            configured_subproducts,
            key=lambda subproduct: (
                subproduct.get(
                    "display_order",
                    9999
                )
            )
        )

        for subproduct in (
            configured_subproducts
        ):
            subproduct_id = (
                subproduct[
                    "product_id"
                ]
            )

            is_required = (
                subproduct.get(
                    "required",
                    False
                )
            )

            user_selectable = (
                subproduct.get(
                    "user_selectable",
                    True
                )
            )

            is_selected = (
                subproduct_id
                in self._selected_subproducts
            )

            # A required product must always be selected.
            if is_required:
                is_selected = True

            variable = ctk.BooleanVar(
                value=is_selected
            )

            self._subproduct_variables[
                subproduct_id
            ] = variable

            checkbox = ctk.CTkCheckBox(
                master=self._options_frame,
                text=(
                    subproduct[
                        "display_name"
                    ]
                ),
                variable=variable,
                onvalue=True,
                offvalue=False,
                command=(
                    self
                    ._update_generate_button_state
                ),
                state=(
                    "normal"
                    if user_selectable
                    else "disabled"
                )
            )

            checkbox.grid(
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

        current_row = (
            start_row
        )

        supported_countries = (
            self._product_config[
                "sender_options"
            ][
                "supported_countries"
            ]
        )

        configured_countries = (
            self._sender_overrides[
                "countries"
            ]
        )

        for country_code in (
            supported_countries
        ):
            country_config = (
                configured_countries[
                    country_code
                ]
            )

            section_label = (
                ctk.CTkLabel(
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
            )

            section_label.grid(
                row=current_row,
                column=0,
                padx=25,
                pady=(22, 10),
                sticky="ew"
            )

            current_row += 1

            default_sender_id = (
                country_config[
                    "default_sender_id"
                ]
            )

            selected_sender_id = (
                self._selected_sender_ids.get(
                    country_code,
                    default_sender_id
                )
            )

            sender_variable = (
                ctk.StringVar(
                    value=selected_sender_id
                )
            )

            self._sender_variables[
                country_code
            ] = sender_variable

            for (
                sender_id,
                sender_config
            ) in (
                country_config[
                    "sender_ids"
                ].items()
            ):
                sender_button = (
                    ctk.CTkRadioButton(
                        master=self._options_frame,
                        text=(
                            sender_config[
                                "display_name"
                            ]
                        ),
                        variable=(
                            sender_variable
                        ),
                        value=sender_id
                    )
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

        if (
            self._local_country_selector
            is None
        ):
            return []

        return (
            self._local_country_selector
            .get_selected_countries()
        )

    def _get_selected_product_options(
        self
    ) -> dict[str, str]:
        """
        Returns current generic product-option selections.
        """

        return {
            option_id: variable.get()
            for option_id, variable
            in self._choice_variables.items()
            if variable.get()
        }

    def _get_selected_subproducts(
        self
    ) -> list[str]:
        """
        Returns selected subproduct IDs in configured
        display order.

        For Phone ID Suite this always includes
        PHONE_ID_STANDARD.
        """

        selected_subproducts = []

        configured_subproducts = (
            self._product_config.get(
                "subproducts",
                []
            )
        )

        configured_subproducts = sorted(
            configured_subproducts,
            key=lambda subproduct: (
                subproduct.get(
                    "display_order",
                    9999
                )
            )
        )

        for subproduct in (
            configured_subproducts
        ):
            subproduct_id = (
                subproduct[
                    "product_id"
                ]
            )

            variable = (
                self._subproduct_variables.get(
                    subproduct_id
                )
            )

            if (
                variable is not None
                and variable.get()
            ):
                selected_subproducts.append(
                    subproduct_id
                )

        return selected_subproducts

    def _all_required_choice_options_selected(
        self
    ) -> bool:
        """
        Returns True when every required generic option
        has a selected value.
        """

        choice_options = (
            self._product_config.get(
                "choice_options",
                []
            )
        )

        for option_config in (
            choice_options
        ):
            if not option_config.get(
                "required",
                False
            ):
                continue

            option_id = (
                option_config[
                    "option_id"
                ]
            )

            variable = (
                self._choice_variables.get(
                    option_id
                )
            )

            if (
                variable is None
                or not variable.get()
            ):
                return False

        return True

    def _all_required_subproducts_selected(
        self
    ) -> bool:
        """
        Returns True when every required configured
        subproduct is selected.

        Phone ID Standard is currently the main use case.
        """

        configured_subproducts = (
            self._product_config.get(
                "subproducts",
                []
            )
        )

        for subproduct in (
            configured_subproducts
        ):
            if not subproduct.get(
                "required",
                False
            ):
                continue

            subproduct_id = (
                subproduct[
                    "product_id"
                ]
            )

            variable = (
                self._subproduct_variables.get(
                    subproduct_id
                )
            )

            if (
                variable is None
                or not variable.get()
            ):
                return False

        return True

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

        cancel_button = (
            ctk.CTkButton(
                master=button_frame,
                text="Cancel",
                command=on_cancel,
                fg_color="transparent",
                border_width=1
            )
        )

        cancel_button.grid(
            row=0,
            column=2,
            padx=(0, 12)
        )

        self._generate_button = (
            ctk.CTkButton(
                master=button_frame,
                text="Generate",
                command=(
                    self._handle_generate
                ),
                state="disabled"
            )
        )

        self._generate_button.grid(
            row=0,
            column=3
        )

    def _update_generate_button_state(
        self
    ) -> None:
        """
        Enables Generate when all currently required
        selections are complete.
        """

        # ==================================================
        # PRICING TYPE
        # ==================================================

        supported_pricing_types = (
            self._product_config.get(
                "supported_pricing_types",
                []
            )
        )

        pricing_type_is_valid = (
            not supported_pricing_types
            or bool(
                self._pricing_type_variable
                .get()
                .strip()
            )
        )

        # ==================================================
        # GENERIC REQUIRED OPTIONS
        # ==================================================

        choice_options_are_valid = (
            self
            ._all_required_choice_options_selected()
        )

        # ==================================================
        # REQUIRED SUBPRODUCTS
        # ==================================================

        subproducts_are_valid = (
            self
            ._all_required_subproducts_selected()
        )

        # ==================================================
        # FINAL BUTTON STATE
        # ==================================================

        can_generate = (
            pricing_type_is_valid
            and choice_options_are_valid
            and subproducts_are_valid
        )

        self._generate_button.configure(
            state=(
                "normal"
                if can_generate
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

    def _handle_generate(
        self
    ) -> None:
        """
        Sends all Step 2 selections to MainWindow.
        """

        pricing_type_value = (
            self._pricing_type_variable
            .get()
            .strip()
        )

        pricing_type = (
            pricing_type_value
            if pricing_type_value
            else None
        )

        self._on_generate(
            pricing_type,
            self._get_selected_sender_ids(),
            self._get_selected_local_countries(),
            self._get_selected_product_options(),
            self._get_selected_subproducts()
        )

    def set_generation_in_progress(
        self,
        is_in_progress: bool
    ) -> None:
        """
        Updates the Generate button while generation is running.

        Args:
            is_in_progress:
                True while generation is running;
                otherwise False.
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