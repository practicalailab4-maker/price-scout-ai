import time
import ipaddress
import socket
import urllib3

def resolve_public_addresses(hostname):
    """
    Resolve a hostname and return only public IP addresses.

    Reject the entire hostname if any resolved address is
    private, loopback, reserved, or otherwise non-global.
    """
    addresses = set()

    results = socket.getaddrinfo(
        hostname,
        443,
        type=socket.SOCK_STREAM
    )

    for result in results:
        address = result[4][0]
        ip = ipaddress.ip_address(address)

        if not ip.is_global:
            raise ValueError(
                "Retailer hostname resolved to a non-public IP."
            )

        addresses.add(address)

    if not addresses:
        raise ValueError("No public retailer IP addresses found.")

    
    return sorted(
        addresses,
        key=lambda address: (
            ipaddress.ip_address(address).version != 4,
            address
        )
    )


def fetch_pinned_https(hostname, ip_address, path, timeout_seconds=10):
    """
    Make an HTTPS request to a specific public IP while
    verifying the certificate against the original hostname.

    Returns the response object.
    """
    import urllib3

    ip = ipaddress.ip_address(ip_address)

    if not ip.is_global:
        raise ValueError("Connection target must be a public IP.")

    if not path.startswith("/") or path.startswith("//"):
        raise ValueError("Invalid request path.")

    pool = urllib3.HTTPSConnectionPool(
        host=ip_address,
        port=443,
        server_hostname=hostname,
        assert_hostname=hostname,
        cert_reqs="CERT_REQUIRED",
        maxsize=1,
        retries=False,
        timeout=urllib3.Timeout(
        connect=min(5.0, timeout_seconds),
        read=timeout_seconds
),
    )

    try:


        response = pool.urlopen(
            "GET",
            path,
            
            headers={
                "Host": hostname,
                "User-Agent": "PriceScoutAI/0.1",
                "Accept": "text/html",
                "Accept-Encoding": "identity"
            },

            redirect=False,
            preload_content=False,
        )

        if 300 <= response.status < 400:
            response.release_conn()
            response.close()
            raise ValueError(
                "Retailer redirected the request. Redirects are not followed."
            )


        if response.status < 200 or response.status >= 300:
            response.release_conn()
            response.close()
            raise ValueError(
                f"Retailer returned HTTP {response.status}."
            )


        return response, pool

    except Exception:
        pool.close()
        raise

def read_and_close_response(response, pool, max_bytes=2 * 1024 * 1024):
    """
    Read a limited amount of response data and always
    release the HTTPS response and connection pool.
    """
    try:
        content_length = response.headers.get("Content-Length")

        if content_length is not None:
            if int(content_length) > max_bytes:
                raise ValueError("Retailer response exceeds size limit.")

        chunks = []
        total = 0

        for chunk in response.stream(8192, decode_content=True):
            total += len(chunk)

            if total > max_bytes:
                raise ValueError("Retailer response exceeds size limit.")

            chunks.append(chunk)

        return b"".join(chunks)

    finally:
        response.release_conn()
        response.close()
        pool.close()


def prepare_retailer_url(url):
    """
    Validate a retailer URL and return its hostname
    and request path without making a network request.
    """
    from urllib.parse import urlsplit

    allowed_domains = (
        "bestbuy.com",
        "bhphotovideo.com",
        "newegg.com",
        "microcenter.com",
        "walmart.com",
        "target.com",
        "amazon.com",
    )

    if not isinstance(url, str):
        raise ValueError("Retailer URL must be a string.")

    try:
        parsed = urlsplit(url)
        hostname = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError:
        raise ValueError("Invalid retailer URL.")

    if (
        parsed.scheme != "https"
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or not any(
            hostname == domain
            or hostname.endswith("." + domain)
            for domain in allowed_domains
        )
    ):
        raise ValueError("Retailer URL is not approved.")

    path = parsed.path or "/"

   
    if parsed.query:
        path += "?" + parsed.query

    if any(ord(char) < 32 or ord(char) == 127 for char in path):
        raise ValueError("Retailer URL contains invalid control characters.")

    if path.startswith("//"):
        raise ValueError("Invalid retailer request path.")

    return hostname, path

def download_retailer_page(url):
    """
    Download a retailer page using a public-IP-pinned
    HTTPS connection with a response-size limit.
    """
    hostname, path = prepare_retailer_url(url)

    
    addresses = resolve_public_addresses(hostname)

    response = None
    pool = None
    last_error = None

    
    deadline = time.monotonic() + 15

    for ip_address in addresses[:3]:
        if time.monotonic() >= deadline:
            raise TimeoutError(
                "Retailer connection deadline exceeded."
            )

        try:
            
            remaining_seconds = deadline - time.monotonic()

            if remaining_seconds <= 0:
                raise TimeoutError(
                    "Retailer connection deadline exceeded."
                )

            response, pool = fetch_pinned_https(
                hostname,
                ip_address,
                path,
                timeout_seconds=remaining_seconds
            )

            break
        
        except (
            urllib3.exceptions.ConnectTimeoutError,
            urllib3.exceptions.NewConnectionError,
            urllib3.exceptions.NameResolutionError,
            ConnectionError,
            TimeoutError,
            OSError
        ) as error:
            last_error = error


    if response is None:
        raise ConnectionError(
            "All validated retailer IP addresses failed."
        ) from last_error


    content_type = response.headers.get(
        "Content-Type", ""
    ).lower()

    if "text/html" not in content_type:
        response.close()
        pool.close()
        raise ValueError(
            "Retailer response is not an HTML page."
        )

    content_encoding = response.headers.get(
        "Content-Encoding", "identity"
    ).strip().lower()

    if content_encoding not in ("", "identity"):
        response.close()
        pool.close()
        raise ValueError(
            "Retailer returned unsupported compressed content."
        )


    content = read_and_close_response(response, pool)


    return content.decode("utf-8", errors="replace")

