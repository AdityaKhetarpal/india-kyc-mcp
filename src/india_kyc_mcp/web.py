"""
The hosted version: a remote MCP server any assistant can connect to by URL, plus a small landing page.

    /             landing page: what the server does, how to connect, and a box to try one check (page in site/index.html)
    /mcp          the MCP endpoint (streamable HTTP, stateless, JSON responses: works on serverless hosts like Vercel)
    /health       {"ok": true}
    /robots.txt   every crawler may read the page (search engines and AI search bots), /mcp is skipped
    /sitemap.xml  the page list for search engines
    /llms.txt     a short plain-text summary for AI tools (an experiment: no search engine has said it uses it)

Stateless means every request is handled on its own, so the server can run on short-lived serverless functions.
"""
from __future__ import annotations

import html
import json
import os
from pathlib import Path

from mcp.server.transport_security import TransportSecuritySettings
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
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


# ---- Who built it, and his other projects (the same on every one of Aditya's sites) ----
HUB_URL = "https://adityakhetarpal.vercel.app"  # Aditya's portfolio page; change here if it moves
AUTHOR = {
    "name": "Aditya Khetarpal",
    "job_title": "Data Analyst and AI Builder",
    "location": "Delhi, India",
    "same_as": [
        "https://www.linkedin.com/in/adityakhetarpal",
        "https://github.com/AdityaKhetarpal",
        "https://degenfinds.substack.com",
        "https://x.com/0xAditya_k",
    ],
}
OTHER_PROJECTS = [
    ("Evalgate", "open-source LLM eval harness that blocks regressions in CI", "https://evalgate-ak.vercel.app"),
    ("UPI Merchant Discount Rate (MDR) Impact Simulator", "what India's 0.4% UPI fee costs a payment and raises in a year", "https://upi-mdr-simulator.vercel.app"),
    ("AI Data Analyst Agent", "read-only, self-correcting text-to-SQL agent", "https://ai-data-analyst-agent-ten.vercel.app"),
]

# ---- Questions people search, with short direct answers (shown on the page and repeated as FAQPage data) ----
FAQ = [
    ("What is an MCP server?",
     "MCP (Model Context Protocol) is an open standard that lets AI assistants such as Claude and Cursor call outside tools. "
     "An MCP server offers those tools. This one gives an assistant seven tools for checking Indian bank, address and tax details."),
    ("How do I add India KYC MCP to Claude or Cursor?",
     f"Give your assistant the URL {PUBLIC_URL}/mcp. In Claude Code run: claude mcp add --transport http india-kyc {PUBLIC_URL}/mcp. "
     "In the Claude app use Settings, Connectors, Add custom connector. In Cursor add it to .cursor/mcp.json. Nothing to install and no sign-up."),
    ("How does it validate a GSTIN?",
     "A GSTIN has 15 characters: a 2-digit state code, the holder's 10-character PAN, an entity character, the letter Z and a check character. "
     "The server checks the format and the state code, pulls out the PAN and its holder type, and recomputes the check character "
     "(a weighted mod-36 sum of the first 14 characters), which catches most typos."),
    ("Does it confirm that a GSTIN or PAN is registered and active?",
     "No. GSTIN and PAN checks are offline format and check-digit checks: they prove a number is well-formed, not that it is registered. "
     "For registration status, check the GST portal or the Income Tax Department."),
    ("Where do the IFSC and PIN code answers come from?",
     "IFSC lookups use Razorpay's free IFSC API, which is built from RBI data, and return the bank, branch, address and UPI, NEFT, RTGS and IMPS support. "
     "PIN code lookups use India Post's directory at api.postalpincode.in. A weekly automated check calls both through a real MCP session."),
    ("What does verify_vendor check?",
     "In one call it checks the GSTIN, the PAN, the bank's IFSC and the address, then cross-checks them the way a finance team does by hand: "
     "is the PAN the one inside the GSTIN, is the PIN code in the stated city, does the GST state match the address. It returns pass, review or fail."),
    ("Does the server store the details I check?",
     "The server has no database and no sessions: every tool only looks things up, and each request is handled on its own and then forgotten."),
    ("Is it free?",
     "Yes. The hosted server needs no API key, and the code is open source under the MIT licence, so you can also run it on your own machine."),
]


def faq_html() -> str:
    items = "".join(f"<div class='faq-item'><h3>{html.escape(q)}</h3><p>{html.escape(a)}</p></div>" for q, a in FAQ)
    return items


def more_projects_html() -> str:
    links = "".join(f"<li><a href='{url}'>{html.escape(name)}</a>: {html.escape(text)}</li>" for name, text, url in OTHER_PROJECTS)
    return f"<ul class='more'>{links}</ul>"


