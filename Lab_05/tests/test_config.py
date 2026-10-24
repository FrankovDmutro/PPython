"""Tests for configuration loading and validation."""

from pathlib import Path
import tempfile
import unittest

from experiment_importer.config import load_config
from experiment_importer.exceptions import ConfigurationError


class TestConfig(unittest.TestCase):
    """Test suite for YAML configuration parser and validator."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_load_valid_config(self) -> None:
        cfg_file = self.dir_path / "valid.yaml"
        cfg_file.write_text(
            """
input:
  path: data/exp.csv
output:
  path: output/exp.json
  summary_path: output/sum.json
processing:
  allowed_parameters:
    - temperature
    - pressure
  min_result: 10.0
  max_result: 500.0
  skip_invalid: true
logging:
  level: DEBUG
  path: logs/test.log
""",
            encoding="utf-8",
        )
        config = load_config(cfg_file)
        self.assertEqual(config.processing.allowed_parameters, ("temperature", "pressure"))
        self.assertEqual(config.processing.min_result, 10.0)
        self.assertEqual(config.processing.max_result, 500.0)
        self.assertTrue(config.processing.skip_invalid)
        self.assertEqual(config.logging.level, "DEBUG")

    def test_missing_config_file(self) -> None:
        non_existent = self.dir_path / "absent.yaml"
        with self.assertRaises(ConfigurationError) as ctx:
            load_config(non_existent)
        self.assertIn("not found", str(ctx.exception).lower())

    def test_invalid_yaml_syntax(self) -> None:
        broken_file = self.dir_path / "broken.yaml"
        broken_file.write_text("input: [unclosed list", encoding="utf-8")
        with self.assertRaises(ConfigurationError) as ctx:
            load_config(broken_file)
        self.assertIsNotNone(ctx.exception.__cause__)

    def test_invalid_min_max_range(self) -> None:
        cfg_file = self.dir_path / "range_err.yaml"
        cfg_file.write_text(
            """
input:
  path: data/exp.csv
output:
  path: output/exp.json
processing:
  allowed_parameters: ["voltage"]
  min_result: 100.0
  max_result: 50.0
logging:
  level: INFO
""",
            encoding="utf-8",
        )
        with self.assertRaises(ConfigurationError) as ctx:
            load_config(cfg_file)
        self.assertIn("cannot exceed", str(ctx.exception))

    def test_invalid_logging_level(self) -> None:
        cfg_file = self.dir_path / "log_err.yaml"
        cfg_file.write_text(
            """
input:
  path: data/exp.csv
output:
  path: output/exp.json
processing:
  allowed_parameters: ["voltage"]
logging:
  level: SUPER_VERBOSE
""",
            encoding="utf-8",
        )
        with self.assertRaises(ConfigurationError) as ctx:
            load_config(cfg_file)
        self.assertIn("Invalid log level", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
