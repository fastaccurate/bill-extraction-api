"""
Table parser: Convert OCR rows into structured bill items
"""
import re
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


class TableParser:
    """Parse table rows into structured bill items"""

    # Regex patterns to identify fields
    QUANTITY_PATTERN = re.compile(r'^\d+(\.\d+)?$')
    RATE_PATTERN = re.compile(r'^\d+(\.\d+)?$')
    AMOUNT_PATTERN = re.compile(r'^\d+(\.\d+)?$')

    def __init__(self):
        """Initialize table parser"""
        pass

    def parse_rows(self, rows: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Parse rows of OCR text into bill items

        Args:
            rows: List of rows, each containing OCR items

        Returns:
            List of parsed bill items with: name, qty, rate, amount
        """
        parsed_items = []

        for row_idx, row in enumerate(rows):
            try:
                item = self._parse_row(row, row_idx)
                if item:
                    parsed_items.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse row {row_idx}: {e}")
                continue

        logger.info(f"Parsed {len(parsed_items)} items from {len(rows)} rows")
        return parsed_items

    def _parse_row(
        self, 
        row: List[Dict[str, Any]], 
        row_idx: int
    ) -> Optional[Dict[str, Any]]:
        """
        Parse a single row into a bill item

        Strategy: Last 3 columns are likely quantity, rate, amount
        Earlier columns are item name

        Args:
            row: List of OCR items in the row
            row_idx: Row index

        Returns:
            Parsed item or None if invalid
        """
        if len(row) < 2:
            return None

        try:
            # Extract fields based on position
            # Strategy: Try to identify numeric columns from right to left

            texts = [item["text"] for item in row]
            confidences = [item["confidence"] for item in row]

            # Try to find numeric columns (amount, rate, qty)
            numeric_cols = []
            for i, text in enumerate(texts):
                if self._is_numeric(text):
                    numeric_cols.append(i)

            # If we have at least 3 numeric columns, use last 3
            if len(numeric_cols) >= 3:
                qty_idx = numeric_cols[-3]
                rate_idx = numeric_cols[-2]
                amount_idx = numeric_cols[-1]

                # Everything before qty is the name
                name_parts = texts[:qty_idx]
                name = " ".join(name_parts).strip()

                qty = self._parse_float(texts[qty_idx])
                rate = self._parse_float(texts[rate_idx])
                amount = self._parse_float(texts[amount_idx])

                # Calculate confidence
                confidence = np.mean([
                    confidences[qty_idx],
                    confidences[rate_idx],
                    confidences[amount_idx]
                ])

                return {
                    "item_name": name,
                    "item_quantity": qty,
                    "item_rate": rate,
                    "item_amount": amount,
                    "confidence": float(confidence),
                    "row_idx": row_idx
                }

            # Fallback: If only 1-2 numeric columns, might be subtotal or incomplete
            elif len(numeric_cols) >= 1:
                # Could be a subtotal - just extract what we can
                amount = self._parse_float(texts[numeric_cols[-1]])

                return {
                    "item_name": " ".join(texts[:-1]).strip(),
                    "item_quantity": 1.0,
                    "item_rate": amount,
                    "item_amount": amount,
                    "confidence": 0.5,  # Lower confidence for incomplete rows
                    "row_idx": row_idx
                }

            return None

        except Exception as e:
            logger.warning(f"Parse error in row {row_idx}: {e}")
            return None

    def _is_numeric(self, text: str) -> bool:
        """Check if text represents a number"""
        text = text.strip()
        if not text:
            return False

        # Remove common currency symbols and separators
        cleaned = text.replace("₹", "").replace("$", "").replace(",", "")

        try:
            float(cleaned)
            return True
        except ValueError:
            return False

    def _parse_float(self, text: str) -> float:
        """Parse text to float, handling currency symbols and separators"""
        text = text.strip()

        # Remove currency symbols
        text = text.replace("₹", "").replace("$", "").replace("Rs", "")

        # Remove comma separators (Indian numbering: 1,000)
        text = text.replace(",", "")

        try:
            return float(text)
        except ValueError:
            logger.warning(f"Could not parse float: {text}")
            return 0.0


# Singleton instance
_table_parser = None


def get_table_parser() -> TableParser:
    """Get or create table parser instance"""
    global _table_parser
    if _table_parser is None:
        _table_parser = TableParser()
    return _table_parser
