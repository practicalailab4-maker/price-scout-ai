
import unittest

from price_verifier import verify_product_identity


class TestProductIdentity(unittest.TestCase):

    def test_correct_product_and_sku(self):
        result = verify_product_identity(
            expected_name="AMD Ryzen 7 9700X",
            detected_name="AMD Ryzen 7 9700X",
            expected_sku="100-100001404WOF",
            detected_sku="100-100001404WOF"
        )

        self.assertTrue(result["matched"])
        self.assertEqual(
            result["status"],
            "name_and_sku_matched"
        )

    def test_wrong_sku_rejected(self):
        result = verify_product_identity(
            expected_name="AMD Ryzen 7 9700X",
            detected_name="AMD Ryzen 7 9700X",
            expected_sku="100-100001404WOF",
            detected_sku="WRONG-SKU-123"
        )

        self.assertFalse(result["matched"])
        self.assertEqual(
            result["status"],
            "sku_mismatch"
        )


    def test_missing_required_sku_rejected(self):
        result = verify_product_identity(
            expected_name="AMD Ryzen 7 9700X",
            detected_name="AMD Ryzen 7 9700X",
            expected_sku="100-100001404WOF",
            detected_sku=None
        )

        self.assertFalse(result["matched"])
        self.assertEqual(
            result["status"],
            "missing_sku"
        )

    def test_wrong_product_name_rejected(self):
        result = verify_product_identity(
            expected_name="AMD Ryzen 7 9700X",
            detected_name="AMD Ryzen 5 9600X",
            expected_sku="100-100001404WOF",
            detected_sku="OTHER-PRODUCT"
        )

        self.assertFalse(result["matched"])
        self.assertEqual(
            result["status"],
            "product_mismatch"
        )

    def test_name_match_without_required_sku(self):
        result = verify_product_identity(
            expected_name="AMD Ryzen 7 9700X",
            detected_name="AMD Ryzen 7 9700X"
        )

        self.assertTrue(result["matched"])
        self.assertEqual(
            result["status"],
            "name_matched_sku_not_checked"
        )

    def test_product_name_case_insensitive(self):
        result = verify_product_identity(
            expected_name="AMD Ryzen 7 9700X",
            detected_name="amd ryzen 7 9700x",
            expected_sku="100-100001404WOF",
            detected_sku="100-100001404WOF"
        )

        self.assertTrue(result["matched"])
        self.assertEqual(
            result["status"],
            "name_and_sku_matched"
        )

if __name__ == "__main__":
    unittest.main()
