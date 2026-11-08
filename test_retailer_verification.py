
import unittest
from unittest.mock import patch
from price_verifier import fetch_retailer_price, read_limited_response
import requests


class TestRetailerVerification(unittest.TestCase):

    def test_network_disabled_by_default(self):
        url = "https://www.bestbuy.com/site/example-product"

        with patch("price_verifier.requests.Session") as mock_session:
            result = fetch_retailer_price(url)

            mock_session.assert_not_called()

        self.assertEqual(
            result["status"],
            "network_disabled"
        )
        self.assertIsNone(result["price"])


    def test_unsafe_url_schemes_rejected(self):
        unsafe_urls = [
            "http://www.bestbuy.com/site/product",
            "file:///etc/passwd",
            "ftp://www.bestbuy.com/product"
        ]

        for url in unsafe_urls:
            with self.subTest(url=url):
                with patch(
                    "price_verifier.requests.Session"
                ) as mock_session:
                    result = fetch_retailer_price(
                        url,
                        allow_network=True
                    )

                    mock_session.assert_not_called()

                self.assertNotEqual(
                    result["status"],
                    "price_detected"
                )
                self.assertIsNone(result["price"])

    def test_unapproved_retailer_rejected(self):
        url = "https://example.com/product"

        with patch(
            "price_verifier.requests.Session"
        ) as mock_session:
            result = fetch_retailer_price(
                url,
                allow_network=True
            )

            mock_session.assert_not_called()

        self.assertNotEqual(
            result["status"],
            "price_detected"
        )
        self.assertIsNone(result["price"])

    def test_deceptive_retailer_domain_rejected(self):
        url = "https://www.bestbuy.com.evil-example.com/product"

        with patch(
            "price_verifier.requests.Session"
        ) as mock_session:
            result = fetch_retailer_price(
                url,
                allow_network=True
            )

            mock_session.assert_not_called()

        self.assertNotEqual(
            result["status"],
            "price_detected"
        )
        self.assertIsNone(result["price"])

    def test_url_with_credentials_rejected(self):
        url = "https://www.bestbuy.com@evil-example.com/product"

        with patch(
            "price_verifier.requests.Session"
        ) as mock_session:
            result = fetch_retailer_price(
                url,
                allow_network=True
            )

            mock_session.assert_not_called()

        self.assertNotEqual(
            result["status"],
            "price_detected"
        )
        self.assertIsNone(result["price"])

    def test_nonstandard_https_port_rejected(self):
        url = "https://www.bestbuy.com:8443/product"

        with patch(
            "price_verifier.requests.Session"
        ) as mock_session:
            result = fetch_retailer_price(
                url,
                allow_network=True
            )

            mock_session.assert_not_called()

        self.assertNotEqual(
            result["status"],
            "price_detected"
        )
        self.assertIsNone(result["price"])

    def test_retailer_redirects_disabled(self):
        url = "https://www.bestbuy.com/site/product"

        with patch(
            "price_verifier.requests.Session"
        ) as mock_session:
            mock_response = (
                mock_session.return_value.__enter__.return_value
                .get.return_value
            )

            mock_response.status_code = 302

            result = fetch_retailer_price(
                url,
                allow_network=True
            )

            mock_session.return_value.__enter__.return_value.get.assert_called_once()

            call_kwargs = (
                mock_session.return_value.__enter__.return_value
                .get.call_args.kwargs
            )

            self.assertFalse(
                call_kwargs["allow_redirects"]
            )

        self.assertNotEqual(
            result["status"],
            "price_detected"
        )
        self.assertIsNone(result["price"])

    def test_retailer_request_has_timeout(self):
        url = "https://www.bestbuy.com/site/product"

        with patch(
            "price_verifier.requests.Session"
        ) as mock_session:
            mock_response = (
                mock_session.return_value.__enter__.return_value
                .get.return_value
            )

            mock_response.status_code = 302

            fetch_retailer_price(
                url,
                allow_network=True
            )

            call_kwargs = (
                mock_session.return_value.__enter__.return_value
                .get.call_args.kwargs
            )

            self.assertEqual(
                call_kwargs["timeout"],
                10
            )

    def test_environment_proxies_disabled(self):
        url = "https://www.bestbuy.com/site/product"

        with patch(
            "price_verifier.requests.Session"
        ) as mock_session:
            session = mock_session.return_value.__enter__.return_value
            session.get.return_value.status_code = 302

            fetch_retailer_price(
                url,
                allow_network=True
            )

            self.assertFalse(session.trust_env)
            session.get.assert_called_once()

    def test_retailer_request_uses_streaming(self):
        url = "https://www.bestbuy.com/site/product"

        with patch(
            "price_verifier.requests.Session"
        ) as mock_session:
            session = mock_session.return_value.__enter__.return_value
            session.get.return_value.status_code = 302

            fetch_retailer_price(
                url,
                allow_network=True
            )

            session.get.assert_called_once()

            call_kwargs = session.get.call_args.kwargs

            self.assertTrue(
                call_kwargs["stream"]
            )

    def test_oversized_response_rejected(self):
        class FakeResponse:
            def iter_content(self, chunk_size):
                yield b"A" * (1024 * 1024)
                yield b"B" * (1024 * 1024)
                yield b"C"

        response = FakeResponse()

        result = read_limited_response(
            response,
            max_bytes=2 * 1024 * 1024
        )

        self.assertEqual(
            result["status"],
            "response_too_large"
        )
        self.assertIsNone(result["content"])

    def test_response_exactly_at_size_limit_accepted(self):
        class FakeResponse:
            def iter_content(self, chunk_size):
                yield b"A" * (1024 * 1024)
                yield b"B" * (1024 * 1024)

        result = read_limited_response(
            FakeResponse(),
            max_bytes=2 * 1024 * 1024
        )

        self.assertEqual(
            result["status"],
            "response_within_limit"
        )
        self.assertEqual(
            len(result["content"]),
            2 * 1024 * 1024
        )

    def test_empty_response_chunks_ignored(self):
        class FakeResponse:
            def iter_content(self, chunk_size):
                yield b""
                yield b"Hello"
                yield b""
                yield b" World"
                yield b""

        result = read_limited_response(
            FakeResponse(),
            max_bytes=100
        )

        self.assertEqual(
            result["status"],
            "response_within_limit"
        )
        self.assertEqual(
            result["content"],
            b"Hello World"
        )

    def test_retailer_http_error_handled(self):
        url = "https://www.bestbuy.com/site/product"

        with patch(
            "price_verifier.requests.Session"
        ) as mock_session:
            session = mock_session.return_value.__enter__.return_value
            response = session.get.return_value

            response.status_code = 404
            response.raise_for_status.side_effect = (
                requests.exceptions.HTTPError("404 Not Found")
            )

            result = fetch_retailer_price(
                url,
                allow_network=True
            )

        self.assertNotEqual(
            result["status"],
            "price_detected"
        )
        self.assertIsNone(result["price"])

    def test_retailer_connection_failure_handled(self):
        url = "https://www.bestbuy.com/site/product"

        with patch(
            "price_verifier.requests.Session"
        ) as mock_session:
            session = mock_session.return_value.__enter__.return_value

            session.get.side_effect = (
                requests.exceptions.ConnectionError(
                    "Simulated connection failure"
                )
            )

            result = fetch_retailer_price(
                url,
                allow_network=True
            )

        self.assertNotEqual(
            result["status"],
            "price_detected"
        )
        self.assertIsNone(result["price"])

    def test_valid_retailer_product_response(self):
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "AMD Ryzen 7 9700X",
            "sku": "100-100001404WOF",
            "offers": {
                "price": "299.99",
                "priceCurrency": "USD"
            }
        }
        </script>
        """

        with patch(
            "price_verifier.requests.Session"
        ) as mock_session:
            session = mock_session.return_value.__enter__.return_value
            response = session.get.return_value

            response.status_code = 200
            response.encoding = "utf-8"
            response.iter_content.return_value = [
                html.encode("utf-8")
            ]

            result = fetch_retailer_price(
                "https://www.bestbuy.com/site/product",
                expected_product="AMD Ryzen 7 9700X",
                expected_sku="100-100001404WOF",
                allow_network=True
            )

        print("Mock retailer result:", result)

        self.assertEqual(
            result["price"],
            299.99
        )

    def test_wrong_retailer_product_rejected(self):
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "AMD Ryzen 5 9600X",
            "sku": "WRONG-SKU",
            "offers": {
                "price": "199.99",
                "priceCurrency": "USD"
            }
        }
        </script>
        """

        with patch(
            "price_verifier.requests.Session"
        ) as mock_session:
            session = mock_session.return_value.__enter__.return_value
            response = session.get.return_value

            response.status_code = 200
            response.encoding = "utf-8"
            response.iter_content.return_value = [
                html.encode("utf-8")
            ]

            result = fetch_retailer_price(
                "https://www.bestbuy.com/site/product",
                expected_product="AMD Ryzen 7 9700X",
                expected_sku="100-100001404WOF",
                allow_network=True
            )

        print("Wrong product result:", result)

        self.assertNotEqual(
            result["status"],
            "price_detected"
        )
        self.assertNotEqual(
            result.get("price"),
            199.99
        )

    def test_retailer_sku_mismatch_rejected(self):
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "AMD Ryzen 7 9700X",
            "sku": "WRONG-SKU-123",
            "offers": {
                "price": "199.99",
                "priceCurrency": "USD"
            }
        }
        </script>
        """

        with patch(
            "price_verifier.requests.Session"
        ) as mock_session:
            session = mock_session.return_value.__enter__.return_value
            response = session.get.return_value

            response.status_code = 200
            response.encoding = "utf-8"
            response.iter_content.return_value = [
                html.encode("utf-8")
            ]

            result = fetch_retailer_price(
                "https://www.bestbuy.com/site/product",
                expected_product="AMD Ryzen 7 9700X",
                expected_sku="100-100001404WOF",
                allow_network=True
            )

        self.assertNotEqual(
            result["status"],
            "price_detected"
        )
        self.assertNotEqual(
            result.get("price"),
            199.99
        )

if __name__ == "__main__":
    unittest.main()
