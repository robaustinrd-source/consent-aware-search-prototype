import unittest

from app.cli import _loopback_host, _loopback_url


class CliSafetyTests(unittest.TestCase):
    def test_accepts_local_addresses(self):
        self.assertEqual(_loopback_host("127.0.0.1"), "127.0.0.1")
        self.assertEqual(_loopback_url("http://localhost:8000/"), "http://localhost:8000")

    def test_rejects_non_loopback_host(self):
        with self.assertRaises(ValueError):
            _loopback_host("0.0.0.0")

    def test_rejects_remote_api_url(self):
        with self.assertRaises(ValueError):
            _loopback_url("https://example.com")


if __name__ == "__main__":
    unittest.main()
