"""
The MCP server: the tools an AI assistant (Claude, Cursor, ...) can call.

    lookup_ifsc       bank + branch + address + UPI/NEFT/RTGS/IMPS support for an IFSC code     (live)
    lookup_pincode    district, state and post offices for a PIN code                           (live)
    find_pincode      PIN codes for a place name                                                (live)
    check_address     does this PIN code really belong to this city / state?                    (live)
    validate_gstin    GST number: format, state, embedded PAN, check digit                      (offline)
    validate_pan      PAN: format and holder type (person, company, firm...)                     (offline)
    verify_vendor     everything above for one vendor, with cross-checks and a verdict          (live + offline)

Run it:  india-kyc-mcp            (stdio, for Claude Desktop / Claude Code / Cursor)
         india-kyc-mcp --http     (streamable HTTP on http://127.0.0.1:8000/mcp)
"""
from __future__ import annotations

import argparse
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from . import __version__
from .lookups import Lookups, ServiceError, same_place
from .validators import check_gstin, check_pan, clean

INSTRUCTIONS = (
    "Tools for checking Indian bank, address and tax details during customer or vendor onboarding (KYC). "
    "Format checks (GSTIN, PAN) are offline and only prove a number is well-formed, not that it is registered. "
    "IFSC and PIN code lookups use live public data. Report problems plainly and never invent details a tool did not return."
)

server = MCPServer("india-kyc", title="India KYC lookups", version=__version__, instructions=INSTRUCTIONS)
lookups = Lookups()

LIVE = ToolAnnotations(readOnlyHint=True, openWorldHint=True, idempotentHint=True)
OFFLINE = ToolAnnotations(readOnlyHint=True, openWorldHint=False, idempotentHint=True)


async def _safe(coro) -> dict:
    try:
        return await coro
    except ServiceError as e:
        return {"found": False, "error": str(e)}


@server.tool(title="Look up an IFSC code", annotations=LIVE)
async def lookup_ifsc(ifsc: Annotated[str, Field(description="11-character IFSC code, e.g. HDFC0000001")]) -> dict:
    """Find the bank and branch for an IFSC code: name, address, city, state, MICR/SWIFT codes,
    and whether the branch supports UPI, NEFT, RTGS and IMPS. Use it to confirm the bank details a customer typed."""
    return await _safe(lookups.ifsc(ifsc))


@server.tool(title="Look up a PIN code", annotations=LIVE)
async def lookup_pincode(pincode: Annotated[str, Field(description="6-digit Indian PIN code, e.g. 110001")]) -> dict:
    """Find the district, state and post offices for an Indian PIN code."""
    return await _safe(lookups.pincode(pincode))


@server.tool(title="Find PIN codes for a place", annotations=LIVE)
async def find_pincode(place: Annotated[str, Field(description="Post office or locality name, e.g. Connaught Place")]) -> dict:
    """Search post offices by name and return their PIN codes, districts and states."""
    return await _safe(lookups.find_pincodes(place))


@server.tool(title="Check an address against its PIN code", annotations=LIVE)
async def check_address(
    pincode: Annotated[str, Field(description="6-digit PIN code from the address")],
    city: Annotated[str | None, Field(description="City, town or locality from the address")] = None,
    state: Annotated[str | None, Field(description="State from the address")] = None,
) -> dict:
    """Check that a PIN code really belongs to the city and state written in an address.
    Catches the most common address error in forms: a PIN code from a different city."""
    info = await _safe(lookups.pincode(pincode))
    if not info.get("found"):
        return {"verdict": "unknown_pincode", **info}
    districts = info["district"] if isinstance(info["district"], list) else [info["district"]]
    states = info["state"] if isinstance(info["state"], list) else [info["state"]]
    places = districts + [o["name"] for o in info["post_offices"]] + [o["block"] for o in info["post_offices"] if o["block"]]
    checks = {}
    if city:
        checks["city"] = {"given": city, "matches": any(same_place(city, p) for p in places), "pincode_district": districts}
    if state:
        checks["state"] = {"given": state, "matches": any(same_place(state, s) for s in states), "pincode_state": states}
    if not checks:
        verdict = "pincode_only"
    elif all(c["matches"] for c in checks.values()):
        verdict = "match"
    elif any(c["matches"] for c in checks.values()):
        verdict = "partial_match"
    else:
        verdict = "mismatch"
    return {"verdict": verdict, "pincode": info["pincode"], "checks": checks,
            "post_offices": [o["name"] for o in info["post_offices"]][:10]}


