from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class SenderOverridePrice:
    """
    Represents one sender-specific pricing override extracted
    from the 2-way SMS worksheet.
    """

    lookup_value: str
    baseline_price: Decimal
    enterprise_price: Decimal