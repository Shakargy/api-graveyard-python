# api-graveyard

Official Python collector for [API Graveyard](https://api-graveyard.com) — automatically tracks your outgoing HTTP dependencies, detects risk events, and surfaces zombie APIs before they take down your product.

## Install

```bash
pip install api-graveyard
```

## Quick start

Add one call to the top of your app entry point:

```python
import api_graveyard

api_graveyard.init(
    api_key="agk_your_key_here",
    project_id="your-project-id",
)

# ... rest of your app
```

That's it. Every outgoing HTTP/HTTPS request your app makes is now automatically captured, batched, and sent to API Graveyard in the background.

## Works with

- `requests`
- `httpx` (sync mode)
- `urllib3` directly
- Any library that uses `urllib3` under the hood

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_key` | `str` | **required** | Your `agk_...` API key from the dashboard |
| `project_id` | `str` | **required** | Your project ID from the dashboard |
| `base_url` | `str` | `https://api-graveyard.com` | Override for self-hosted |
| `service_name` | `str` | `None` | Tag events with a service name |
| `environment` | `str` | `"production"` | Tag events with an environment |
| `flush_interval_s` | `float` | `10.0` | How often to flush the event buffer (seconds) |
| `max_batch_size` | `int` | `100` | Max events per batch before forcing a flush |
| `debug` | `bool` | `False` | Log flush activity |

## Django / Flask example

```python
# manage.py or wsgi.py / app factory
import api_graveyard

api_graveyard.init(
    api_key=os.environ["API_GRAVEYARD_KEY"],
    project_id=os.environ["API_GRAVEYARD_PROJECT_ID"],
    service_name="django-backend",
    environment=os.environ.get("DJANGO_ENV", "production"),
)
```

## Graceful shutdown

The collector automatically flushes on process exit. For manual control:

```python
import api_graveyard

api_graveyard.shutdown()
```

## What gets captured

- Method, URL, HTTP status code, response time
- Timestamp of each request
- Service name and environment (if configured)

Requests to `api-graveyard.com` itself are never captured to avoid infinite loops.
Localhost and `127.0.0.1` requests are ignored by default.

## Get your API key

1. Sign up at [api-graveyard.com](https://api-graveyard.com)
2. Create a project
3. Go to **Settings → Integrations** and create an API key

## License

MIT