def jsonld() -> str:
    """Structured data for search engines and AI assistants: the software, the site, the author and the FAQ."""
    person_id = f"{HUB_URL}/#person"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SoftwareApplication",
                "@id": f"{PUBLIC_URL}/#software",
                "name": "India KYC MCP",
                "alternateName": "India KYC MCP server",
                "url": f"{PUBLIC_URL}/",
                "description": "A remote MCP server that lets Claude, Cursor and other AI assistants check Indian IFSC codes, PIN codes, GSTINs and PANs, "
                "and run a full vendor onboarding check in one call.",
                "applicationCategory": "DeveloperApplication",
                "applicationSubCategory": "Model Context Protocol (MCP) server",
                "operatingSystem": "Any (remote MCP over HTTP), or Python 3.10+ locally",
                "softwareVersion": __version__,
                "license": "https://opensource.org/licenses/MIT",
                "isAccessibleForFree": True,
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "INR"},
                "codeRepository": REPO,
                "downloadUrl": REPO,
                "programmingLanguage": "Python",
                "featureList": [f"{name}: {about}" for _, name, about, _ in TOOLS],
                "author": {"@id": person_id},
            },
            {"@type": "WebSite", "@id": f"{PUBLIC_URL}/#website", "url": f"{PUBLIC_URL}/", "name": "India KYC MCP", "author": {"@id": person_id}},
            {
                "@type": "Person",
                "@id": person_id,
                "name": AUTHOR["name"],
                "jobTitle": AUTHOR["job_title"],
                "url": HUB_URL,
                "address": {"@type": "PostalAddress", "addressLocality": "Delhi", "addressCountry": "IN"},
                "sameAs": AUTHOR["same_as"],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ],
            },
        ],
    }
    # "<" escaped so the data can never close the script tag
    return json.dumps(graph, ensure_ascii=False).replace("<", "\\u003c")


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
        "{{FAQ}}": faq_html(),
        "{{JSONLD}}": jsonld(),
        "{{HUB_URL}}": HUB_URL,
        "{{MORE_PROJECTS}}": more_projects_html(),
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


# ---- Files for search engines and AI tools ----
ROBOTS = f"""User-Agent: *
Allow: /
Disallow: /mcp

Sitemap: {PUBLIC_URL}/sitemap.xml
"""

SITEMAP = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>{PUBLIC_URL}/</loc><changefreq>monthly</changefreq><priority>1</priority></url>
</urlset>
"""

LLMS = f"""# India KYC MCP

> A free remote MCP server that lets Claude, Cursor and other AI assistants check Indian bank, address and tax details: IFSC codes (live, Razorpay's IFSC API from RBI data), PIN codes (live, India Post), GSTINs and PANs (offline format and check-digit checks), and a one-call vendor onboarding check with a pass / review / fail verdict. No API key. Open source (MIT). Built by {AUTHOR["name"]} ({HUB_URL}).

Connect: {PUBLIC_URL}/mcp (streamable HTTP, stateless). Claude Code: claude mcp add --transport http india-kyc {PUBLIC_URL}/mcp

Tools:
{chr(10).join(f"- {name}: {about}" for _, name, about, _ in TOOLS)}

Limits: GSTIN and PAN checks prove a number is well-formed, not that it is registered.

## Links
- [Landing page with a live demo]({PUBLIC_URL}/)
- [Source code and README]({REPO})
"""


def robots(request: Request) -> PlainTextResponse:
    return PlainTextResponse(ROBOTS, headers=CACHE)


def sitemap(request: Request) -> Response:
    return Response(SITEMAP, media_type="application/xml", headers=CACHE)


def llms(request: Request) -> PlainTextResponse:
    return PlainTextResponse(LLMS, headers=CACHE)


# A real page for addresses that don't exist (still status 404, and noindex so it never shows in search).
# The MCP endpoint keeps its plain answers, so assistants see exactly what they did before.
NOT_FOUND = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Page not found · India KYC MCP</title><meta name="robots" content="noindex"><link rel="icon" href="/icon.svg" type="image/svg+xml">
<style>body{{font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;max-width:640px;margin:12vh auto;padding:0 20px;color:#10201e;background:#f7f6f1}}a{{color:#0b3b38}}</style></head>
<body><h1>This page doesn't exist.</h1><p>The address may be mistyped. Try:</p>
<ul><li><a href="/">India KYC MCP: the server, how to connect and a live demo</a></li><li><a href="{REPO}">Source code on GitHub</a></li>
<li><a href="{HUB_URL}">Other projects by {AUTHOR["name"]}</a></li></ul></body></html>"""


async def not_found(request: Request, exc: HTTPException) -> Response:
    if request.url.path.startswith("/mcp") or request.method != "GET":
        return PlainTextResponse("Not Found", status_code=404)
    return HTMLResponse(NOT_FOUND, status_code=404)


# the MCP app already serves /mcp (and runs the session manager in its lifespan); add the page, icons and fonts to it
app.router.routes[:0] = [
    Route("/", landing),
    Route("/health", health),
    Route("/robots.txt", robots),
    Route("/sitemap.xml", sitemap),
    Route("/llms.txt", llms),
    *(Route(path, static_file) for path in FILES),
    Route("/fonts/{name}", font),
]
app.add_exception_handler(404, not_found)
