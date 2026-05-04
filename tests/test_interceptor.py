import pytest
import urllib3
from unittest.mock import MagicMock
from api_graveyard import interceptor


@pytest.fixture(autouse=True)
def reset_interceptor():
    yield
    interceptor.unpatch()


def make_batcher():
    b = MagicMock()
    b.push = MagicMock()
    return b


def test_patches_urllib3():
    original = urllib3.HTTPConnectionPool.urlopen
    batcher = make_batcher()
    interceptor.patch(batcher, {"api_key": "agk_test", "project_id": "proj-123"})
    assert urllib3.HTTPConnectionPool.urlopen is not original


def test_restores_after_unpatch():
    original = urllib3.HTTPConnectionPool.urlopen
    batcher = make_batcher()
    interceptor.patch(batcher, {"api_key": "agk_test", "project_id": "proj-123"})
    interceptor.unpatch()
    assert urllib3.HTTPConnectionPool.urlopen is original


def test_does_not_patch_twice():
    batcher = make_batcher()
    interceptor.patch(batcher, {"api_key": "agk_test", "project_id": "proj-123"})
    first_patched = urllib3.HTTPConnectionPool.urlopen
    interceptor.patch(batcher, {"api_key": "agk_test", "project_id": "proj-123"})
    assert urllib3.HTTPConnectionPool.urlopen is first_patched
