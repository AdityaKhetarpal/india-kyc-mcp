"""The tools, called the way an AI assistant calls them: through a real MCP client session."""
import json

import pytest
from mcp.client.client import Client

from india_kyc_mcp.lookups import same_place
from india_kyc_mcp.server import server


async def call(name: str, **args) -> dict:
    async with Client(server) as client:
        result = await client.call_tool(name, args)
        assert not result.is_error, result.content
        return json.loads(result.content[0].text)


async def test_tools_and_prompt_are_listed():
    async with Client(server) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
        assert set(tools) == {"lookup_ifsc", "lookup_pincode", "find_pincode", "check_address",
                              "validate_gstin", "validate_pan", "verify_vendor"}
        assert tools["validate_gstin"].annotations.read_only_hint is True
        assert "ifsc" in tools["lookup_ifsc"].input_schema["properties"]
        prompts = [p.name for p in (await client.list_prompts()).prompts]
        assert prompts == ["onboard_vendor"]


async def test_lookup_ifsc(fake_api):
    r = await call("lookup_ifsc", ifsc="hdfc0000001")
    assert r["found"] and r["bank"] == "HDFC Bank" and r["city"] == "MUMBAI"
    assert r["supports"] == {"upi": True, "neft": True, "rtgs": True, "imps": True}


async def test_lookup_ifsc_not_found_and_bad_format(fake_api):
    r = await call("lookup_ifsc", ifsc="HDFC0999999")
    assert not r["found"] and "branch part" in r["reason"]
    r = await call("lookup_ifsc", ifsc="HDFC1")
    assert not r["found"] and "11 characters" in r["reason"]
    assert fake_api.counter.calls == 1  # the badly formed code never hit the network


async def test_service_down_is_reported_not_crashed(fake_api):
    r = await call("lookup_ifsc", ifsc="HDFC0000503")
    assert r["found"] is False and "having problems (HTTP 503)" in r["error"]


async def test_results_are_cached(fake_api):
    await call("lookup_ifsc", ifsc="HDFC0000001")
    await call("lookup_ifsc", ifsc="HDFC0000001")
    assert fake_api.counter.calls == 1


async def test_lookup_pincode(fake_api):
    r = await call("lookup_pincode", pincode="110001")
    assert r["found"] and r["state"] == "Delhi"
    assert r["district"] == ["Central Delhi", "New Delhi"]
    first = r["post_offices"][0]
    assert first == {"name": "Connaught Place", "type": "Head Post Office", "delivers": True, "block": "New Delhi"}
    r = await call("lookup_pincode", pincode="999999")
    assert not r["found"] and "no post office" in r["reason"]


async def test_find_pincode(fake_api):
    r = await call("find_pincode", place="Connaught Place")
    assert r["found"] and r["results"][0]["pincode"] == "110001"
    assert not (await call("find_pincode", place="ab"))["found"]


async def test_check_address(fake_api):
    assert (await call("check_address", pincode="560001", city="Bangalore", state="Karnataka"))["verdict"] == "match"
    r = await call("check_address", pincode="560001", city="Mumbai", state="Karnataka")
    assert r["verdict"] == "partial_match" and r["checks"]["city"]["matches"] is False
    assert (await call("check_address", pincode="560001", city="Pune", state="Maharashtra"))["verdict"] == "mismatch"
    assert (await call("check_address", pincode="999999", city="Pune"))["verdict"] == "unknown_pincode"


async def test_validate_tools():
    assert (await call("validate_gstin", gstin="27AAPFU0939F1ZV"))["valid"] is True
    assert (await call("validate_pan", pan="AAPFU0939F"))["holder_type"] == "Firm / LLP"


async def test_verify_vendor_pass(fake_api):
    r = await call("verify_vendor", gstin="27AAPFU0939F1ZV", pan="AAPFU0939F", ifsc="HDFC0000001",
                   pincode="400018", city="Mumbai", state="Maharashtra")
    assert r["verdict"] == "pass" and r["red_flags"] == []
    assert r["checked"] == ["address", "bank", "gstin", "pan"]


async def test_verify_vendor_catches_mismatches(fake_api):
    r = await call("verify_vendor", gstin="27AAPFU0939F1ZV", pan="AAPFU0939G", ifsc="HDFC0000001",
                   pincode="560001", city="Mumbai", state="Karnataka")
    assert r["verdict"] == "fail"
    text = " ".join(r["red_flags"])
    assert "not the PAN inside the GSTIN" in text
    assert "city 'Mumbai' does not match" in text
    assert "GST registration state (Maharashtra) differs from the address state (Karnataka)" in text


async def test_verify_vendor_review_only(fake_api):
    # everything is well-formed and real, only the state is different: needs a human look, not a rejection
    r = await call("verify_vendor", gstin="27AAPFU0939F1ZV", pincode="560001", state="Karnataka")
    assert r["verdict"] == "review"


async def test_verify_vendor_needs_something():
    assert (await call("verify_vendor"))["verdict"] == "nothing_to_check"


@pytest.mark.parametrize("a,b,ok", [
    ("Bengaluru", "BANGALORE", True), ("Bangalore Urban", "Bengaluru", True), ("Gurugram", "GURGAON", True),
    ("New Delhi", "Delhi", True), ("Pune", "Mumbai", False), ("", "Delhi", False),
])
def test_same_place(a, b, ok):
    assert same_place(a, b) is ok
