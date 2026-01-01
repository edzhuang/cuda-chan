"""Screen capture and basic analysis."""

import asyncio
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import numpy as np
from PIL import Image
import mss
import pytesseract

from config.settings import settings
from utils.logger import log


class ScreenCapture:
    """Captures and analyzes screen content."""

    def __init__(self):
        """Initialize screen capture."""
        self.sct = mss.mss()
        self.last_capture: Optional[np.ndarray] = None
        self.last_capture_time = 0

        # Capture settings
        self.monitor_index = 1  # Primary monitor
        self.capture_region: Optional[Dict[str, int]] = None  # Full screen by default

        # Change detection
        self.change_threshold = 0.05  # 5% difference to trigger update

        log.info("Screen capture initialized")

    def capture_screen(
        self,
        region: Optional[Dict[str, int]] = None
    ) -> Optional[Image.Image]:
        """
        Capture current screen.

        Args:
            region: Region to capture ({"top": y, "left": x, "width": w, "height": h})
                   None = full screen

        Returns:
            PIL Image or None if failed
        """
        try:
            # Use specified region or full monitor
            capture_region = region or self.capture_region or self.sct.monitors[self.monitor_index]

            # Capture screenshot
            screenshot = self.sct.grab(capture_region)

            # Convert to PIL Image
            img = Image.frombytes(
                'RGB',
                (screenshot.width, screenshot.height),
                screenshot.rgb
            )

            self.last_capture = np.array(img)
            self.last_capture_time = asyncio.get_event_loop().time()

            log.debug(f"Captured screen: {img.size}")
            return img

        except Exception as e:
            log.error(f"Screen capture failed: {e}")
            return None

    async def capture_screen_async(
        self,
        region: Optional[Dict[str, int]] = None
    ) -> Optional[Image.Image]:
        """Async version of capture_screen."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.capture_screen, region)

    def has_significant_change(self, new_image: Image.Image) -> bool:
        """
        Check if new image has significant changes from last capture.

        Args:
            new_image: New image to compare

        Returns:
            True if significant change detected
        """
        if self.last_capture is None:
            return True  # First capture always counts as change

        try:
            # Convert new image to numpy array
            new_array = np.array(new_image)

            # Ensure shapes match
            if new_array.shape != self.last_capture.shape:
                return True

            # Calculate pixel difference
            diff = np.abs(new_array.astype(float) - self.last_capture.astype(float))
            mean_diff = np.mean(diff) / 255.0  # Normalize to 0-1

            changed = mean_diff > self.change_threshold
            log.debug(f"Screen change: {mean_diff:.3f} (threshold: {self.change_threshold})")

            return changed

        except Exception as e:
            log.error(f"Change detection failed: {e}")
            return True  # Assume change on error

    def extract_text(self, image: Image.Image) -> str:
        """
        Extract text from image using OCR.

        Args:
            image: Image to extract text from

        Returns:
            Extracted text
        """
        try:
            # Use pytesseract for OCR
            text = pytesseract.image_to_string(image)
            text = text.strip()

            log.debug(f"Extracted text: {len(text)} characters")
            return text

        except Exception as e:
            log.error(f"Text extraction failed: {e}")
            return ""

    async def extract_text_async(self, image: Image.Image) -> str:
        """Async version of extract_text."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.extract_text, image)

    def resize_for_api(
        self,
        image: Image.Image,
        max_dimension: int = 1024
    ) -> Image.Image:
        """
        Resize image for API transmission.

        Args:
            image: Image to resize
            max_dimension: Maximum width or height

        Returns:
            Resized image
        """
        width, height = image.size

        if width <= max_dimension and height <= max_dimension:
            return image

        # Calculate new size maintaining aspect ratio
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))

        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        log.debug(f"Resized image: {image.size} -> {resized.size}")

        return resized

    def create_text_summary(
        self,
        image: Optional[Image.Image] = None,
        include_ocr: bool = True
    ) -> str:
        """
        Create a text summary of screen content.

        Args:
            image: Image to analyze (uses last capture if None)
            include_ocr: Whether to include OCR text

        Returns:
            Text summary
        """
        if image is None and self.last_capture is not None:
            image = Image.fromarray(self.last_capture)

        if image is None:
            return "No screen content available"

        summary_parts = []

        # Basic info
        summary_parts.append(f"Screen size: {image.size[0]}x{image.size[1]}")

        # Dominant colors
        colors = self._get_dominant_colors(image)
        summary_parts.append(f"Dominant colors: {colors}")

        # OCR text if requested
        if include_ocr:
            text = self.extract_text(image)
            if text:
                # Limit text length
                text = text[:200]
                summary_parts.append(f"Visible text: {text}")

        summary = " | ".join(summary_parts)
        return summary

    def _get_dominant_colors(self, image: Image.Image, num_colors: int = 3) -> str:
        """Get dominant colors in image."""
        try:
            # Resize for faster processing
            small_image = image.resize((100, 100))

            # Convert to RGB if needed
            if small_image.mode != 'RGB':
                small_image = small_image.convert('RGB')

            # Get color histogram
            pixels = np.array(small_image).reshape(-1, 3)

            # Simple clustering: find most common colors
            unique_colors = np.unique(pixels, axis=0, return_counts=True)
            colors = unique_colors[0]
            counts = unique_colors[1]

            # Sort by frequency
            top_indices = counts.argsort()[-num_colors:][::-1]
            top_colors = colors[top_indices]

            # Convert to color names
            color_names = []
            for color in top_colors:
                r, g, b = color
                color_names.append(self._rgb_to_color_name(r, g, b))

            return ", ".join(color_names)

        except Exception as e:
            log.error(f"Color analysis failed: {e}")
            return "unknown"

    def _rgb_to_color_name(self, r: int, g: int, b: int) -> str:
        """Convert RGB to simple color name."""
        # Simple color naming
        if r > 200 and g > 200 and b > 200:
            return "white"
        elif r < 50 and g < 50 and b < 50:
            return "black"
        elif r > g and r > b:
            return "red"
        elif g > r and g > b:
            return "green"
        elif b > r and b > g:
            return "blue"
        elif r > 150 and g > 150:
            return "yellow"
        else:
            return "mixed"

    def set_capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int
    ):
        """
        Set region of screen to capture.

        Args:
            x: Left position
            y: Top position
            width: Region width
            height: Region height
        """
        self.capture_region = {
            "left": x,
            "top": y,
            "width": width,
            "height": height
        }
        log.info(f"Capture region set: {width}x{height} at ({x}, {y})")

    def reset_capture_region(self):
        """Reset to full screen capture."""
        self.capture_region = None
        log.info("Capture region reset to full screen")

    def save_screenshot(self, filepath: Path):
        """Save last screenshot to file."""
        if self.last_capture is not None:
            image = Image.fromarray(self.last_capture)
            image.save(filepath)
            log.info(f"Screenshot saved: {filepath}")
        else:
            log.warning("No screenshot to save")


if __name__ == "__main__":
    # Test screen capture
    async def test_capture():
        capture = ScreenCapture()

        print("Capturing screen...")
        image = await capture.capture_screen_async()

        if image:
            print(f"Captured: {image.size}")

            # Test text extraction
            print("\nExtracting text...")
            text = await capture.extract_text_async(image)
            print(f"Text: {text[:100] if text else 'None'}")

            # Test summary
            print("\nCreating summary...")
            summary = capture.create_text_summary(image)
            print(f"Summary: {summary}")

            # Test change detection
            print("\nTesting change detection...")
            print(f"Has change: {capture.has_significant_change(image)}")

            # Save test screenshot
            output_dir = Path("data/screenshots")
            output_dir.mkdir(parents=True, exist_ok=True)
            capture.save_screenshot(output_dir / "test_screenshot.png")

        else:
            print("Capture failed")

    asyncio.run(test_capture())
