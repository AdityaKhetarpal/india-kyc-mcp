"""The hosted version (what runs on Vercel): landing page, health check and the MCP endpoint over HTTP."""
import pytest
from starlette.testclient import TestClient

from india_kyc_mcp.web import app

HEADERS = {"content-type": "application/json", "accept": "application/json, text/event-stream"}


@pytest.fixture(scope="module")
def client():
    # one app start for the whole file, like one serverless instance (the MCP session manager starts once per app)
    with TestClient(app, follow_redirects=False) as c:
        yield c


def rpc(client, method, params=None, id_=1):
    body = {"jsonrpc": "2.0", "id": id_, "method": method, "params": params or {}}
    response = client.post("/mcp", json=body, headers=HEADERS)
    assert response.status_code == 200, response.text
    return response.json()


def test_landing_and_health(client):
    page = client.get("/")
    assert page.status_code == 200 and "/mcp" in page.text and "verify_vendor" in page.text
    assert client.get("/health").json()["ok"] is True


def test_mcp_over_http_without_a_session(client):
    # stateless: each request stands alone, no initialize handshake or session id needed (serverless-friendly)
    tools = rpc(client, "tools/list")["result"]["tools"]
    assert len(tools) == 7
    result = rpc(client, "tools/call", {"name": "validate_gstin", "arguments": {"gstin": "27AAPFU0939F1ZV"}})
    assert '"valid": true' in result["result"]["content"][0]["text"]


def test_endpoint_is_exactly_mcp_no_redirect(client):
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}, headers=HEADERS)
    assert r.status_code == 200


def test_logo_icons_and_fonts(client):
    page = client.get("/").text
    assert 'href="/icon.svg"' in page and "/og.png" in page and "{{" not in page  # every placeholder filled
    files = {"/icon.svg": "image/svg+xml", "/favicon.ico": "image/x-icon", "/apple-touch-icon.png": "image/png"}
    files["/og.png"] = "image/png"
    for path, kind in files.items():
        r = client.get(path)
        assert r.status_code == 200 and r.headers["content-type"].startswith(kind) and r.content, path
    assert client.get("/fonts/ibm-plex-sans-latin-400-normal.woff2").headers["content-type"] == "font/woff2"
    # only the bundled font files are served, nothing else from disk
    assert client.get("/fonts/..%2F..%2Fweb.py").status_code == 404
    assert client.get("/fonts/OFL.txt").status_code == 404
