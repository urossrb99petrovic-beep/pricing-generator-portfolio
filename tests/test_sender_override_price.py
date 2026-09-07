import sys
import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path


APPLICATION_ROOT = Path(__file__).resolve().parent.parent

if str(APPLICATION_ROOT) not in sys.path:
    sys.path.insert(0, str(APPLICATION_ROOT))


from app.models.sender_override_price import (
    SenderOverridePrice
)


class TestSenderOverridePrice(unittest.TestCase):
    """
    Tests the SenderOverridePrice model.
    """

    def test_creates_sender_override_price(
        self
    ) -> None:
        sender_price = SenderOverridePrice(
            lookup_value="United States - 10DLC",
            baseline_price=Decimal("0.012"),
            enterprise_price=Decimal("0.01")
        )

        self.assertEqual(
            sender_price.lookup_value,
            "United States - 10DLC"
        )

        self.assertEqual(
            sender_price.baseline_price,
            Decimal("0.012")
        )

        self.assertEqual(
            sender_price.enterprise_price,
            Decimal("0.01")
        )

    def test_sender_override_price_is_immutable(
        self
    ) -> None:
        sender_price = SenderOverridePrice(
            lookup_value="Canada - Toll Free",
            baseline_price=Decimal("0.02"),
            enterprise_price=Decimal("0.018")
        )

        with self.assertRaises(
            FrozenInstanceError
        ):
            sender_price.lookup_value = "Changed"


if __name__ == "__main__":
    unittest.main()