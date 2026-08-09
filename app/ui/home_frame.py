from collections.abc import Callable

import customtkinter as ctk


class HomeFrame(ctk.CTkFrame):
    """
    First page of the Pricing Generator wizard.
    """

    CURRENCY_PLACEHOLDER = "Select currency"
    PRODUCT_PLACEHOLDER = "Select product"

    def __init__(
        self,
        parent: ctk.CTkFrame,
        currencies: list[str],
        products: list[str],
        on_cancel: Callable[[], None],
        on_next: Callable[[str, str], None],
        selected_currency: str | None = None,
        selected_product: str | None = None
    ) -> None:
        """
        Creates the home page.

        Args:
            parent:
                Container in which this frame is displayed.

            currencies:
                Currency values displayed in the dropdown.

            products:
                Product names displayed in the dropdown.

            on_cancel:
                Function called when Cancel is selected.

            on_next:
                Function called when Next is selected.

            selected_currency:
                Previously selected currency, when returning
                from Step 2.

            selected_product:
                Previously selected product, when returning
                from Step 2.
        """

        super().__init__(
            master=parent,
            corner_radius=0
        )

        self._on_next = on_next

        self._currency_variable = ctk.StringVar(
            value=(
                selected_currency
                or self.CURRENCY_PLACEHOLDER
            )
        )

        self._product_variable = ctk.StringVar(
            value=(
                selected_product
                or self.PRODUCT_PLACEHOLDER
            )
        )

        self._configure_grid()
        self._create_header()
        self._create_form(
            currencies=currencies,
            products=products
        )
        self._create_buttons(
            on_cancel=on_cancel
        )

        self._update_next_button_state()

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

    def _create_header(self) -> None:
        """
        Creates the page title and step indicator.
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
            pady=(45, 5)
        )

        step_label = ctk.CTkLabel(
            master=self,
            text="Step 1 of 2",
            font=ctk.CTkFont(
                size=14
            )
        )

        step_label.grid(
            row=1,
            column=0,
            pady=(0, 25)
        )

    def _create_form(
        self,
        currencies: list[str],
        products: list[str]
    ) -> None:
        """
        Creates the Currency and Product controls.
        """

        form_frame = ctk.CTkFrame(
            master=self,
            width=440
        )

        form_frame.grid(
            row=2,
            column=0,
            padx=40,
            pady=10,
            sticky="n"
        )

        form_frame.grid_columnconfigure(
            0,
            weight=1
        )

        currency_label = ctk.CTkLabel(
            master=form_frame,
            text="Currency",
            anchor="w",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        currency_label.grid(
            row=0,
            column=0,
            padx=30,
            pady=(30, 8),
            sticky="ew"
        )

        self._currency_dropdown = ctk.CTkComboBox(
            master=form_frame,
            values=currencies,
            variable=self._currency_variable,
            command=self._handle_selection_change,
            state="readonly",
            width=380
        )

        self._currency_dropdown.grid(
            row=1,
            column=0,
            padx=30,
            pady=(0, 22),
            sticky="ew"
        )

        product_label = ctk.CTkLabel(
            master=form_frame,
            text="Product",
            anchor="w",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        product_label.grid(
            row=2,
            column=0,
            padx=30,
            pady=(0, 8),
            sticky="ew"
        )

        self._product_dropdown = ctk.CTkComboBox(
            master=form_frame,
            values=products,
            variable=self._product_variable,
            command=self._handle_selection_change,
            state="readonly",
            width=380
        )

        self._product_dropdown.grid(
            row=3,
            column=0,
            padx=30,
            pady=(0, 30),
            sticky="ew"
        )

    def _create_buttons(
        self,
        on_cancel: Callable[[], None]
    ) -> None:
        """
        Creates the Cancel and Next buttons.
        """

        button_frame = ctk.CTkFrame(
            master=self,
            fg_color="transparent"
        )

        button_frame.grid(
            row=3,
            column=0,
            padx=40,
            pady=(20, 35),
            sticky="ew"
        )

        button_frame.grid_columnconfigure(
            0,
            weight=1
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
            column=1,
            padx=(0, 12)
        )

        self._next_button = ctk.CTkButton(
            master=button_frame,
            text="Next >",
            command=self._handle_next,
            state="disabled"
        )

        self._next_button.grid(
            row=0,
            column=2
        )

    def _handle_selection_change(
        self,
        _: str
    ) -> None:
        """
        Reacts when a dropdown selection changes.

        The supplied argument is the selected dropdown value.
        It is not needed because both values are read directly
        from their StringVar objects.
        """

        self._update_next_button_state()

    def _update_next_button_state(self) -> None:
        """
        Enables Next only when both required selections exist.
        """

        currency_selected = (
            self._currency_variable.get()
            != self.CURRENCY_PLACEHOLDER
        )

        product_selected = (
            self._product_variable.get()
            != self.PRODUCT_PLACEHOLDER
        )

        if currency_selected and product_selected:
            self._next_button.configure(
                state="normal"
            )
        else:
            self._next_button.configure(
                state="disabled"
            )

    def _handle_next(self) -> None:
        """
        Sends the selected values to MainWindow.
        """

        self._on_next(
            self._currency_variable.get(),
            self._product_variable.get()
        )