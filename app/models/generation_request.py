from dataclasses import dataclass, field


@dataclass(frozen=True)
class GenerationRequest:
    currency: str
    product_id: str

    pricing_type: str | None = None

    sender_ids: dict[str, str] = field(
        default_factory=dict
    )

    local_countries: list[str] = field(
        default_factory=list
    )

    product_options: dict[str, str] = field(
        default_factory=dict
    )

    selected_subproducts: list[str] = field(
        default_factory=list
    )