import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import disk_check


class DiskCheckTests(unittest.TestCase):
    def invoke(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = disk_check.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_warning_starts_at_threshold(self):
        self.assertEqual(disk_check.check_usage(80, 80), "WARNING")

    def test_below_threshold_is_safe(self):
        self.assertEqual(disk_check.check_usage(79.999, 80), "OK")

    def test_above_threshold_is_warning(self):
        self.assertEqual(disk_check.check_usage(81, 80), "WARNING")

    def test_empty_disk_is_safe(self):
        self.assertEqual(disk_check.check_usage(0), "OK")

    def test_full_disk_is_warning(self):
        self.assertEqual(disk_check.check_usage(100), "WARNING")

    def test_custom_threshold(self):
        self.assertEqual(disk_check.check_usage(60, 60), "WARNING")

    def test_negative_usage_is_rejected(self):
        with self.assertRaises(ValueError):
            disk_check.check_usage(-1)

    def test_usage_over_100_is_rejected(self):
        with self.assertRaises(ValueError):
            disk_check.check_usage(101)

    def test_invalid_threshold_is_rejected(self):
        for threshold in (-1, 101, float("nan"), float("inf")):
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                disk_check.check_usage(50, threshold)

    def test_nonfinite_usage_is_rejected(self):
        with self.assertRaises(ValueError):
            disk_check.check_usage(float("nan"))

    def test_disk_percent(self):
        usage = type("Usage", (), {"total": 1000, "used": 250})()
        with patch("disk_check.shutil.disk_usage", return_value=usage):
            self.assertEqual(disk_check.disk_percent("."), 25)

    def test_cli_safe_returns_zero(self):
        code, out, _ = self.invoke("--used-percent", "79", "--threshold", "80")
        self.assertEqual(code, 0)
        self.assertIn("OK:", out)

    def test_cli_threshold_returns_one(self):
        code, out, _ = self.invoke("--used-percent", "80", "--threshold", "80")
        self.assertEqual(code, 1)
        self.assertIn("WARNING:", out)

    def test_cli_invalid_returns_two(self):
        code, _, err = self.invoke("--used-percent", "-1")
        self.assertEqual(code, 2)
        self.assertIn("ERROR:", err)

    def test_missing_disk_returns_two(self):
        with patch("disk_check.shutil.disk_usage", side_effect=FileNotFoundError("missing")):
            self.assertEqual(self.invoke("--path", "missing")[0], 2)

    def test_example_settings(self):
        settings = disk_check.load_settings(Path(__file__).resolve().parents[1] / "settings.json.example")
        self.assertEqual(settings, {"path": ".", "threshold": 80})

    def test_cli_uses_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(json.dumps({"path": ".", "threshold": 60}), encoding="utf-8")
            self.assertEqual(self.invoke("--config", str(path), "--used-percent", "60")[0], 1)

    def test_cli_overrides_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text('{"threshold": 60}', encoding="utf-8")
            code, _, _ = self.invoke("--config", str(path), "--threshold", "80", "--used-percent", "60")
            self.assertEqual(code, 0)

    def test_invalid_json_returns_two(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text("{broken", encoding="utf-8")
            self.assertEqual(self.invoke("--config", str(path))[0], 2)

    def test_config_must_be_object(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                disk_check.load_settings(path)


if __name__ == "__main__":
    unittest.main()
