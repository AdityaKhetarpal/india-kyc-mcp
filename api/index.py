"""Vercel entry point: the hosted MCP server (see src/india_kyc_mcp/web.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from india_kyc_mcp.web import app  # noqa: E402

__all__ = ["app"]
