from fastapi.testclient import TestClient
from unittest.mock import Mock
import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from main import app
from app.core.dependencies import get_db_manager, get_pipeline_cache, get_services
from ia_auth_sessions import get_current_active_user


def test_revert_requires_admin(monkeypatch):
    mock_db = Mock()
    mock_db.fetch_one.return_value = None
    mock_cache = Mock()

    app.dependency_overrides = {
        get_db_manager: lambda: mock_db,
        get_pipeline_cache: lambda: mock_cache,
        get_current_active_user: lambda: {'id': 'u1', 'is_admin': False}
    }

    client = TestClient(app)
    resp = client.post('/api/pipelines/simple_chat/revert')
    assert resp.status_code == 403

    app.dependency_overrides = {}


def test_revert_success_publishes(monkeypatch):
    # Admin
    app.dependency_overrides = {
        get_current_active_user: lambda: {'id': 'ops', 'is_admin': True}
    }

    mock_db = Mock()
    # First call: fetch version, second call: pending count
    mock_db.fetch_one.side_effect = [
        {'id': 'v1', 'pipeline_id': '123', 'pipeline_name': 'simple_chat', 'pipeline_json': json.dumps({'name':'simple_chat','steps':[]})},
        {'cnt': 0}
    ]

    mock_cache = Mock()
    mock_services = Mock()
    fake_redis = Mock()
    # async publish returns coroutine - but in tests just ensure method called
    async def fake_publish(channel, msg):
        fake_redis.last = (channel, msg)
    mock_services.redis_client = Mock()
    mock_services.redis_client.publish = fake_publish

    app.dependency_overrides.update({
        get_db_manager: lambda: mock_db,
        get_pipeline_cache: lambda: mock_cache,
        get_services: lambda: mock_services
    })

    client = TestClient(app)
    resp = client.post('/api/pipelines/simple_chat/revert')
    assert resp.status_code == 200
    assert 'reverted' in resp.json()['message']

    app.dependency_overrides = {}