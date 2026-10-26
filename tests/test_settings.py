import unittest

from src.campus_guide.settings import SettingsError, get_settings


class SettingsTests(unittest.TestCase):
    def test_invalid_numeric_setting_has_a_clear_error(self):
        with self.assertRaisesRegex(SettingsError, "MIN_RETRIEVAL_SCORE"):
            get_settings({"MIN_RETRIEVAL_SCORE": "not-a-number"})

    def test_request_cap_must_be_positive(self):
        with self.assertRaisesRegex(SettingsError, "MAX_REQUESTS_PER_SESSION"):
            get_settings({"MAX_REQUESTS_PER_SESSION": "0"})

    def test_invalid_boolean_setting_has_a_clear_error(self):
        with self.assertRaisesRegex(SettingsError, "ENABLE_DENSE_EMBEDDINGS"):
            get_settings({"ENABLE_DENSE_EMBEDDINGS": "sometimes"})
