
from urllib.parse import urlparse
import ipaddress
import socket
from decimal import Decimal, InvalidOperation

def verify_price_source(offer):
    """
    Perform preliminary checks on a retailer offer.

    This does NOT confirm the live retailer price.
    """

    retailer = offer.get("retailer", "Unknown")
    price = offer.get("price")
    source_url = offer.get("source_url")

    result = {
        "retailer": retailer,
        "reported_price": price,
        "verified_price": None,
        "status": "not_verified",
        "message": "Live retailer price has not been checked."
    }

    if not isinstance(price, (int, float)) or isinstance(price, bool) or price <= 0:
        result["status"] = "invalid_price"
        result["message"] = "No valid reported price."
        return result

    if not isinstance(source_url, str):
        result["status"] = "missing_source"
        result["message"] = "No supporting source URL."
        return result

    parsed = urlparse(source_url)

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        result["status"] = "invalid_source"
        result["message"] = "Invalid source URL."
        return result

    result["status"] = "source_available"
    result["message"] = (
        "Source URL is present, but the live price "
        "has not been independently verified."
    )

    return result


import json
import requests
from bs4 import BeautifulSoup



def fetch_retailer_price(
    url,
    expected_product=None,
    expected_sku=None,
    allow_network=False
):
    """
    Look for a candidate product price in retailer page data.

    This does not independently verify the live price,
    product identity, or seller.
    """

    result = {
        "status": "not_verified",
        "price": None,
        "currency": None,
        "message": "No supported product price found."
    }

    if not isinstance(url, str):
        result["message"] = "Retailer URL is not approved."
        return result

    allowed_domains = (
        "bestbuy.com",
        "bhphotovideo.com",
        "newegg.com",
        "microcenter.com",
        "walmart.com",
        "target.com",
        "amazon.com",
    )

    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError:
        result["message"] = "Invalid retailer URL."
        return result

    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or not any(
            hostname == domain
            or hostname.endswith("." + domain)
            for domain in allowed_domains
        )
    ):
        result["message"] = "Retailer URL is not approved."
        return result

    if not allow_network:
        result["status"] = "network_disabled"
        result["message"] = (
            "Live retailer requests are disabled "
            "until connection-level safety checks are implemented."
        )
        return result

    
    try:
        
        with requests.Session() as session:
            session.trust_env = False

            response = session.get(
                url,
                timeout=10,
                allow_redirects=False,
                stream=True,
                headers={
                    "User-Agent": "PriceScoutAI/0.1"
                }
            )

            
            response.raise_for_status()

            # Reject redirects before reading their content.
            if 300 <= response.status_code < 400:
                response.close()
                result["status"] = "redirect_not_followed"
                result["message"] = "Retailer redirected the request."
                return result

            try:
                limited = read_limited_response(response)

            except requests.RequestException:
                result["status"] = "request_failed"
                result["message"] = "Retailer response could not be read."
                return result
            finally:
                response.close()




        response.raise_for_status()

    except requests.RequestException as error:

        if "response" in locals():
            response.close()

        if (
            isinstance(error, requests.HTTPError)
            and error.response is not None
            and error.response.status_code in (401, 403)
        ):
            result["status"] = "access_restricted"
            result["message"] = (
                "Retailer restricts automated page access. "
                "Live price could not be verified."
            )
        else:
            result["status"] = "request_failed"
            result["message"] = (
                f"Retailer request failed: "
                f"{type(error).__name__}"
            )

        return result





    if limited["status"] == "response_too_large":
        result["status"] = "response_too_large"
        result["message"] = (
            "Retailer response exceeds the 2 MB limit."
        )
        return result

    html = limited["content"].decode(
        response.encoding or "utf-8",
        errors="replace"
    )

    extracted = extract_product_price(html)


    


    if extracted["status"] == "price_detected" and expected_product is not None:
        identity = verify_product_identity(
            expected_product,
            extracted["product"],
            expected_sku,
            extracted["sku"]
        )

        if not identity["matched"]:
            result["status"] = identity["status"]
            result["message"] = (
                "Product identity did not match. "
                "Candidate price rejected."
            )
            return result

    if extracted["status"] == "price_detected":

        result.update({
            "status": "price_detected",
            "price": extracted["price"],
            "currency": extracted["currency"],
            "product": extracted["product"],
            "sku": extracted["sku"],
            "message": (
                "Candidate price found in retailer page data. "
                "Exact product and seller match not yet confirmed."
            )
        })

    return result