@server.tool(title="Validate a GSTIN", annotations=OFFLINE)
def validate_gstin(gstin: Annotated[str, Field(description="15-character GST number, e.g. 27AAPFU0939F1ZV")]) -> dict:
    """Check a GST number offline: length and format, state code, the PAN inside it, the holder type,
    and the check digit (which catches almost all single-character typos). It does not prove the GSTIN is registered."""
    return check_gstin(gstin)


@server.tool(title="Validate a PAN", annotations=OFFLINE)
def validate_pan(pan: Annotated[str, Field(description="10-character PAN, e.g. ABCPE1234F")]) -> dict:
    """Check a PAN offline: format, and the holder type from its 4th letter (person, company, firm, trust...).
    It does not prove the PAN is registered or belongs to a particular person."""
    return check_pan(pan)


@server.tool(title="Verify a vendor's details", annotations=LIVE)
async def verify_vendor(
    gstin: Annotated[str | None, Field(description="Vendor's GST number")] = None,
    pan: Annotated[str | None, Field(description="Vendor's PAN")] = None,
    ifsc: Annotated[str | None, Field(description="IFSC of the vendor's bank account")] = None,
    pincode: Annotated[str | None, Field(description="PIN code of the vendor's address")] = None,
    city: Annotated[str | None, Field(description="City in the vendor's address")] = None,
    state: Annotated[str | None, Field(description="State in the vendor's address")] = None,
) -> dict:
    """One onboarding check for a vendor or business customer. Runs every relevant check and the cross-checks
    a finance team does by hand: does the PAN match the one inside the GSTIN, is the GST state the same as the
    address state, is the bank branch real. Returns a verdict (pass / review / fail) and the list of red flags."""
    report: dict = {}
    flags: list[str] = []
    hard_fail = False

    if gstin:
        g = check_gstin(gstin)
        report["gstin"] = g
        if not g["valid"]:
            hard_fail = True
            flags += [f"GSTIN: {p}" for p in g["problems"]]
    if pan:
        p = check_pan(pan)
        report["pan"] = p
        if not p["valid_format"]:
            hard_fail = True
            flags += [f"PAN: {x}" for x in p["problems"]]
    if gstin and pan and report["gstin"].get("pan") and clean(pan) != report["gstin"]["pan"]:
        hard_fail = True
        flags.append(f"PAN {clean(pan)} is not the PAN inside the GSTIN ({report['gstin']['pan']})")
    if ifsc:
        bank = await _safe(lookups.ifsc(ifsc))
        report["bank"] = bank
        if bank.get("error"):
            flags.append(f"bank check could not run: {bank['error']}")
        elif not bank.get("found"):
            hard_fail = True
            flags.append(f"IFSC: {bank.get('reason')}")
        elif not bank["supports"].get("neft"):
            flags.append("bank branch does not support NEFT, so vendor payouts may fail")
    if pincode:
        address = await check_address(pincode, city, state)
        report["address"] = address
        if address.get("error"):
            flags.append(f"address check could not run: {address['error']}")
        elif address["verdict"] == "unknown_pincode":
            hard_fail = True
            flags.append(f"PIN code: {address.get('reason')}")
        elif address["verdict"] in ("mismatch", "partial_match"):
            for name, c in address["checks"].items():
                if not c["matches"]:
                    where = c.get("pincode_district") or c.get("pincode_state")
                    flags.append(f"{name} '{c['given']}' does not match PIN code {address['pincode']} ({', '.join(where)})")
        gst_state = report.get("gstin", {}).get("state")
        if gst_state and state and not same_place(gst_state, state):
            flags.append(f"GST registration state ({gst_state}) differs from the address state ({state})")

    if not report:
        return {"verdict": "nothing_to_check", "red_flags": ["give at least one of gstin, pan, ifsc, pincode"]}
    verdict = "fail" if hard_fail else ("review" if flags else "pass")
    return {"verdict": verdict, "red_flags": flags, "checked": sorted(report), "details": report}


@server.prompt(title="Onboard a vendor")
def onboard_vendor(vendor_details: str) -> str:
    """A ready-made instruction for checking a new vendor's details pasted from an email or form."""
    return (
        "Check these vendor details for onboarding. Pull out the GSTIN, PAN, IFSC, PIN code, city and state, "
        "call verify_vendor once with them, then reply with a short table of each check and its result, "
        "the red flags in plain words, and a clear recommendation (approve / ask the vendor to fix X / reject). "
        "Do not guess any detail that is missing; list it as missing.\n\nVendor details:\n" + vendor_details
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="india-kyc-mcp", description="MCP server for Indian KYC lookups")
    parser.add_argument("--http", action="store_true", help="serve over streamable HTTP instead of stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.http:
        server.run("streamable-http", host=args.host, port=args.port)
    else:
        server.run("stdio")


if __name__ == "__main__":
    main()
