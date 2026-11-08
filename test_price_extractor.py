
import json
from pathlib import Path

from bs4 import BeautifulSoup


html = Path("sample_product.html").read_text(
    encoding="utf-8"
)

soup = BeautifulSoup(html, "html.parser")

for script in soup.find_all(
    "script",
    type="application/ld+json"
):
    data = json.loads(script.string or script.get_text())

    if data.get("@type") == "Product":
        product_name = data.get("name")
        offer = data.get("offers", {})

        price = float(offer["price"])
        currency = offer["priceCurrency"]

        print("PRICE SCOUT AI — LOCAL TEST")
        print("---------------------------")
        print("Product:", product_name)
        print("Price:", price)
        print("Currency:", currency)
        print("Status: price_detected")
