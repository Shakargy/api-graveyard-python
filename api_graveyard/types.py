from typing import Optional, TypedDict


class HttpEvent(TypedDict, total=False):
    ts: str
    method: str
    url: str
    status: Optional[int]
    duration_ms: Optional[int]
    service_name: Optional[str]
    environment: Optional[str]
