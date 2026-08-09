from dataclasses import dataclass, field


@dataclass(frozen=True)
class GenerationRequest:
    """
    Represents the complete set of user selections required
    to generate pricing.
    """

    currency: str
    product_id: str
    pricing_type: str

    sender_ids: dict[str, str] = field(
        default_factory=dict
    )

    local_countries: list[str] = field(
        default_factory=list
    )