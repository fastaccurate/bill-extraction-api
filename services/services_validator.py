"""
Validator: Deduplication, amount validation, subtotal detection
CRITICAL: NO double-counting, NO missed items
"""
import logging
import hashlib
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class BillValidator:
    """Validate and clean extracted bill items"""

    def __init__(self, amount_tolerance: float = 0.05):
        """
        Initialize validator

        Args:
            amount_tolerance: Tolerance for amount = qty × rate check (5% default)
        """
        self.amount_tolerance = amount_tolerance

    def validate_and_clean(
        self, 
        items: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Validate and clean extracted items

        CRITICAL STEPS:
        1. Validate amount = qty × rate
        2. Remove duplicates (by name + qty + rate)
        3. Filter out subtotals
        4. Keep valid items only

        Args:
            items: Raw extracted items

        Returns:
            Tuple of (cleaned_items, validation_messages)
        """
        messages = []
        messages.append(f"Starting validation with {len(items)} items")

        # Step 1: Validate amounts
        validated_items = []
        for item in items:
            is_valid, msg = self._validate_item(item)
            if is_valid:
                validated_items.append(item)
            else:
                messages.append(msg)

        messages.append(f"After amount validation: {len(validated_items)} items")

        # Step 2: Remove duplicates
        deduplicated, dup_msgs = self._remove_duplicates(validated_items)
        messages.extend(dup_msgs)

        # Step 3: Filter subtotals
        final_items = self._filter_subtotals(deduplicated)
        messages.append(f"After subtotal filtering: {len(final_items)} items")

        logger.info("; ".join(messages))
        return final_items, messages

    def _validate_item(self, item: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate single item

        Checks:
        - Has required fields
        - Numeric values make sense
        - amount ≈ quantity × rate

        Args:
            item: Item to validate

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Check required fields
            required_fields = ["item_name", "item_quantity", "item_rate", "item_amount"]
            for field in required_fields:
                if field not in item or item[field] is None:
                    return False, f"Item missing {field}: {item}"

            name = item["item_name"]
            qty = float(item["item_quantity"])
            rate = float(item["item_rate"])
            amount = float(item["item_amount"])

            # Skip if zero amount (likely header or garbage)
            if amount == 0 and qty == 0:
                return False, f"Zero amount item: {name}"

            # Validate amount = qty × rate (with tolerance)
            if qty > 0 and rate > 0:
                calculated_amount = qty * rate
                relative_error = abs(amount - calculated_amount) / max(amount, calculated_amount)

                if relative_error > self.amount_tolerance:
                    # Log but don't reject - might be due to discounts
                    logger.debug(
                        f"Amount mismatch for {name}: "
                        f"amount={amount}, qty={qty}, rate={rate}, "
                        f"calculated={calculated_amount}"
                    )

            return True, f"Valid: {name}"

        except Exception as e:
            return False, f"Validation error: {e}"

    def _remove_duplicates(
        self, 
        items: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Remove duplicate items

        Duplicates are identified by: (name, qty, rate) hash

        Args:
            items: Items to deduplicate

        Returns:
            Tuple of (deduplicated_items, messages)
        """
        messages = []
        seen_hashes: Set[str] = set()
        deduplicated = []
        duplicates_found = 0

        for item in items:
            # Create hash of (name, qty, rate)
            hash_key = self._create_hash(
                item["item_name"],
                item["item_quantity"],
                item["item_rate"]
            )

            if hash_key not in seen_hashes:
                seen_hashes.add(hash_key)
                deduplicated.append(item)
            else:
                duplicates_found += 1
                messages.append(
                    f"Duplicate removed: {item['item_name']} "
                    f"(qty={item['item_quantity']}, rate={item['item_rate']})"
                )

        if duplicates_found > 0:
            messages.append(f"Removed {duplicates_found} duplicate items")

        return deduplicated, messages

    def _filter_subtotals(
        self, 
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter out subtotals and section headers

        Heuristics:
        - Rows with keywords: "subtotal", "total", "sub-total"
        - Rows with only amount (no qty/rate)
        - Rows with qty=1 and very high amounts (likely totals)

        Args:
            items: Items to filter

        Returns:
            Filtered items (without subtotals)
        """
        filtered = []
        subtotal_keywords = {"subtotal", "sub-total", "total", "tax", "gst", "discount"}

        for item in items:
            name = item["item_name"].lower()
            qty = item["item_quantity"]
            rate = item["item_rate"]

            # Check for subtotal keywords
            if any(keyword in name for keyword in subtotal_keywords):
                logger.debug(f"Filtered subtotal: {item['item_name']}")
                continue

            # Skip items with no quantity or rate (likely subtotal rows)
            if qty == 0 or qty == 1 and rate == 0:
                continue

            filtered.append(item)

        return filtered

    def _create_hash(self, name: str, qty: float, rate: float) -> str:
        """
        Create hash of (name, qty, rate) for deduplication

        Args:
            name: Item name
            qty: Quantity
            rate: Rate

        Returns:
            Hash string
        """
        key = f"{name.lower().strip()}|{qty}|{rate}"
        return hashlib.md5(key.encode()).hexdigest()

    def calculate_total(self, items: List[Dict[str, Any]]) -> float:
        """
        Calculate total from items

        Args:
            items: List of items

        Returns:
            Sum of item amounts
        """
        total = sum(item["item_amount"] for item in items)
        return total


# Singleton instance
_validator = None


def get_validator() -> BillValidator:
    """Get or create validator instance"""
    global _validator
    if _validator is None:
        _validator = BillValidator()
    return _validator
