
import unittest

from market_engine import resolve_market_ticker


class MarketEngineTests(unittest.TestCase):

    def test_idx_ticker(self):
        result = resolve_market_ticker("BBCA", "IDX")
        self.assertEqual(result["ticker"], "BBCA.JK")
        self.assertEqual(result["currency"], "IDR")

    def test_idx_explicit_suffix(self):
        result = resolve_market_ticker("ANTM.JK", "IDX")
        self.assertEqual(result["ticker"], "ANTM.JK")

    def test_us_ticker(self):
        result = resolve_market_ticker("NVDA", "US")
        self.assertEqual(result["ticker"], "NVDA")
        self.assertEqual(result["currency"], "USD")

    def test_us_class_share(self):
        result = resolve_market_ticker("BRK.B", "US")
        self.assertEqual(result["ticker"], "BRK-B")

    def test_reject_idx_suffix_in_us(self):
        with self.assertRaises(ValueError):
            resolve_market_ticker("BBCA.JK", "US")

    def test_reject_invalid_market(self):
        with self.assertRaises(ValueError):
            resolve_market_ticker("AAPL", "EU")

    def test_reject_empty_ticker(self):
        with self.assertRaises(ValueError):
            resolve_market_ticker("", "IDX")

    def test_reject_invalid_idx_format(self):
        with self.assertRaises(ValueError):
            resolve_market_ticker("AAPL.US", "IDX")


if __name__ == "__main__":
    unittest.main()
