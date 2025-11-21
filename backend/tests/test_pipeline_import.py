import json
from unittest.mock import Mock
from fastapi.testclient import TestClient
from pathlib import Path
import sys
import os
sys.path.append(str(Path(__file__).resolve().parents[2]))

from main import app
from app.core.dependencies import get_db_manager, get_pipeline_cache, get_services
from ia_auth_sessions import get_current_active_user


def test_force_import_requires_admin(monkeypatch):
    # Mock DB and pipeline cache
    mock_db = Mock()
    # 1st fetch_one (exists) -> pipeline row; 2nd fetch_one (pending) -> no pending interactions
    mock_db.fetch_one.side_effect = [
        {'id': '123', 'name': 'simple_chat'},
        {'cnt': 0}
    ]
    mock_cache = Mock()

    # Mock services
    mock_services = Mock()
    monkeypatch.setattr('app.core.dependencies.get_db_manager', lambda: mock_db)
    monkeypatch.setattr('app.core.dependencies.get_pipeline_cache', lambda: mock_cache)

    # Non-admin user
    def non_admin_user():
        return {'id': 'u1', 'username': 'test', 'is_admin': False}

    app.dependency_overrides = {
        get_db_manager: lambda: mock_db,
        get_pipeline_cache: lambda: mock_cache,
        # override auth dependency
        get_current_active_user: non_admin_user
    }

    client = TestClient(app)

    resp = client.post('/api/pipelines/import-from-filesystem?force=true')
    assert resp.status_code == 403
    app.dependency_overrides = {}


def test_force_import_publishes_event(monkeypatch):
    # Admin user
    def admin_user():
        return {'id': 'u1', 'username': 'ops', 'is_admin': True}

    # Mock DB: a pipeline exists
    mock_db = Mock()
    # 1st fetch_one (exists), 2nd (pending) -> 0
    mock_db.fetch_one.side_effect = [
        {'id': '123', 'name': 'simple_chat'},
        {'cnt': 0}
    ]
    mock_db.execute = Mock()

    # Cache
    mock_cache = Mock()

    # Mock services with a fake redis client
    class FakeRedis:
        async def publish(self, channel, message):
            self.last = (channel, message)

    fake_redis = FakeRedis()
    mock_services = Mock()
    mock_services.redis_client = fake_redis

    # Override dependencies
    app.dependency_overrides = {
        get_db_manager: lambda: mock_db,
        get_pipeline_cache: lambda: mock_cache,
        get_services: lambda: mock_services,
        get_current_active_user: admin_user
    }

    client = TestClient(app)

    resp = client.post('/api/pipelines/import-from-filesystem?force=true')

    # If our handler attempted to publish, fake_redis.last should exist
    assert resp.status_code == 200
    assert hasattr(fake_redis, 'last')

    app.dependency_overrides = {}