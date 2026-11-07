"""Vercel entry point (Vercel looks for a top-level `app` in app.py): the hosted MCP server, src/india_kyc_mcp/web.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from india_kyc_mcp.web import app  # noqa: E402

__all__ = ["app"]