def extract_product_price(html):
    """
    Extract a candidate product price from JSON-LD HTML.

    Does not independently verify the retailer or price.
    """
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):
        try:
            data = json.loads(script.string or script.get_text())
        except (json.JSONDecodeError, TypeError):
            continue

        items = data if isinstance(data, list) else [data]

        for item in items:
            if not isinstance(item, dict):
                continue

            if item.get("@type") != "Product":
                continue

            offers = item.get("offers", [])
            if isinstance(offers, dict):
                offers = [offers]

            for offer in offers:
                if not isinstance(offer, dict):
                    continue

                
                try:
                    raw_price = offer.get("price")
                    decimal_price = Decimal(str(raw_price).strip())

                    if decimal_price.as_tuple().exponent < -2:
                        continue

                    price = float(decimal_price)

                except (TypeError, ValueError, InvalidOperation):
                    continue


                if (
                    not 0 < price < float("inf")
                    or offer.get("priceCurrency") != "USD"
                ):
                    continue

                return {
                    "status": "price_detected",
                    "product": item.get("name"),
                    "sku": item.get("sku"),
                    "price": price,
                    "currency": "USD"
                }

    return {
        "status": "not_verified",
        "product": None,
        "sku": None,
        "price": None,
        "currency": None
    }

import re


def normalize_product_name(name):
    """Normalize a product name for comparison."""
    if not isinstance(name, str):
        return ""

    return " ".join(
        re.findall(r"[a-z0-9]+", name.lower())
    )


def check_product_match(expected_product, detected_product):
    """
    Check whether normalized product names match exactly.

    This is a preliminary name check, not full SKU
    or seller verification.
    """
    expected = normalize_product_name(expected_product)
    detected = normalize_product_name(detected_product)

    if not expected or not detected:
        return {
            "matched": False,
            "status": "missing_product_name"
        }

    if expected == detected:
        return {
            "matched": True,
            "status": "product_name_matched"
        }

    return {
        "matched": False,
        "status": "product_mismatch"
    }

def check_product_price(html, expected_product):
    """
    Extract a candidate price and check the product name.

    A name match does not independently verify the
    seller, SKU, or current retailer price.
    """

    extracted = extract_product_price(html)

    if extracted["status"] != "price_detected":
        return {
            "status": "not_verified",
            "price": None,
            "message": "No supported product price found."
        }

    match = check_product_match(
        expected_product,
        extracted["product"]
    )

    if not match["matched"]:
        return {
            "status": "product_mismatch",
            "price": None,
            "message": (
                "Detected product does not match "
                "the requested product."
            )
        }

    return {
        "status": "product_name_matched",
        "price": extracted["price"],
        "currency": extracted["currency"],
        "product": extracted["product"],
        "sku": extracted["sku"],
        "message": (
            "Product name matches and a candidate price "
            "was detected. Seller and live price are "
            "not yet independently verified."
        )
    }

def check_sku_match(expected_sku, detected_sku):
    """
    Compare product SKU identifiers.

    Both identifiers must be present for a match.
    """

    if not isinstance(expected_sku, str) or not isinstance(detected_sku, str):
        return {
            "matched": False,
            "status": "missing_sku"
        }

    expected = expected_sku.strip().upper()
    detected = detected_sku.strip().upper()

    if not expected or not detected:
        return {
            "matched": False,
            "status": "missing_sku"
        }

    if expected == detected:
        return {
            "matched": True,
            "status": "sku_matched"
        }

    return {
        "matched": False,
        "status": "sku_mismatch"
    }

def verify_product_identity(
    expected_name,
    detected_name,
    expected_sku=None,
    detected_sku=None
):
    """
    Check product identity using name and SKU.

    This does not verify a live retailer price.
    """

    name_result = check_product_match(
        expected_name,
        detected_name
    )

    if not name_result["matched"]:
        return {
            "matched": False,
            "status": "product_mismatch"
        }

    if expected_sku is not None:
        sku_result = check_sku_match(
            expected_sku,
            detected_sku
        )

        if not sku_result["matched"]:
            return {
                "matched": False,
                "status": sku_result["status"]
            }

        return {
            "matched": True,
            "status": "name_and_sku_matched"
        }

    return {
        "matched": True,
        "status": "name_matched_sku_not_checked"
    }

