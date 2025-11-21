# tests/test_health.py
from fastapi import status

def test_health_check(test_app):
    """Test the health check endpoint."""
    response = test_app.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}