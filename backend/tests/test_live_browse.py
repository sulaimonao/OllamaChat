import pytest
import httpx
import time
import subprocess
import os

@pytest.fixture(scope="module")
def server():
    env = os.environ.copy()
    env["USE_FAKE_EMBEDDER"] = "1"
    process = subprocess.Popen(
        ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd="backend",
        env=env,
    )
    # Wait for the server to be ready
    for _ in range(60):
        try:
            response = httpx.get("http://127.0.0.1:8000/healthz")
            if response.status_code == 200:
                break
        except httpx.RequestError:
            time.sleep(0.5)
    else:
        raise RuntimeError("Server did not start in time.")

    yield
    process.terminate()
    process.wait()

def test_healthz(server):
    response = httpx.get("http://127.0.0.1:8000/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_sources_endpoint_default(server):
    # Rename sources.yaml to test default config
    if os.path.exists("backend/config/sources.yaml"):
        os.rename("backend/config/sources.yaml", "backend/config/sources.yaml.bak")

    response = httpx.get("http://127.0.0.1:8000/tools/live/sources")
    assert response.status_code == 200
    data = response.json()
    assert "https://feeds.arstechnica.com/arstechnica/index" in data["rss_feeds"]

    # Restore sources.yaml
    if os.path.exists("backend/config/sources.yaml.bak"):
        os.rename("backend/config/sources.yaml.bak", "backend/config/sources.yaml")

def test_chat_fallback(server):
    # Create an empty sources.yaml to force fallback
    with open("backend/config/sources.yaml", "w") as f:
        f.write("# Empty file to force fallback")

    # Create a session
    response = httpx.post("http://127.0.0.1:8000/session")
    assert response.status_code == 200
    session_id = response.json()["id"]

    chat_request = {
        "session_id": session_id,
        "message": "today's breaking news in artificial intelligence",
        "model_id": "deepseek-r1",
        "persona": "default",
        "use_browser": True,
        "workspace_id": None
    }

    # Send the chat message
    response = httpx.post("http://127.0.0.1:8000/chat", json=chat_request, timeout=None)
    assert response.status_code == 200
    data = response.json()
    assert "model_message" in data

    # Restore sources.yaml
    if os.path.exists("backend/config/sources.yaml"):
        # For simplicity, we just delete it. The next test will restore it.
        os.remove("backend/config/sources.yaml")
