"""
The hosted version: a remote MCP server any assistant can connect to by URL, plus a small landing page.

    /        landing page: what the server does, how to connect, and a box to try one check (page in site/index.html)
    /mcp     the MCP endpoint (streamable HTTP, stateless, JSON responses: works on serverless hosts like Vercel)
    /health  {"ok": true}

Stateless means every request is handled on its own, so the server can run on short-lived serverless functions.
"""
from __future__ import annotations

import html
import os
from pathlib import Path

from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route

from . import __version__
from .server import server

PUBLIC_URL = os.environ.get("PUBLIC_URL", "https://indiakyc.vercel.app")
REPO = "https://github.com/AdityaKhetarpal/india-kyc-mcp"

# The endpoint is public and read-only (every tool only looks things up), so requests from any host are accepted.
app = server.streamable_http_app(
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

# (group, name, what it does, where the answer comes from)
TOOLS = [
    ("Bank", "lookup_ifsc", "Bank, branch, address and UPI / NEFT / RTGS / IMPS support for an IFSC code", "live"),
    ("Address", "lookup_pincode", "District, state and post offices for a PIN code", "live"),
    ("Address", "find_pincode", "PIN codes for a post office or locality name", "live"),
    ("Address", "check_address", "Does this PIN code really belong to this city and state?", "live"),
    ("Tax", "validate_gstin", "GST number: format, state, the PAN inside it, check digit", "offline"),
    ("Tax", "validate_pan", "PAN: format and holder type (person, company, firm...)", "offline"),
    ("All three", "verify_vendor", "Every check above for one vendor, cross-checked, with a pass / review / fail verdict", "both"),
]
SOURCE = {"live": "Live API", "offline": "Offline", "both": "Live + offline"}

# The page and its files live in site/ next to this module. They are read once, when the server starts.
SITE = Path(__file__).with_name("site")
OK_ICON = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.2 6.3 4.8 8.8 9.8 3.4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
NO_ICON = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M6 2.2V6.6" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"/><circle cx="6" cy="9.4" r="1.15" fill="currentColor"/></svg>'
FILES = {
    "/icon.svg": "image/svg+xml",
    "/favicon.ico": "image/x-icon",
    "/apple-touch-icon.png": "image/png",
    "/og.png": "image/png",
}
FONTS = sorted(p.name for p in (SITE / "fonts").glob("*.woff2"))


def tools_html() -> str:
    groups: dict[str, list[str]] = {}
    for group, name, about, kind in TOOLS:
        groups.setdefault(group, []).append(
            f"<div class='tool'><code>{name}</code><span>{html.escape(about)}</span><b class='chip {kind}'>{SOURCE[kind]}</b></div>"
        )
    return "".join(f"<div class='group'><h3>{group}</h3>{''.join(rows)}</div>" for group, rows in groups.items())


def build_page() -> str:
    page = (SITE / "index.html").read_text(encoding="utf-8")
    for key, value in {
        "{{MCP_URL}}": f"{PUBLIC_URL}/mcp",
        "{{PUBLIC_URL}}": PUBLIC_URL,
        "{{REPO}}": REPO,
        "{{VERSION}}": __version__,
        "{{TOOLS}}": tools_html(),
        "{{OK}}": OK_ICON,
        "{{NO}}": NO_ICON,
    }.items():
        page = page.replace(key, value)
    return page


PAGE = build_page()
CACHE = {"cache-control": "public, max-age=86400"}


def landing(request: Request) -> HTMLResponse:
    return HTMLResponse(PAGE, headers={"cache-control": "public, max-age=300"})


def static_file(request: Request) -> Response:
    path = request.url.path
    return Response((SITE / path.lstrip("/")).read_bytes(), media_type=FILES[path], headers=CACHE)


def font(request: Request) -> Response:
    name = request.path_params["name"]
    if name not in FONTS:  # only the files that ship with the site, nothing else from disk
        return Response(status_code=404)
    return Response((SITE / "fonts" / name).read_bytes(), media_type="font/woff2", headers={"cache-control": "public, max-age=31536000, immutable"})


def health(request: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "server": "india-kyc", "version": __version__})


# the MCP app already serves /mcp (and runs the session manager in its lifespan); add the page, icons and fonts to it
app.router.routes[:0] = [
    Route("/", landing),
    Route("/health", health),
    *(Route(path, static_file) for path in FILES),
    Route("/fonts/{name}", font),
]
