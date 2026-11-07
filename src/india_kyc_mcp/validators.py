"""
Offline checks for Indian identifiers. No network, no API keys.

    IFSC    bank branch code, e.g. HDFC0000001   = 4-letter bank code + "0" + 6-character branch code
    GSTIN   GST number, e.g. 27AAPFU0939F1ZV     = state code + PAN + entity number + "Z" + check digit
    PAN     income-tax number, e.g. AAPFU0939F   = 5 letters + 4 digits + 1 letter; the 4th letter says who holds it
    PIN     postal code, e.g. 110001             = 6 digits; the first digit is the postal region

A format check can't prove a number belongs to a real person or company. It catches typos and made-up numbers
before anything is looked up or saved, which is most of the value in an onboarding form.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib import resources

GST_STATES = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh", "05": "Uttarakhand",
    "06": "Haryana", "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim",
    "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura", "17": "Meghalaya",
    "18": "Assam", "19": "West Bengal", "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh",
    "24": "Gujarat", "26": "Dadra and Nagar Haveli and Daman and Diu", "27": "Maharashtra", "29": "Karnataka",
    "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry",
    "35": "Andaman and Nicobar Islands", "36": "Telangana", "37": "Andhra Pradesh", "38": "Ladakh",
    "97": "Other Territory", "99": "Centre Jurisdiction",
}

PAN_HOLDER = {
    "P": "Individual (person)", "C": "Company", "H": "Hindu Undivided Family (HUF)", "F": "Firm / LLP",
    "A": "Association of Persons (AOP)", "T": "Trust", "B": "Body of Individuals (BOI)", "L": "Local authority",
    "J": "Artificial juridical person", "G": "Government",
}

PIN_REGIONS = {
    "1": "Delhi, Haryana, Punjab, Himachal Pradesh, Jammu & Kashmir, Ladakh, Chandigarh",
    "2": "Uttar Pradesh, Uttarakhand",
    "3": "Rajasthan, Gujarat, Dadra & Nagar Haveli and Daman & Diu",
    "4": "Maharashtra, Goa, Madhya Pradesh, Chhattisgarh",
    "5": "Andhra Pradesh, Telangana, Karnataka",
    "6": "Tamil Nadu, Kerala, Puducherry, Lakshadweep",
    "7": "West Bengal, Odisha, Assam and the North-East, Andaman & Nicobar Islands",
    "8": "Bihar, Jharkhand",
    "9": "Army Post Office / Field Post Office",
}

GST_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
PIN_RE = re.compile(r"^[1-9][0-9]{5}$")


def clean(value: str) -> str:
    """Upper-case and drop spaces, dots and dashes people type into forms."""
    return re.sub(r"[\s.\-]", "", str(value or "")).upper()


@lru_cache(maxsize=1)
def bank_names() -> dict[str, str]:
    """Bank code -> bank name, from Razorpay's open IFSC dataset (MIT licence)."""
    text = resources.files("india_kyc_mcp").joinpath("data/banknames.json").read_text(encoding="utf-8")
    return json.loads(text)


def check_ifsc_format(code: str) -> dict:
    ifsc = clean(code)
    problems = []
    if len(ifsc) != 11:
        problems.append(f"an IFSC has 11 characters, this has {len(ifsc)}")
    elif not IFSC_RE.match(ifsc):
        if not ifsc[:4].isalpha():
            problems.append("the first 4 characters (the bank code) must be letters")
        if ifsc[4] != "0":
            problems.append("the 5th character must be the digit 0")
        if not ifsc[5:].isalnum():
            problems.append("the last 6 characters must be letters or digits")
    bank = bank_names().get(ifsc[:4]) if len(ifsc) >= 4 else None
    if not problems and bank is None:
        problems.append(f"{ifsc[:4]} is not a known bank code")
    return {"ifsc": ifsc, "valid_format": not problems, "bank_code": ifsc[:4] or None, "bank": bank, "problems": problems}


def gstin_check_digit(first14: str) -> str:
    """The GSTIN check digit: a weighted mod-36 sum over the first 14 characters."""
    total = 0
    for i, ch in enumerate(first14):
        product = GST_CHARS.index(ch) * (2 if i % 2 else 1)
        total += product // 36 + product % 36
    return GST_CHARS[(36 - total % 36) % 36]


def check_pan(value: str) -> dict:
    pan = clean(value)
    problems = []
    if len(pan) != 10:
        problems.append(f"a PAN has 10 characters, this has {len(pan)}")
    elif not PAN_RE.match(pan):
        problems.append("a PAN is 5 letters, then 4 digits, then 1 letter (e.g. ABCPE1234F)")
    holder = PAN_HOLDER.get(pan[3]) if len(pan) == 10 and PAN_RE.match(pan) else None
    if not problems and holder is None:
        problems.append(f"the 4th letter '{pan[3]}' is not a known holder type")
    return {"pan": pan, "valid_format": not problems, "holder_type": holder, "problems": problems}


def check_gstin(value: str) -> dict:
    gstin = clean(value)
    out = {"gstin": gstin, "valid": False, "state_code": None, "state": None, "pan": None, "holder_type": None,
           "registration_number": None, "check_digit_ok": None, "problems": []}
    if len(gstin) != 15:
        out["problems"].append(f"a GSTIN has 15 characters, this has {len(gstin)}")
        return out
    if not GSTIN_RE.match(gstin):
        out["problems"].append("expected 2 digits (state) + PAN (10) + 1 entity character + 'Z' + 1 check character")
        return out
    out["state_code"] = gstin[:2]
    out["state"] = GST_STATES.get(gstin[:2])
    if out["state"] is None:
        out["problems"].append(f"{gstin[:2]} is not a valid GST state code")
    pan = check_pan(gstin[2:12])
    out["pan"] = pan["pan"]
    out["holder_type"] = pan["holder_type"]
    out["problems"] += [f"embedded PAN: {p}" for p in pan["problems"]]
    out["registration_number"] = int(gstin[12], 36)  # 1 = first registration of this PAN in this state
    expected = gstin_check_digit(gstin[:14])
    out["check_digit_ok"] = expected == gstin[14]
    if not out["check_digit_ok"]:
        out["problems"].append(f"check digit is '{gstin[14]}' but should be '{expected}': probably a typo")
    out["valid"] = not out["problems"]
    return out


def check_pincode_format(value: str) -> dict:
    pin = clean(value)
    ok = bool(PIN_RE.match(pin))
    return {
        "pincode": pin,
        "valid_format": ok,
        "region": PIN_REGIONS.get(pin[0]) if ok else None,
        "problems": [] if ok else ["a PIN code is 6 digits and does not start with 0"],
    }
