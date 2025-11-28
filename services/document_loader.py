"""
Document loader: Download and validate bill images from URLs
"""
import httpx
import logging
from pathlib import Path
from typing import Tuple
from PIL import Image
import io

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Handle downloading and validating documents from URLs"""

    VALID_MIME_TYPES = {
        "image/png", "image/jpeg", "image/jpg", 
        "application/pdf", "image/tiff"
    }

    def __init__(self, timeout: int = 30, max_size: int = 50 * 1024 * 1024):
        """
        Initialize document loader

        Args:
            timeout: Request timeout in seconds
            max_size: Maximum file size in bytes (50MB default)
        """
        self.timeout = timeout
        self.max_size = max_size

    async def download(self, url: str, temp_dir: Path) -> Tuple[Path, str]:
        """
        Download document from URL

        Args:
            url: Document URL
            temp_dir: Temporary directory to save file

        Returns:
            Tuple of (file_path, mime_type)

        Raises:
            ValueError: If URL is invalid or file too large
            IOError: If download fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                # Validate content type
                content_type = response.headers.get("content-type", "").lower()
                mime_type = content_type.split(";")[0].strip()

                if mime_type not in self.VALID_MIME_TYPES:
                    raise ValueError(
                        f"Invalid MIME type: {mime_type}. "
                        f"Supported: {self.VALID_MIME_TYPES}"
                    )

                # Check file size
                if len(response.content) > self.max_size:
                    raise ValueError(
                        f"File too large: {len(response.content)} bytes. "
                        f"Max: {self.max_size} bytes"
                    )

                # Determine file extension
                ext = self._get_extension(mime_type)

                # Save to temporary file
                temp_file = temp_dir / f"document_{id(response)}{ext}"
                temp_file.write_bytes(response.content)

                logger.info(f"Downloaded document: {url} -> {temp_file}")
                return temp_file, mime_type

        except httpx.HTTPError as e:
            logger.error(f"HTTP error downloading {url}: {e}")
            raise IOError(f"Failed to download document: {e}")
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            raise

    def _get_extension(self, mime_type: str) -> str:
        """Get file extension from MIME type"""
        mapping = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "application/pdf": ".pdf",
            "image/tiff": ".tiff"
        }
        return mapping.get(mime_type, ".bin")

    def validate_image(self, file_path: Path) -> bool:
        """
        Validate that file is a readable image

        Args:
            file_path: Path to image file

        Returns:
            True if valid image, False otherwise
        """
        try:
            if file_path.suffix.lower() == ".pdf":
                return True  # PDF validation handled separately

            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception as e:
            logger.error(f"Invalid image file {file_path}: {e}")
            return False


# Singleton instance
_document_loader = None


def get_document_loader() -> DocumentLoader:
    """Get or create document loader instance"""
    global _document_loader
    if _document_loader is None:
        _document_loader = DocumentLoader()
    return _document_loader
