import pytest

from india_kyc_mcp.validators import (
    bank_names,
    check_gstin,
    check_ifsc_format,
    check_pan,
    check_pincode_format,
    gstin_check_digit,
)


@pytest.mark.parametrize("gstin", ["27AAPFU0939F1ZV", "29AAGCB7383J1Z4"])
def test_real_gstin_examples_are_valid(gstin):
    r = check_gstin(gstin)
    assert r["valid"] and r["check_digit_ok"] and r["problems"] == []


def test_gstin_details():
    r = check_gstin(" 27aapfu0939f1zv ")
    assert r["gstin"] == "27AAPFU0939F1ZV"
    assert r["state"] == "Maharashtra" and r["pan"] == "AAPFU0939F" and r["holder_type"] == "Firm / LLP"
    assert r["registration_number"] == 1


def test_gstin_typo_is_caught_by_the_check_digit():
    # change one character of a valid GSTIN: the check digit no longer fits
    r = check_gstin("27AAPFU0939F1ZW")
    assert not r["valid"] and r["check_digit_ok"] is False and "should be 'V'" in r["problems"][0]
    r = check_gstin("27AAPFU0938F1ZV")
    assert not r["valid"]


def test_every_single_character_typo_in_the_pan_part_is_caught():
    good = "27AAPFU0939F1ZV"
    caught = 0
    for i in range(2, 14):
        for ch in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if ch == good[i]:
                continue
            typo = good[:i] + ch + good[i + 1:]
            if gstin_check_digit(typo[:14]) != typo[14]:
                caught += 1
    total = 12 * 35
    assert caught == total  # the mod-36 check digit catches every single-character substitution


def test_gstin_bad_shapes():
    assert "15 characters" in check_gstin("27AAPFU0939F1Z")["problems"][0]
    assert not check_gstin("27AAPFU0939F1XV")["valid"]  # 14th character must be Z
    r = check_gstin("98AAPFU0939F1ZV")
    assert not r["valid"] and any("state code" in p for p in r["problems"])


def test_pan():
    assert check_pan("abcpe1234f")["holder_type"] == "Individual (person)"
    assert check_pan("AAACR5055K")["holder_type"] == "Company"
    assert not check_pan("ABCPE1234")["valid_format"]
    assert not check_pan("1BCPE1234F")["valid_format"]
    r = check_pan("ABCXE1234F")
    assert not r["valid_format"] and "holder type" in r["problems"][0]


def test_ifsc_format():
    r = check_ifsc_format("hdfc 0000 001")
    assert r["valid_format"] and r["ifsc"] == "HDFC0000001" and r["bank"] == "HDFC Bank"
    assert "5th character" in check_ifsc_format("HDFC1000001")["problems"][0]
    assert "11 characters" in check_ifsc_format("HDFC00001")["problems"][0]
    assert "not a known bank code" in check_ifsc_format("ZZZZ0000001")["problems"][0]
    assert len(bank_names()) > 1000


def test_pincode_format():
    assert check_pincode_format("110001")["region"].startswith("Delhi")
    assert not check_pincode_format("011001")["valid_format"]
    assert not check_pincode_format("11001")["valid_format"]