def check_verified_product_price(
    html,
    expected_product,
    expected_sku=None
):
    """
    Extract a candidate price and check product identity.

    Does not independently verify the current
    retailer price or seller.
    """

    extracted = extract_product_price(html)

    if extracted["status"] != "price_detected":
        return {
            "status": "not_verified",
            "price": None
        }

    identity = verify_product_identity(
        expected_product,
        extracted["product"],
        expected_sku,
        extracted["sku"]
    )

    if not identity["matched"]:
        return {
            "status": identity["status"],
            "price": None
        }

    return {
        "status": identity["status"],
        "price": extracted["price"],
        "currency": extracted["currency"],
        "product": extracted["product"],
        "sku": extracted["sku"],
        "message": (
            "Product identity matched. Candidate price "
            "detected, but live retailer price and seller "
            "are not independently verified."
        )
    }

def check_public_dns(hostname):
    """
    Check whether a hostname resolves only to global IPs.

    This is a preliminary DNS check, not complete
    protection against DNS rebinding.
    """

    try:
        addresses = socket.getaddrinfo(
            hostname,
            443,
            type=socket.SOCK_STREAM
        )
    except (socket.gaierror, OSError, ValueError, TypeError):
        return {
            "safe": False,
            "status": "dns_lookup_failed"
        }

    if not addresses:
        return {
            "safe": False,
            "status": "dns_lookup_failed"
        }

    for address in addresses:
        ip_text = address[4][0]

        try:
            ip = ipaddress.ip_address(ip_text)
        except ValueError:
            return {
                "safe": False,
                "status": "invalid_ip"
            }

        if not ip.is_global:
            return {
                "safe": False,
                "status": "non_public_ip"
            }

    return {
        "safe": True,
        "status": "public_dns"
    }

def read_limited_response(response, max_bytes=2 * 1024 * 1024):
    """
    Read an HTTP response in chunks with a size limit.

    The response should be requested with stream=True.
    """

    collected = bytearray()

    for chunk in response.iter_content(chunk_size=8192):
        if not chunk:
            continue

        if len(collected) + len(chunk) > max_bytes:
            return {
                "status": "response_too_large",
                "content": None
            }

        collected.extend(chunk)

    return {
        "status": "response_within_limit",
        "content": bytes(collected)
    }

def verify_downloaded_retailer_html(html, expected_product, expected_sku=None):
    """
    Verify a retailer price from HTML that has already
    been downloaded.

    This function makes no network requests.
    """
    extracted = extract_product_price(html)

    if extracted.get("status") != "price_detected":
        return {
            "status": "price_not_detected",
            "price": None,
            "currency": None
        }

    identity = verify_product_identity(
        expected_product,
        extracted.get("product"),
        expected_sku=expected_sku,
        detected_sku=extracted.get("sku")
    )

    if not identity.get("matched"):
        return {
            "status": "product_mismatch",
            "price": None,
            "currency": None
        }

    return {
        "status": "price_extracted",
        "price": extracted.get("price"),
        "currency": extracted.get("currency")
    }

def verify_retailer_live_price(
    url,
    expected_product,
    expected_sku=None,
    allow_network=False
):
    """
    Independently check a retailer price.

    Network access is disabled by default.
    """
    if not allow_network:
        return {
            "status": "network_disabled",
            "price": None,
            "currency": None
        }

    from safe_retailer_connection import download_retailer_page

    try:
        html = download_retailer_page(url)

        return verify_downloaded_retailer_html(
            html,
            expected_product,
            expected_sku=expected_sku
        )

    except ValueError as error:
        if "HTTP 403" in str(error):
            return {
                "status": "retailer_access_blocked",
                "price": None,
                "currency": None
            }

        return {
            "status": "verification_failed",
            "price": None,
            "currency": None
        }

    except Exception:
        return {
            "status": "verification_failed",
            "price": None,
            "currency": None
        }
