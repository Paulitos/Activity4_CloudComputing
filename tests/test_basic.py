import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_healthcheck():
    """Test the healthcheck endpoint"""
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_exists():
    """Test that the app is importable"""
    assert app is not None


@pytest.mark.asyncio
async def test_async_example():
    """Example async test"""
    assert True