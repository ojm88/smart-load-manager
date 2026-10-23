"""Validate the image files bundled for Home Assistant integration branding."""
import struct
import unittest
from pathlib import Path


BRAND = Path(__file__).parents[1] / "custom_components" / "smart_load_manager" / "brand"
EXPECTED = {
    "icon.png": (256, 256),
    "icon@2x.png": (512, 512),
    "dark_icon.png": (256, 256),
    "dark_icon@2x.png": (512, 512),
    "logo.png": (768, 256),
    "logo@2x.png": (1536, 512),
    "dark_logo.png": (768, 256),
    "dark_logo@2x.png": (1536, 512),
}


class BrandAssetsTest(unittest.TestCase):
    def test_home_assistant_brand_images_are_valid_transparent_pngs(self):
        for filename, expected_size in EXPECTED.items():
            with self.subTest(filename=filename):
                data = (BRAND / filename).read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                width, height = struct.unpack(">II", data[16:24])
                self.assertEqual((width, height), expected_size)
                # PNG color type 6 means RGBA, preserving transparent backgrounds.
                self.assertEqual(data[25], 6)


if __name__ == "__main__":
    unittest.main()
