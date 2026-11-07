# india-kyc-mcp

**An MCP server that lets AI assistants check Indian bank, address and tax details during onboarding.**

Ask Claude, Cursor or any MCP-compatible assistant *"Is this vendor's bank and GST info okay?"* and it can check,
instead of guessing:

- **IFSC code** → bank, branch, address, and whether the branch supports UPI, NEFT, RTGS and IMPS (live)
- **PIN code** → district, state and post offices (live), or PIN codes for a place name
- **Address check** → does the PIN code really belong to the city and state written in the address?
- **GSTIN** → format, state, the PAN inside it, holder type, and the **check digit** (catches typos), offline
- **PAN** → format and holder type (person, company, firm, trust...), offline
- **Vendor check** → all of the above in one call, with the cross-checks a finance team does by hand,
  and a verdict: `pass`, `review` or `fail`

No API keys. Live data comes from two free public services:
[Razorpay's IFSC API](https://github.com/razorpay/ifsc) (RBI data) and the India Post directory at
[api.postalpincode.in](https://api.postalpincode.in).

[![CI](https://github.com/AdityaKhetarpal/india-kyc-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/AdityaKhetarpal/india-kyc-mcp/actions/workflows/ci.yml)
[![Weekly live check](https://github.com/AdityaKhetarpal/india-kyc-mcp/actions/workflows/live-check.yml/badge.svg)](examples/live_check.md)

---

## Why

Onboarding a vendor or a business customer in India means checking the same handful of details every time:
the GSTIN, the PAN, the bank's IFSC and the address. The usual mistakes are small: one wrong character in a GSTIN,
a PAN that isn't the one inside the GSTIN, a PIN code from a different city, a branch that doesn't support NEFT so
payouts fail. They are easy to check, but only if the assistant has tools for it. Without tools, an LLM will
happily say a made-up IFSC "looks fine".

## Example

You paste a vendor's details into Claude:

> Onboard this vendor: Shree Ganesh Traders, GSTIN 27AAPFU0939F1ZV, PAN AAPFU0939G, bank IFSC HDFC0000001,
> address: MG Road, Mumbai, Karnataka 560001

Claude calls `verify_vendor` and gets back (this is the real output):

```json
{
  "verdict": "fail",
  "red_flags": [
    "PAN AAPFU0939G is not the PAN inside the GSTIN (AAPFU0939F)",
    "city 'Mumbai' does not match PIN code 560001 (Bangalore)",
    "GST registration state (Maharashtra) differs from the address state (Karnataka)"
  ],
  "checked": ["address", "bank", "gstin", "pan"]
}
```

So it can reply: *"Don't approve yet. The PAN has a typo (last letter should be F), and PIN code 560001 is in
Bangalore, not Mumbai. Ask the vendor to confirm both."* The full responses from every tool, run against the real
APIs every week, are in [examples/live_check.md](examples/live_check.md).

## Tools

| Tool | What it does | Data |
|---|---|---|
| `lookup_ifsc` | Bank, branch, address, city, state, MICR, SWIFT, UPI/NEFT/RTGS/IMPS support | live |
| `lookup_pincode` | District, state and post offices for a PIN code | live |
| `find_pincode` | PIN codes for a post office or locality name | live |
| `check_address` | `match` / `partial_match` / `mismatch` between a PIN code and a city/state | live |
| `validate_gstin` | Format, state code, embedded PAN, holder type, check digit | offline |
| `validate_pan` | Format and holder type from the 4th letter | offline |
| `verify_vendor` | All of the above in one call, plus cross-checks, verdict and red flags | both |

There is also a prompt, `onboard_vendor`, that tells the assistant to extract the details from pasted text,
call `verify_vendor` once and answer with a table and a recommendation.

Every tool is marked read-only. Badly formed codes are rejected before any network call, short outages of the public
APIs (a 503 or a timeout) are retried twice, results are cached for an
hour, and when a service is down the tool says so in plain words instead of failing.

**What it does not do:** a format check proves a GSTIN or PAN is *well-formed*, not that it is registered to that
business. Confirming registration needs the government GST portal, which has no free public API.

## Install

```bash
pip install "git+https://github.com/AdityaKhetarpal/india-kyc-mcp"
```

**Claude Code**

```bash
claude mcp add india-kyc -- india-kyc-mcp
```

**Claude Desktop** (`claude_desktop_config.json`) or **Cursor** (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "india-kyc": { "command": "india-kyc-mcp" }
  }
}
```

**Over HTTP** (for agents that connect to a URL): `india-kyc-mcp --http --port 8000` serves
`http://127.0.0.1:8000/mcp`.

Try it with the MCP Inspector: `npx @modelcontextprotocol/inspector india-kyc-mcp`

## How the GSTIN check works

A GSTIN is 15 characters: `27` state code + `AAPFU0939F` PAN + `1` registration number + `Z` + `V` check digit.
The check digit is a weighted sum of the first 14 characters (each mapped to 0–35, every second one doubled,
the two base-36 digits of each product added), taken mod 36. The tests prove it catches **every** single-character
substitution in the PAN part (all 420 possible typos of a sample GSTIN).

## Project layout

```
src/india_kyc_mcp/
  server.py        the MCP server: tools, prompt, stdio/HTTP entry point
  lookups.py       live IFSC and PIN code lookups (httpx, 1-hour cache, clear errors)
  validators.py    offline GSTIN / PAN / IFSC / PIN checks
  data/            bank codes and names (from razorpay/ifsc, MIT)
tests/             tools called through a real MCP client session, against recorded API responses
scripts/live_check.py   the same tools against the real APIs (weekly on GitHub Actions)
```

## Development

```bash
pip install -e ".[dev]"
ruff check . && pytest -q
python scripts/live_check.py      # needs internet
```

Built by [Aditya Khetarpal](https://www.linkedin.com/in/adityakhetarpal). MIT licence. Bank names from
[razorpay/ifsc](https://github.com/razorpay/ifsc) (MIT).
