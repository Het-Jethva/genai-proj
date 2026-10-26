import unittest
from unittest.mock import patch

from src.campus_guide.providers import OpenRouterProvider, ProviderError
from src.campus_guide.settings import get_settings


class _Response:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.body


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = OpenRouterProvider(get_settings({"OPENROUTER_API_KEY": "test-key"}))

    def test_valid_response_is_normalized(self):
        body = b'{"model":"test-model","choices":[{"message":{"content":"  Hello **there**  "}}]}'
        with patch("src.campus_guide.providers.urllib.request.urlopen", return_value=_Response(body)):
            result = self.provider.generate("system", "user")

        self.assertEqual(result.text, "Hello **there**")
        self.assertEqual(result.model, "test-model")

    def test_malformed_response_is_reported_as_provider_error(self):
        body = b'{"choices":[{"message":{"content":""}}]}'
        with patch("src.campus_guide.providers.urllib.request.urlopen", return_value=_Response(body)), self.assertRaisesRegex(ProviderError, "empty answer"):
            self.provider.generate("system", "user")

    def test_request_errors_are_reported_as_provider_error(self):
        with patch(
            "src.campus_guide.providers.urllib.request.urlopen",
            side_effect=ValueError("invalid request"),
        ), self.assertRaisesRegex(ProviderError, "request failed"):
            self.provider.generate("system", "user")


if __name__ == "__main__":
    unittest.main()
