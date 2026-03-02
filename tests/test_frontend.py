from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_served():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Community Briefing" in response.text


def test_static_assets_served():
    with TestClient(app) as client:
        css = client.get("/static/app.css")
        js = client.get("/static/app.js")
        assert css.status_code == 200
        assert js.status_code == 200
        assert "text/css" in css.headers.get("content-type", "")
        assert "javascript" in js.headers.get("content-type", "")

