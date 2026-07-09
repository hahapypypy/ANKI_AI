import json
import unittest
from pathlib import Path


class ManifestTests(unittest.TestCase):
    def test_manifest_contains_required_addon_fields(self):
        manifest_path = Path(__file__).resolve().parent.parent / "manifest.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertTrue(data.get("name"), "manifest should declare a display name")
        self.assertTrue(data.get("package"), "manifest should declare a package id")
        self.assertTrue(data.get("version"), "manifest should declare a version")
        self.assertTrue(data.get("author"), "manifest should declare an author")
        self.assertTrue(data.get("desc"), "manifest should declare a description")


if __name__ == "__main__":
    unittest.main()
