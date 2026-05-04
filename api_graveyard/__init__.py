import atexit
import signal
import logging
from typing import Optional

from .batcher import Batcher
from . import interceptor

logger = logging.getLogger(__name__)

_batcher: Optional[Batcher] = None


def init(
    api_key: str,
    project_id: str,
    base_url: str = "https://api-graveyard.com",
    service_name: Optional[str] = None,
    environment: Optional[str] = None,
    flush_interval_s: float = 10.0,
    max_batch_size: int = 100,
    debug: bool = False,
) -> None:
    global _batcher

    if _batcher is not None:
        return

    _batcher = Batcher(
        api_key=api_key,
        project_id=project_id,
        base_url=base_url,
        flush_interval_s=flush_interval_s,
        max_batch_size=max_batch_size,
        debug=debug,
    )

    options = {
        "base_url": base_url,
        "service_name": service_name,
        "environment": environment or "production",
    }
    interceptor.patch(_batcher, options)

    atexit.register(shutdown)

    def _sigterm_handler(signum, frame):
        shutdown()

    try:
        signal.signal(signal.SIGTERM, _sigterm_handler)
    except (OSError, ValueError):
        pass


def shutdown() -> None:
    global _batcher

    interceptor.unpatch()
    if _batcher is not None:
        _batcher.shutdown()
        _batcher = None
