from unittest.mock import patch, MagicMock
from api_graveyard.batcher import Batcher


def make_batcher(**kwargs):
    defaults = dict(api_key="agk_test", project_id="proj-123", flush_interval_s=9999, max_batch_size=5, debug=False)
    defaults.update(kwargs)
    return Batcher(**defaults)


def test_queues_without_sending():
    b = make_batcher()
    with patch.object(b, "_send") as mock_send:
        b.push({"ts": "2026-01-01T00:00:00Z", "method": "GET", "url": "https://api.stripe.com"})
        assert len(b._queue) == 1
        mock_send.assert_not_called()
    b.shutdown()


def test_auto_flush_on_max_batch_size():
    b = make_batcher(max_batch_size=3)
    with patch.object(b, "_send") as mock_send:
        for i in range(3):
            b.push({"ts": "2026-01-01T00:00:00Z", "method": "GET", "url": f"https://api.example.com/{i}"})
        mock_send.assert_called_once()
        assert len(b._queue) == 0
    b.shutdown()


def test_flush_sends_correct_payload():
    b = make_batcher()
    event = {"ts": "2026-01-01T00:00:00Z", "method": "POST", "url": "https://api.sendgrid.com", "status": 200, "duration_ms": 42}
    with patch.object(b, "_send") as mock_send:
        b.push(event)
        b.flush()
        mock_send.assert_called_once_with([event])
    b.shutdown()


def test_shutdown_flushes_queue():
    b = make_batcher()
    with patch.object(b, "_send") as mock_send:
        b.push({"ts": "2026-01-01T00:00:00Z", "method": "GET", "url": "https://api.example.com"})
        b.shutdown()
        mock_send.assert_called_once()
        assert len(b._queue) == 0


def test_flush_noop_on_empty_queue():
    b = make_batcher()
    with patch.object(b, "_send") as mock_send:
        b.flush()
        mock_send.assert_not_called()
    b.shutdown()
