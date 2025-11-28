"""
OCR Extraction: PaddleOCR wrapper for text and bounding box extraction
"""
import numpy as np
import logging
from typing import List, Tuple, Dict, Any
from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)


class OCRExtractor:
    """Handle OCR extraction using PaddleOCR"""

    def __init__(self, languages: List[str] = None, use_angle_cls: bool = True):
        """
        Initialize OCR extractor

        Args:
            languages: Languages to recognize (default: ["en"])
            use_angle_cls: Use angle classification for rotation
        """
        self.languages = languages or ["en"]
        self.use_angle_cls = use_angle_cls
        self.ocr = None
        self._initialize_ocr()

    def _initialize_ocr(self):
        """Initialize PaddleOCR model (lazy loading)"""
        try:
            logger.info("Initializing PaddleOCR...")
            self.ocr = PaddleOCR(
                use_angle_cls=self.use_angle_cls,
                lang=self.languages,
                show_log=False,
                enable_mkldnn=True
            )
            logger.info("PaddleOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise

    def extract(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extract text and bounding boxes from image

        Args:
            image: Input image (numpy array)

        Returns:
            List of extracted items with:
            - text: Recognized text
            - confidence: Confidence score (0-1)
            - bbox: Bounding box [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            - center: Center point (x, y)
        """
        if self.ocr is None:
            self._initialize_ocr()

        try:
            # Run OCR
            results = self.ocr.ocr(image, cls=self.use_angle_cls)

            if not results or not results[0]:
                logger.warning("No text detected in image")
                return []

            # Parse results
            extracted_items = []
            for line in results[0]:
                bbox, (text, confidence) = line

                # Calculate center point
                center_x = np.mean([point[0] for point in bbox])
                center_y = np.mean([point[1] for point in bbox])

                item = {
                    "text": text.strip(),
                    "confidence": float(confidence),
                    "bbox": [[float(x), float(y)] for x, y in bbox],
                    "center": (float(center_x), float(center_y))
                }

                extracted_items.append(item)

            logger.info(f"Extracted {len(extracted_items)} text regions")
            return extracted_items

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise

    def group_by_row(
        self, 
        items: List[Dict[str, Any]], 
        y_tolerance: float = 10
    ) -> List[List[Dict[str, Any]]]:
        """
        Group extracted items into rows based on Y-coordinate

        Args:
            items: List of extracted items
            y_tolerance: Y-coordinate tolerance for same row

        Returns:
            List of rows, each containing items from left to right
        """
        if not items:
            return []

        # Sort by Y-coordinate
        sorted_items = sorted(items, key=lambda x: x["center"][1])

        # Group into rows
        rows = []
        current_row = [sorted_items[0]]

        for item in sorted_items[1:]:
            # Check if item belongs to current row
            current_y = np.mean([it["center"][1] for it in current_row])
            item_y = item["center"][1]

            if abs(item_y - current_y) <= y_tolerance:
                current_row.append(item)
            else:
                # Start new row
                rows.append(current_row)
                current_row = [item]

        # Add last row
        if current_row:
            rows.append(current_row)

        # Sort each row by X-coordinate (left to right)
        for row in rows:
            row.sort(key=lambda x: x["center"][0])

        logger.info(f"Grouped items into {len(rows)} rows")
        return rows


# Singleton instance
_ocr_extractor = None


def get_ocr_extractor() -> OCRExtractor:
    """Get or create OCR extractor instance"""
    global _ocr_extractor
    if _ocr_extractor is None:
        _ocr_extractor = OCRExtractor()
    return _ocr_extractor
