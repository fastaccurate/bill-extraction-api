"""
Image preprocessing: Enhancement, rotation detection, denoising
"""
import cv2
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Handle image preprocessing and enhancement"""

    def __init__(self, contrast_threshold: float = 1.5, denoise_strength: int = 10):
        """
        Initialize preprocessor

        Args:
            contrast_threshold: Contrast enhancement factor
            denoise_strength: Denoising strength (0-20, higher = stronger)
        """
        self.contrast_threshold = contrast_threshold
        self.denoise_strength = denoise_strength

    def process(self, image_path: Path) -> np.ndarray:
        """
        Process image: load, enhance, denoise

        Args:
            image_path: Path to image file

        Returns:
            Processed image (numpy array)
        """
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        logger.info(f"Loaded image: {image_path}, shape: {image.shape}")

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Denoise using bilateral filter (preserves edges)
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Auto-rotate if needed (using edge detection)
        rotated = self._auto_rotate(enhanced)

        logger.info("Image preprocessing complete")
        return rotated

    def _auto_rotate(self, image: np.ndarray) -> np.ndarray:
        """
        Detect and correct image rotation

        Args:
            image: Grayscale image

        Returns:
            Rotated image if needed, otherwise original
        """
        try:
            # Detect edges
            edges = cv2.Canny(image, 50, 150)

            # Find contours
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if not contours:
                return image

            # Get largest contour
            largest = max(contours, key=cv2.contourArea)

            # Fit rectangle
            rect = cv2.minAreaRect(largest)
            angle = rect[2]

            # Only rotate if angle is significant (> 2 degrees)
            if abs(angle) > 2:
                logger.info(f"Auto-rotating image by {angle} degrees")
                h, w = image.shape
                rotation_matrix = cv2.getRotationMatrix2D(
                    (w/2, h/2), angle, 1.0
                )
                rotated = cv2.warpAffine(
                    image, rotation_matrix, (w, h),
                    borderMode=cv2.BORDER_REFLECT
                )
                return rotated

            return image

        except Exception as e:
            logger.warning(f"Auto-rotate failed: {e}, using original")
            return image

    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast

        Args:
            image: Input image

        Returns:
            Enhanced image
        """
        # Convert to float
        img_float = image.astype(np.float32) / 255.0

        # Apply contrast enhancement: output = 1 + (input - 0.5) * factor
        enhanced = 1.0 + (img_float - 0.5) * self.contrast_threshold

        # Clip to valid range
        enhanced = np.clip(enhanced, 0, 1)

        # Convert back to uint8
        return (enhanced * 255).astype(np.uint8)


# Singleton instance
_preprocessor = None


def get_preprocessor() -> ImagePreprocessor:
    """Get or create preprocessor instance"""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = ImagePreprocessor()
    return _preprocessor
