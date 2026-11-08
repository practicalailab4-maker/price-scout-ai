
import json
import os
from price_verifier import verify_price_source, verify_retailer_live_price
from urllib.parse import urlparse



from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def research_product(product_name: str) -> dict:
    response = client.responses.create(
        model="gpt-4.1",
        tools=[{"type": "web_search", "search_context_size": "high"}],
        input=f"""

You are Price Scout AI, a careful US product research assistant.

Research this exact product: {product_name}



RETAILER DISCOVERY STRATEGY:

Research the exact requested product and model.

Find up to EIGHT DISTINCT US retailers with evidence
of an offer for the exact product.

Search relevant retailers individually, including:
- Amazon US
- Best Buy
- Newegg
- Walmart
- B&H Photo Video
- Micro Center
- Target
- Other legitimate US retailers

Do not assume every retailer sells the product.

SEARCH REQUIREMENTS:

1. Search using the full product name and exact model number.
2. Prefer official retailer product pages.
3. Check that the listing describes the same model,
   not a previous generation or a similar product.
4. Include only offers with a numeric price supported
   by a source.
5. Record the retailer associated with each price.
6. Never combine a price from one retailer with a
   product link from another retailer.
7. Do not invent retailers, prices, URLs, or availability.
8. If fewer than eight credible offers are found,
   return fewer offers.

PRICE EVIDENCE:

For each offer, classify verification as:

- direct_listing:
  The price was reported on the retailer's own
  product listing.

- third_party_report:
  The price was reported by another website.

- unverified:
  The price could not be confidently supported.

IMPORTANT:
A source URL alone does not prove that the current
retailer price matches the reported price.

Return the same JSON structure required by this
application. Do not rename existing JSON keys.



RETAILER RULES:
1. Each retailer must appear only once.
2. Prioritize official US retailer product listings.
3. Do not include international retailers.
4. Do not use price comparison sites as retailer names.
5. Do not combine different models, bundles, or refurbished items.
6. If fewer than three credible offers exist, return fewer.

PRICE AND SOURCE RULES:
1. Never invent prices, sellers, or URLs.
2. Prefer prices shown directly on retailer product pages.
3. Search snippets and historical reports are not proof of
   a current retailer price.
4. Every non-null price must include a source_url pointing
   to the page supporting that price.
5. If no supporting source URL exists, set price to null
   and verification to "unverified".
6. Set verification to "direct_listing" only when the
   retailer page itself explicitly supports that price.
7. Set verification to "third_party_report" when the price
   comes from a third-party tracking or comparison site.
8. Otherwise set verification to "unverified".
9. Do not assume a retailer URL proves a price.
10. If the retailer page shows a different price, do not
    report an older price as a current offer.

RECOMMENDATION RULES:
1. Do not claim a price is verified without supporting evidence.
2. Do not call an offer the best current deal unless the
   compared prices have been confirmed.
3. Explain uncertainty clearly.
4. Keep recommendations concise.

Return ONLY valid JSON matching this structure:

{{
  "product": "Exact product name",
  "currency": "USD",
  "offers": [
    {{
      "retailer": "Retailer name",
      "price": 0.00,
      "url": "Retailer product URL or null",
      "source_url": "Supporting source URL or null",
      "seller_type": "direct_retailer, marketplace, or unknown",
      "verification": "direct_listing, third_party_report, or unverified"
    }}
  ],

  "specifications": {{
  
    "feature_1": "Relevant product specification",
    "feature_2": "Relevant product specification",
    "feature_3": "Relevant product specification",
    "feature_4": "Relevant product specification"
  }},

 
  "recommendation": "Short evidence-based recommendation",


"related_products": [
    {{
        "name": "Exact comparable product model",
        "brand": "Manufacturer name",
        "price": null,
        "category": "Budget, Midrange, or Premium",
        "value_score": 80,
        "score_reason": "Brief explanation of the product's estimated value for money.",
        "key_specs": {{
        "Cores / Threads": "Supported core and thread count",
        "Boost Clock": "Supported maximum boost frequency",
        "Cache": "Supported cache capacity",
        "Power": "Supported power rating"
    }}
    }},
]
}}


COMPARABLE PRODUCT COVERAGE:

Research comparable products as a separate required part
of the response, not as an optional addition to retailer offers.

Aim to return 8 genuine, distinct comparable products
when sufficient research evidence is available.

Include a useful range of models from relevant manufacturers,
including Budget, Midrange, and Premium alternatives
where appropriate.

Prioritize meaningful differences in model, features,
performance class, and intended use.

Do not stop comparable-product discovery just because
5 or 6 retailer offers have already been found.

Every comparable product must include:
name, brand, category, price, value_score, and score_reason.

Use null for unavailable prices.

Do not invent products or assign categories simply to
make the Sankey diagram more visually interesting.

If fewer than 8 supported comparable products are found,
return only those products.
RELATED PRODUCT SPECIFICATIONS:

For each comparable product, research up to four meaningful
technical specifications and return them in key_specs.

For CPUs, prioritize:
- Cores / Threads
- Boost Clock
- Cache
- Power

For other product categories, choose specifications
appropriate to that product type.

Use actual supported specification values, including units.

Do not copy specifications from the requested product
to comparable products.

Do not invent specification values.

If a specification cannot be supported by research,
omit that specification.

Return key_specs as an empty JSON object when no
reliable specifications are available.
RELATED PRODUCT RULES:
1. Find up to eight genuine products comparable to the requested product when supported by research.
2. Include different brands or models where appropriate.
3. Do not invent products or prices.
4. Use null for prices that cannot be supported by research.
5. Assign a value_score from 0 to 100 as a subjective AI assessment, not a measured benchmark.
VALUE SCORE GUIDELINES:
A value_score represents estimated value for money, not raw performance.
Consider the product's capabilities, intended use, and available price evidence.
A more expensive or higher-performance product must not automatically receive
a higher value_score.
When reliable price information is missing, acknowledge the uncertainty
in score_reason and avoid presenting the score as precise or verified.
6. Classify each product as Budget, Midrange, or Premium.
7. If no suitable alternatives are found, return an empty related_products array.
8. For each related product, include a score_reason explaining
   the value_score in one concise sentence.
9. Base the explanation on supported product features and available
   price information. Clearly acknowledge uncertainty when needed.
10. Do not describe value_score as a verified benchmark or objective rating.

For specifications, replace feature_1 through feature_4 with four
meaningful specification names appropriate to the requested product.
Use only supported information. Never return the literal keys
feature_1, feature_2, feature_3, or feature_4.
Use actual JSON null values for missing prices and URLs.
Return JSON only, without Markdown fences.
""",
    )

    raw = response.output_text.strip()

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0].strip()
    print("\n=== AI RESPONSE BEFORE JSON PARSING ===", flush=True)
    print(raw[:2000], flush=True)
    print("=== END AI RESPONSE ===\n", flush=True)
    data = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError("AI returned an invalid research object.")

    offers = data.get("offers", [])

    if not isinstance(offers, list):
        raise ValueError("AI returned an invalid offers list.")

    unique_offers = []
    seen_retailers = set()

    for offer in offers:
        if not isinstance(offer, dict):
            continue

        retailer = offer.get("retailer")

        if not isinstance(retailer, str) or not retailer.strip():
            continue

        retailer_key = " ".join(retailer.lower().split())

        if retailer_key in seen_retailers:
            continue

        seen_retailers.add(retailer_key)
        unique_offers.append(offer)

    validated_offers = []

    for offer in unique_offers[:8]:
        source_url = offer.get("source_url")
        valid_source = False

        if isinstance(source_url, str):
            parsed = urlparse(source_url.strip())

            valid_source = (
                parsed.scheme in ("http", "https")
                and bool(parsed.hostname)
            )

        if not valid_source:
            offer["price"] = None
            offer["verification"] = "unverified"
            offer["source_url"] = None

        elif offer.get("verification") == "direct_listing":
            retailer_url = offer.get("url")
            valid_retailer_url = False

            if isinstance(retailer_url, str):
                parsed_retailer = urlparse(retailer_url.strip())
                parsed_source = urlparse(source_url.strip())

                valid_retailer_url = (
                    parsed_retailer.scheme in ("http", "https")
                    and parsed_retailer.hostname
                    == parsed_source.hostname
                )

            if not valid_retailer_url:
                offer["verification"] = "unverified"

        validated_offers.append(offer)

    data["offers"] = validated_offers


    
    # Attach preliminary verification results to each offer.
    # This does not verify live retailer prices.
    for offer in data.get("offers", []):
        offer["price_check"] = verify_price_source(offer)

        
        # Connect the independent verifier.
        # Network access remains disabled for safety.
        retailer_url = offer.get("url")

        if isinstance(retailer_url, str) and retailer_url.strip():
            
            offer["live_price_check"] = verify_retailer_live_price(
                retailer_url,
                expected_product=data.get("product"),
                allow_network=False
            )

        else:
            offer["live_price_check"] = {
                "status": "no_retailer_url",
                "price": None,
                "currency": None
            }




    return data


if __name__ == "__main__":
    result = research_product("AMD Ryzen 7 9700X")
    print(json.dumps(result, indent=2))
