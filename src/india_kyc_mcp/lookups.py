"""
Live lookups against free public services. No API keys.

    IFSC      https://ifsc.razorpay.com/<IFSC>                  Razorpay's open IFSC API (data from RBI)
    PIN code  https://api.postalpincode.in/pincode/<PIN>        India Post post-office directory
    Place     https://api.postalpincode.in/postoffice/<name>    post offices by name

Results are cached in memory for an hour (branch and post-office data change rarely). Short outages (HTTP 5xx,
timeouts) are retried twice, and every failure that remains comes back as a short message the AI can pass on,
never as a crash.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any
from urllib.parse import quote

import httpx

from .validators import check_ifsc_format, check_pincode_format, clean

IFSC_API = "https://ifsc.razorpay.com"
POSTAL_API = "https://api.postalpincode.in"
TIMEOUT = httpx.Timeout(10.0, connect=5.0)
CACHE_SECONDS = 3600
RETRIES = 2          # extra attempts after a 5xx or a timeout
RETRY_DELAY = 1.0    # seconds; doubled on the second retry
USER_AGENT = "india-kyc-mcp/0.1 (+https://github.com/AdityaKhetarpal/india-kyc-mcp)"


class ServiceError(Exception):
    """A lookup failed in a way worth telling the user about (not found, service down...)."""


class Lookups:
    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client
        self._cache: dict[str, tuple[float, Any]] = {}

    async def _get_json(self, url: str) -> tuple[int, Any]:
        hit = self._cache.get(url)
        if hit and time.monotonic() - hit[0] < CACHE_SECONDS:
            return 200, hit[1]
        client = self._client or httpx.AsyncClient(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
        try:
            # free public APIs have short hiccups (a 503 or a timeout): try again, up to RETRIES times
            for attempt in range(RETRIES + 1):
                last = attempt == RETRIES
                try:
                    response = await client.get(url)
                except httpx.TimeoutException as e:
                    if last:
                        raise ServiceError("the lookup service did not answer in time; try again in a minute") from e
                except httpx.HTTPError as e:
                    if last:
                        raise ServiceError(f"could not reach the lookup service ({type(e).__name__})") from e
                else:
                    if response.status_code < 500 or last:
                        break
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
        finally:
            if self._client is None:
                await client.aclose()
        if response.status_code == 404:
            return 404, None
        if response.status_code >= 500:
            raise ServiceError(f"the lookup service is having problems (HTTP {response.status_code})")
        if response.status_code != 200:
            raise ServiceError(f"unexpected answer from the lookup service (HTTP {response.status_code})")
        try:
            data = response.json()
        except ValueError as e:
            raise ServiceError("the lookup service sent something that is not JSON") from e
        self._cache[url] = (time.monotonic(), data)
        return 200, data

    # ------------------------------------------------------------------ IFSC

    async def ifsc(self, code: str) -> dict:
        fmt = check_ifsc_format(code)
        if not fmt["valid_format"]:
            return {"found": False, "ifsc": fmt["ifsc"], "reason": "; ".join(fmt["problems"])}
        status, data = await self._get_json(f"{IFSC_API}/{fmt['ifsc']}")
        if status == 404 or not isinstance(data, dict):
            return {"found": False, "ifsc": fmt["ifsc"], "bank": fmt["bank"],
                    "reason": f"no branch with this IFSC (the bank code {fmt['bank_code']} is valid, the branch part is not)"}
        return {
            "found": True,
            "ifsc": data.get("IFSC", fmt["ifsc"]),
            "bank": data.get("BANK"),
            "branch": data.get("BRANCH"),
            "address": data.get("ADDRESS"),
            "city": data.get("CITY"),
            "district": data.get("DISTRICT"),
            "state": data.get("STATE"),
            "contact": data.get("CONTACT") or None,
            "micr": data.get("MICR") or None,
            "swift": data.get("SWIFT") or None,
            "supports": {k.lower(): bool(data.get(k)) for k in ("UPI", "NEFT", "RTGS", "IMPS")},
        }

    # ------------------------------------------------------------------ PIN codes

    @staticmethod
    def _offices(payload: Any) -> list[dict]:
        if not isinstance(payload, list) or not payload:
            return []
        block = payload[0] or {}
        if str(block.get("Status", "")).lower() != "success":
            return []
        return [o for o in (block.get("PostOffice") or []) if isinstance(o, dict)]

    async def pincode(self, pin: str) -> dict:
        fmt = check_pincode_format(pin)
        if not fmt["valid_format"]:
            return {"found": False, "pincode": fmt["pincode"], "reason": fmt["problems"][0]}
        _, data = await self._get_json(f"{POSTAL_API}/pincode/{fmt['pincode']}")
        offices = self._offices(data)
        if not offices:
            return {"found": False, "pincode": fmt["pincode"], "region": fmt["region"],
                    "reason": "no post office has this PIN code"}
        districts = sorted({o.get("District") for o in offices if o.get("District")})
        states = sorted({o.get("State") for o in offices if o.get("State")})
        return {
            "found": True,
            "pincode": fmt["pincode"],
            "district": districts[0] if len(districts) == 1 else districts,
            "state": states[0] if len(states) == 1 else states,
            "post_offices": [
                {"name": o.get("Name"), "type": o.get("BranchType"), "delivers": o.get("DeliveryStatus") == "Delivery",
                 "block": o.get("Block") if o.get("Block") not in (None, "NA") else None}
                for o in offices
            ],
        }

    async def find_pincodes(self, place: str, limit: int = 15) -> dict:
        name = " ".join(str(place or "").split())
        if len(name) < 3:
            return {"found": False, "place": name, "reason": "give at least 3 letters of the place name"}
        _, data = await self._get_json(f"{POSTAL_API}/postoffice/{quote(name)}")
        offices = self._offices(data)
        if not offices:
            return {"found": False, "place": name, "reason": "no post office with that name"}
        rows = [{"post_office": o.get("Name"), "pincode": o.get("Pincode") or o.get("PINCode"),
                 "district": o.get("District"), "state": o.get("State")} for o in offices]
        return {"found": True, "place": name, "matches": len(rows), "results": rows[:limit],
                "truncated": len(rows) > limit}


def same_place(a: str | None, b: str | None) -> bool:
    """Loose match for place names: case, spaces and common spellings ignored (Bengaluru = Bangalore)."""
    aliases = {"bengaluru": "bangalore", "mumbai": "bombay", "kolkata": "calcutta", "chennai": "madras",
               "gurugram": "gurgaon", "puducherry": "pondicherry", "nctofdelhi": "delhi", "newdelhi": "delhi",
               "prayagraj": "allahabad", "thiruvananthapuram": "trivandrum", "mysuru": "mysore"}

    def norm(s: str) -> str:
        key = "".join(ch for ch in clean(s).lower() if ch.isalnum())
        for suffix in ("urban", "rural", "city", "district"):
            if key.endswith(suffix) and len(key) > len(suffix) + 2:
                key = key[: -len(suffix)]
        return aliases.get(key, key)

    if not a or not b:
        return False
    x, y = norm(a), norm(b)
    return bool(x) and (x == y or x in y or y in x)
