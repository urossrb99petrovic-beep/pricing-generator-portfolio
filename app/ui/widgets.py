from collections.abc import Callable

import customtkinter as ctk


class LocalCountrySelector(ctk.CTkFrame):
    """
    Searchable multi-select control for local-country overrides.
    """

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        available_countries: list[str],
        selected_countries: list[str] | None = None,
        on_selection_change: Callable[[list[str]], None] | None = None
    ) -> None:
        """
        Creates the local-country selector.

        Args:
            parent:
                Container in which the selector is displayed.

            available_countries:
                Countries that may be selected.

            selected_countries:
                Previously selected countries.

            on_selection_change:
                Optional function called whenever the selection
                changes.
        """

        super().__init__(
            master=parent,
            fg_color="transparent"
        )

        self._available_countries = available_countries
        self._selected_countries = set(
            selected_countries or []
        )
        self._on_selection_change = on_selection_change

        self._country_variables: dict[
            str,
            ctk.BooleanVar
        ] = {}

        self._country_checkboxes: dict[
            str,
            ctk.CTkCheckBox
        ] = {}

        self._search_variable = ctk.StringVar(
            value=""
        )

        self._configure_grid()
        self._create_header()
        self._create_search_box()
        self._create_country_list()
        self._create_selection_summary()

    def get_selected_countries(self) -> list[str]:
        """
        Returns selected countries in their original workbook
        order.
        """

        return [
            country
            for country in self._available_countries
            if self._country_variables[
                country
            ].get()
        ]

    def _configure_grid(self) -> None:
        """
        Configures the selector layout.
        """

        self.grid_columnconfigure(
            0,
            weight=1
        )

        self.grid_rowconfigure(
            2,
            weight=1
        )

    def _create_header(self) -> None:
        """
        Creates the section heading and optional indicator.
        """

        heading_label = ctk.CTkLabel(
            master=self,
            text="Local Country Overrides",
            anchor="w",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        heading_label.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        optional_label = ctk.CTkLabel(
            master=self,
            text="Optional — select zero, one, or multiple countries",
            anchor="w",
            font=ctk.CTkFont(
                size=12
            )
        )

        optional_label.grid(
            row=1,
            column=0,
            pady=(2, 10),
            sticky="ew"
        )

    def _create_search_box(self) -> None:
        """
        Creates the country-search field.
        """

        search_entry = ctk.CTkEntry(
            master=self,
            textvariable=self._search_variable,
            placeholder_text="Search countries..."
        )

        search_entry.grid(
            row=2,
            column=0,
            pady=(0, 10),
            sticky="ew"
        )

        self._search_variable.trace_add(
            "write",
            self._handle_search_change
        )

    def _create_country_list(self) -> None:
        """
        Creates one checkbox for every available country.
        """

        self._country_list_frame = (
            ctk.CTkScrollableFrame(
                master=self,
                height=220
            )
        )

        self._country_list_frame.grid(
            row=3,
            column=0,
            sticky="nsew"
        )

        self._country_list_frame.grid_columnconfigure(
            0,
            weight=1
        )

        for country in self._available_countries:
            country_variable = ctk.BooleanVar(
                value=(
                    country
                    in self._selected_countries
                )
            )

            self._country_variables[
                country
            ] = country_variable

            country_checkbox = ctk.CTkCheckBox(
                master=self._country_list_frame,
                text=country,
                variable=country_variable,
                command=self._handle_selection_change
            )

            self._country_checkboxes[
                country
            ] = country_checkbox

        self._display_matching_countries()

    def _create_selection_summary(self) -> None:
        """
        Creates the number-of-selected-countries label.
        """

        self._selection_summary_label = (
            ctk.CTkLabel(
                master=self,
                text="",
                anchor="w"
            )
        )

        self._selection_summary_label.grid(
            row=4,
            column=0,
            pady=(10, 0),
            sticky="ew"
        )

        self._update_selection_summary()

    def _handle_search_change(
        self,
        *_: object
    ) -> None:
        """
        Refreshes the visible country list when search text
        changes.
        """

        self._display_matching_countries()

    def _display_matching_countries(self) -> None:
        """
        Displays only countries matching the search text.
        """

        search_text = (
            self._search_variable
            .get()
            .strip()
            .lower()
        )

        for checkbox in (
            self._country_checkboxes.values()
        ):
            checkbox.grid_forget()

        visible_row = 0

        for country in self._available_countries:
            if (
                search_text
                and search_text
                not in country.lower()
            ):
                continue

            checkbox = self._country_checkboxes[
                country
            ]

            checkbox.grid(
                row=visible_row,
                column=0,
                padx=10,
                pady=5,
                sticky="w"
            )

            visible_row += 1

    def _handle_selection_change(self) -> None:
        """
        Updates the summary and informs the parent that the
        selection changed.
        """

        selected_countries = (
            self.get_selected_countries()
        )

        self._update_selection_summary()

        if self._on_selection_change is not None:
            self._on_selection_change(
                selected_countries
            )

    def _update_selection_summary(self) -> None:
        """
        Displays the current number of selected countries.
        """

        selected_count = len(
            self.get_selected_countries()
        )

        if selected_count == 1:
            summary_text = "1 country selected"
        else:
            summary_text = (
                f"{selected_count} countries selected"
            )

        self._selection_summary_label.configure(
            text=summary_text
        )