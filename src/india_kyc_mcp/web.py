"""
The hosted version: a remote MCP server any assistant can connect to by URL, plus a small landing page.

    /        landing page: what the server does and how to connect
    /mcp     the MCP endpoint (streamable HTTP, stateless, JSON responses: works on serverless hosts like Vercel)
    /health  {"ok": true}

Stateless means every request is handled on its own, so the server can run on short-lived serverless functions.
"""
from __future__ import annotations

import html
import os

from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
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

TOOLS = [
    ("lookup_ifsc", "Bank, branch, address and UPI / NEFT / RTGS / IMPS support for an IFSC code", "live"),
    ("lookup_pincode", "District, state and post offices for a PIN code", "live"),
    ("find_pincode", "PIN codes for a post office or locality name", "live"),
    ("check_address", "Does this PIN code really belong to this city and state?", "live"),
    ("validate_gstin", "GST number: format, state, the PAN inside it, check digit", "offline"),
    ("validate_pan", "PAN: format and holder type (person, company, firm...)", "offline"),
    ("verify_vendor", "All of the above for one vendor, with cross-checks and a pass / review / fail verdict", "both"),
]


def landing(request: Request) -> HTMLResponse:
    url = f"{PUBLIC_URL}/mcp"
    rows = "".join(
        f"<tr><td><code>{name}</code></td><td>{html.escape(about)}</td><td class='k'>{kind}</td></tr>" for name, about, kind in TOOLS
    )
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>India KYC MCP server</title>
<meta name="description" content="A remote MCP server that lets Claude, Cursor and other AI assistants check Indian IFSC codes, PIN codes, GSTINs and PANs.">
<style>
:root{{--bg:#f6f5f1;--card:#fff;--ink:#17171a;--muted:#66646d;--line:#dedbd2;--accent:#0b6e4f;--code:#1b1b1f;--codeink:#eceae4}}
@media (prefers-color-scheme:dark){{:root{{--bg:#131316;--card:#1b1b1f;--ink:#ecebe7;--muted:#a3a1a8;--line:#303036;--accent:#4cc38a;--code:#0c0c0e}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:880px;margin:0 auto;padding:48px 16px 64px}}h1{{font-size:clamp(30px,5vw,44px);line-height:1.15;margin:0 0 14px;letter-spacing:-.02em}}
.eyebrow{{font:600 12px/1 ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:14px}}
p{{color:var(--muted);margin:0 0 14px}}h2{{font-size:20px;margin:40px 0 12px}}code{{font:13.5px ui-monospace,SFMono-Regular,Menlo,monospace}}
pre{{background:var(--code);color:var(--codeink);padding:14px 16px;border-radius:10px;overflow-x:auto;margin:0 0 12px}}
.url{{display:flex;gap:8px;flex-wrap:wrap;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}}
.url code{{font-size:15px;word-break:break-all;flex:1}}button{{font:inherit;border:1px solid var(--line);background:var(--ink);color:var(--bg);border-radius:8px;padding:6px 12px;cursor:pointer}}
.wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}}table{{width:100%;border-collapse:collapse;font-size:15px}}
td{{padding:10px 14px;border-top:1px solid var(--line);vertical-align:top}}tr:first-child td{{border-top:0}}.k{{color:var(--muted);font-size:13px;white-space:nowrap}}
a{{color:inherit}}footer{{margin-top:48px;color:var(--muted);font-size:14px}}
</style></head><body><main>
<div class="eyebrow">Remote MCP server · free · no API key</div>
<h1>Let your AI assistant check Indian KYC details</h1>
<p>Connect Claude, Cursor or any MCP client to this URL and it can look up IFSC codes and PIN codes live, validate GSTINs
and PANs, and run a one-call vendor onboarding check, instead of guessing.</p>
<div class="url"><code id="u">{url}</code><button onclick="navigator.clipboard&&navigator.clipboard.writeText(document.getElementById('u').textContent);this.textContent='Copied'">Copy</button></div>

<h2>Connect</h2>
<p><b>Claude Code</b></p>
<pre><code>claude mcp add --transport http india-kyc {url}</code></pre>
<p><b>Claude (web and desktop):</b> Settings → Connectors → Add custom connector → paste the URL above.</p>
<p><b>Cursor</b> (<code>.cursor/mcp.json</code>)</p>
<pre><code>{{ "mcpServers": {{ "india-kyc": {{ "url": "{url}" }} }} }}</code></pre>

<h2>Tools</h2>
<div class="wrap"><table>{rows}</table></div>

<h2>Try asking</h2>
<p>“Onboard this vendor: GSTIN 27AAPFU0939F1ZV, PAN AAPFU0939G, IFSC HDFC0000001, address MG Road, Mumbai, Karnataka 560001.”<br>
The vendor check flags all three problems: the PAN doesn't match the one inside the GSTIN, PIN code 560001 is in Bangalore,
and the GST state is Maharashtra.</p>

<footer>Live data from <a href="https://github.com/razorpay/ifsc">Razorpay's IFSC API</a> and India Post.
Format checks prove a number is well-formed, not that it is registered. ·
<a href="{REPO}">Source on GitHub</a> · v{__version__} · built by
<a href="https://www.linkedin.com/in/adityakhetarpal">Aditya Khetarpal</a></footer>
</main></body></html>"""
    return HTMLResponse(page)


def health(request: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "server": "india-kyc", "version": __version__})


# the MCP app already serves /mcp (and runs the session manager in its lifespan); add the two plain pages to it
app.router.routes[:0] = [Route("/", landing), Route("/health", health)]
