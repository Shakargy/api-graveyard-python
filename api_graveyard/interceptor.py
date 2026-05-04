import time
import logging
from datetime import datetime, timezone
from typing import Optional, Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_SELF_HOSTNAMES: Set[str] = {"api-graveyard.com", "www.api-graveyard.com"}
_IGNORED_HOSTNAMES: Set[str] = set()
_patched = False
_original_urlopen = None
_batcher = None
_service_name: Optional[str] = None
_environment: Optional[str] = None


def patch(batcher, options: dict) -> None:
    global _patched, _original_urlopen, _batcher, _service_name, _environment, _IGNORED_HOSTNAMES

    if _patched:
        return

    try:
        import urllib3
    except ImportError:
        logger.warning("[api-graveyard] urllib3 not found — HTTP interception disabled")
        return

    _batcher = batcher
    _service_name = options.get("service_name")
    _environment = options.get("environment", "production")

    from urllib.parse import urlparse as _up
    base_url = options.get("base_url", "https://api-graveyard.com")
    base_host = _up(base_url).hostname or "api-graveyard.com"
    _IGNORED_HOSTNAMES = _SELF_HOSTNAMES | {base_host, "localhost", "127.0.0.1", "::1"}

    _original_urlopen = urllib3.HTTPConnectionPool.urlopen

    def patched_urlopen(pool, method, url, **kwargs):
        scheme = "https" if isinstance(pool, urllib3.HTTPSConnectionPool) else "http"
        port = pool.port
        default_port = 443 if scheme == "https" else 80
        port_str = f":{port}" if port and port != default_port else ""
        full_url = f"{scheme}://{pool.host}{port_str}{url}"

        if pool.host in _IGNORED_HOSTNAMES:
            return _original_urlopen(pool, method, url, **kwargs)

        start = time.monotonic()
        status: Optional[int] = None
        try:
            response = _original_urlopen(pool, method, url, **kwargs)
            status = response.status
            return response
        except Exception:
            raise
        finally:
            event = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "method": method.upper(),
                "url": full_url,
                "duration_ms": int((time.monotonic() - start) * 1000),
            }
            if status is not None:
                event["status"] = status
            if _service_name:
                event["service_name"] = _service_name
            if _environment:
                event["environment"] = _environment
            try:
                _batcher.push(event)
            except Exception:
                pass

    urllib3.HTTPConnectionPool.urlopen = patched_urlopen
    _patched = True


def unpatch() -> None:
    global _patched

    if not _patched or _original_urlopen is None:
        return

    try:
        import urllib3
        urllib3.HTTPConnectionPool.urlopen = _original_urlopen
    except ImportError:
        pass

    _patched = False
