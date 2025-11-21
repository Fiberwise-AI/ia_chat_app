import json
import asyncio
import pytest
from unittest.mock import Mock

from app.core.pipeline_cache import PipelineCache


class FakePubSub:
    def __init__(self, messages):
        self._messages = messages

    async def subscribe(self, channel):
        # no-op for fake
        return

    async def listen(self):
        for msg in self._messages:
            await asyncio.sleep(0)  # allow event loop to cycle
            yield msg


class FakeRedis:
    def __init__(self, messages):
        self._messages = messages

    def pubsub(self):
        return FakePubSub(self._messages)


@pytest.mark.asyncio
async def test_pipeline_cache_refreshes_on_redis_message(monkeypatch):
    # Setup pipeline cache and fake DB manager
    cache = PipelineCache()

    # Prepare fake pipeline JSON row
    pipeline_name = 'simple_chat'
    pipeline_json = {
        'name': 'Simple Chat',
        'steps': []
    }

    mock_db = Mock()
    mock_db.fetch_one.return_value = { 'pipeline_json': json.dumps(pipeline_json) }

    # Fake redis message that points to our pipeline
    message = { 'type': 'message', 'data': json.dumps({ 'pipeline': pipeline_name }) }
    fake_redis = FakeRedis([message])

    # Start listener, give it a moment to process
    cache.start_redis_listener(fake_redis, mock_db)

    await asyncio.sleep(0.05)

    # Stop listener
    cache.stop_redis_listener()

    # Assert the pipeline was added to cache
    assert cache.exists(pipeline_name)
    assert cache.get(pipeline_name)['name'] == 'Simple Chat'
