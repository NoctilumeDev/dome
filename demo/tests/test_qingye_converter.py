import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "qingye_converter", ROOT / "demo/qingye/convert_wxml.py"
)
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class QingyeStylesTest(unittest.TestCase):
    def test_native_elements_convert_without_changing_class_or_id_names(self):
        source = "page button, view:hover > image {width:32rpx;} .page, #view, .cover-image, .text {color:red;}"
        result = converter.css(source)
        self.assertIn(".qy-surface button, div:hover > img", result)
        self.assertIn(".page, #view, .cover-image, .text {color:red;}", result)
        self.assertIn("width:calc(32 * var(--rpx))", result)

    def test_real_page_spacing_survives_browser_conversion(self):
        source = (ROOT / "qingye/miniprogram/app.wxss").read_text(encoding="utf-8")
        result = converter.css(source)
        self.assertIn(".page {\n  padding:calc(32 * var(--rpx))", result)
        self.assertNotIn("..qy-surface", result)
        self.assertIn(".qy-surface button.primary", result)


if __name__ == "__main__":
    unittest.main()
