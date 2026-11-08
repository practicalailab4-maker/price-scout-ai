
import json
import unittest

from price_verifier import extract_product_price


class TestPriceValidation(unittest.TestCase):

    def make_html(self, price):
        product = {
            "@type": "Product",
            "name": "AMD Ryzen 7 9700X",
            "sku": "100-100001404WOF",
            "offers": {
                "price": price,
                "priceCurrency": "USD"
            }
        }

        return (
            '<script type="application/ld+json">'
            + json.dumps(product)
            + '</script>'
        )

    def test_valid_usd_price(self):
        result = extract_product_price(
            self.make_html("299.99")
        )

        self.assertEqual(result["status"], "price_detected")
        self.assertEqual(result["price"], 299.99)
        self.assertEqual(result["currency"], "USD")

    def test_excessive_decimal_precision(self):
        result = extract_product_price(
            self.make_html("299.9999")
        )

        self.assertEqual(result["status"], "not_verified")
        self.assertIsNone(result["price"])


    def test_invalid_prices(self):
        invalid_prices = [
            "NaN",
            "Infinity",
            "-299.99",
            "0",
            "0.001",
            "",
            None
        ]

        for price in invalid_prices:
            with self.subTest(price=price):
                result = extract_product_price(
                    self.make_html(price)
                )

                self.assertEqual(
                    result["status"],
                    "not_verified"
                )
                self.assertIsNone(result["price"])

    def test_reject_non_usd_currency(self):
        product = {
            "@type": "Product",
            "name": "AMD Ryzen 7 9700X",
            "sku": "100-100001404WOF",
            "offers": {
                "price": "279.99",
                "priceCurrency": "EUR"
            }
        }

        html = (
            '<script type="application/ld+json">'
            + json.dumps(product)
            + '</script>'
        )

        result = extract_product_price(html)

        self.assertEqual(result["status"], "not_verified")
        self.assertIsNone(result["price"])
        self.assertIsNone(result["currency"])

if __name__ == "__main__":
    unittest.main()

