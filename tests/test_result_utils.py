import unittest

from utils.result_utils import extract_result_urls


class TestExtractResultUrls(unittest.TestCase):
    def test_collects_all_supported_fields(self):
        payload = {
            "result_url": "https://a.png",
            "result_urls": ["https://b.png"],
            "urls": ["https://c.png"],
            "result": [
                {"urls": ["https://d.png"]},
                ["https://e.png", "https://a.png"],
            ],
        }
        urls = extract_result_urls(payload)
        self.assertEqual(
            urls,
            ["https://a.png", "https://b.png", "https://c.png", "https://d.png", "https://e.png"],
        )

    def test_limit_applies(self):
        payload = {"urls": ["u1", "u2", "u3"]}
        self.assertEqual(extract_result_urls(payload, limit=2), ["u1", "u2"])

    def test_invalid_payload_returns_empty(self):
        self.assertEqual(extract_result_urls(None), [])
        self.assertEqual(extract_result_urls([]), [])


if __name__ == "__main__":
    unittest.main()
