"""
End-to-end check against the REAL public APIs, through a real MCP client session (the same way Claude or Cursor
calls the tools). Run weekly on GitHub Actions so a change in either API is noticed quickly.

    python scripts/live_check.py            # prints a report, exits 1 if a check fails
    python scripts/live_check.py --save     # also writes examples/live_check.json and examples/live_check.md
    python scripts/live_check.py --url https://indiakyc.vercel.app/mcp   # the hosted server, over HTTP
"""
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from mcp.client.client import Client

from india_kyc_mcp.server import server

ROOT = Path(__file__).resolve().parent.parent

# (tool, arguments, what must be true about the result)
CHECKS = [
    ("lookup_ifsc", {"ifsc": "HDFC0000001"}, lambda r: r["found"] and "HDFC" in r["bank"].upper()),
    ("lookup_ifsc", {"ifsc": "KKBK0000261"}, lambda r: r["found"] and "KOTAK" in r["bank"].upper()),
    ("lookup_ifsc", {"ifsc": "SBIN0000691"}, lambda r: r["found"] and "STATE BANK" in r["bank"].upper()),
    ("lookup_ifsc", {"ifsc": "HDFC0ZZZZZZ"}, lambda r: r["found"] is False),
    ("lookup_pincode", {"pincode": "110001"}, lambda r: r["found"] and "Delhi" in json.dumps(r["state"])),
    ("lookup_pincode", {"pincode": "560001"}, lambda r: r["found"] and r["state"] == "Karnataka"),
    ("lookup_pincode", {"pincode": "999999"}, lambda r: r["found"] is False),
    ("find_pincode", {"place": "Connaught Place"}, lambda r: r["found"] and any(x["pincode"] == "110001" for x in r["results"])),
    ("check_address", {"pincode": "560001", "city": "Bangalore", "state": "Karnataka"}, lambda r: r["verdict"] == "match"),
    ("check_address", {"pincode": "560001", "city": "Mumbai", "state": "Maharashtra"}, lambda r: r["verdict"] == "mismatch"),
    ("validate_gstin", {"gstin": "27AAPFU0939F1ZV"}, lambda r: r["valid"]),
    ("validate_gstin", {"gstin": "27AAPFU0939F1ZW"}, lambda r: not r["valid"]),
    ("verify_vendor", {"gstin": "27AAPFU0939F1ZV", "pan": "AAPFU0939F", "ifsc": "HDFC0000001", "pincode": "400018",
                       "city": "Mumbai", "state": "Maharashtra"}, lambda r: r["verdict"] == "pass"),
    ("verify_vendor", {"gstin": "27AAPFU0939F1ZV", "pan": "AAPFU0939G", "ifsc": "HDFC0000001", "pincode": "560001",
                       "city": "Mumbai", "state": "Karnataka"}, lambda r: r["verdict"] == "fail"),
]


async def run(url: str | None = None) -> list[dict]:
    rows = []
    async with Client(url or server) as client:
        for tool, args, expect in CHECKS:
            start = time.perf_counter()
            result = await client.call_tool(tool, args)
            seconds = round(time.perf_counter() - start, 2)
            data = json.loads(result.content[0].text)
            try:
                ok = bool(expect(data)) and not result.is_error
            except (KeyError, TypeError):
                ok = False
            rows.append({"tool": tool, "arguments": args, "ok": ok, "seconds": seconds, "result": data})
            print(f"{'PASS' if ok else 'FAIL'} {seconds:5.2f}s {tool} {json.dumps(args)}")
    return rows


def markdown(rows: list[dict], when: str) -> str:
    lines = [f"# Live check ({when})", "", "Real calls to the public APIs through an MCP client session.", "",
             "| Result | Tool | Arguments | Time |", "|---|---|---|---|"]
    for r in rows:
        args = ", ".join(f"{k}={v}" for k, v in r["arguments"].items())
        lines.append(f"| {'✅' if r['ok'] else '❌'} | `{r['tool']}` | {args} | {r['seconds']}s |")
    lines += ["", "## Responses", ""]
    for r in rows:
        lines += [f"### `{r['tool']}` · {', '.join(f'{k}={v}' for k, v in r['arguments'].items())}", "",
                  "```json", json.dumps(r["result"], indent=2, ensure_ascii=False), "```", ""]
    return "\n".join(lines)


def main() -> int:
    url = sys.argv[sys.argv.index("--url") + 1] if "--url" in sys.argv else None
    print(f"checking {'the hosted server at ' + url if url else 'the server in-process'}")
    rows = asyncio.run(run(url))
    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    passed = sum(r["ok"] for r in rows)
    print(f"\n{passed}/{len(rows)} live checks passed")
    if "--save" in sys.argv and not url:
        (ROOT / "examples").mkdir(exist_ok=True)
        (ROOT / "examples" / "live_check.json").write_text(
            json.dumps({"checked_at": when, "passed": passed, "total": len(rows), "checks": rows}, indent=2,
                       ensure_ascii=False) + "\n")
        (ROOT / "examples" / "live_check.md").write_text(markdown(rows, when) + "\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            title = f"Hosted server ({url})" if url else "In-process server"
            f.write(f"## {title}\n\n" + markdown(rows, when).split("## Responses")[0])
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
