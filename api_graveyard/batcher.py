import json
import logging
import threading
import urllib.request
from datetime import datetime, timezone
from typing import List, Optional

from .types import HttpEvent

logger = logging.getLogger(__name__)

_SELF_HOSTNAMES = {"api-graveyard.com", "www.api-graveyard.com"}


class Batcher:
    def __init__(
        self,
        api_key: str,
        project_id: str,
        base_url: str = "https://api-graveyard.com",
        flush_interval_s: float = 10.0,
        max_batch_size: int = 100,
        debug: bool = False,
    ) -> None:
        self._api_key = api_key
        self._project_id = project_id
        self._endpoint = f"{base_url}/api/v1/projects/{project_id}/ingest/events"
        self._max_batch_size = max_batch_size
        self._debug = debug
        self._queue: List[HttpEvent] = []
        self._lock = threading.Lock()
        self._shutdown = False
        self._timer: Optional[threading.Timer] = None
        self._start_timer(flush_interval_s)
        self._flush_interval_s = flush_interval_s

    def _start_timer(self, interval: float) -> None:
        self._timer = threading.Timer(interval, self._timer_flush)
        self._timer.daemon = True
        self._timer.start()

    def _timer_flush(self) -> None:
        if self._shutdown:
            return
        self.flush()
        self._start_timer(self._flush_interval_s)

    def push(self, event: HttpEvent) -> None:
        with self._lock:
            self._queue.append(event)
            should_flush = len(self._queue) >= self._max_batch_size

        if should_flush:
            self.flush()

    def flush(self) -> None:
        with self._lock:
            if not self._queue:
                return
            batch = self._queue[:]
            self._queue.clear()

        self._send(batch)

    def shutdown(self) -> None:
        self._shutdown = True
        if self._timer:
            self._timer.cancel()
        self.flush()

    def _send(self, events: List[HttpEvent]) -> None:
        try:
            body = json.dumps(events).encode("utf-8")
            req = urllib.request.Request(
                self._endpoint,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": self._api_key,
                    "User-Agent": "api-graveyard-python/0.1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if self._debug:
                    logger.debug(f"[api-graveyard] flushed {len(events)} events → {resp.status}")
        except Exception as e:
            if self._debug:
                logger.debug(f"[api-graveyard] flush failed: {e}")
