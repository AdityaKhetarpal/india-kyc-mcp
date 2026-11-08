# Live check (2026-11-08 03:40 UTC)

Real calls to the public APIs through an MCP client session.

| Result | Tool | Arguments | Time |
|---|---|---|---|
| ✅ | `lookup_ifsc` | ifsc=HDFC0000001 | 0.85s |
| ✅ | `lookup_ifsc` | ifsc=KKBK0000261 | 0.71s |
| ✅ | `lookup_ifsc` | ifsc=SBIN0000691 | 0.72s |
| ✅ | `lookup_ifsc` | ifsc=HDFC0ZZZZZZ | 0.73s |
| ✅ | `lookup_pincode` | pincode=110001 | 0.2s |
| ✅ | `lookup_pincode` | pincode=560001 | 0.19s |
| ✅ | `lookup_pincode` | pincode=999999 | 0.34s |
| ✅ | `find_pincode` | place=Connaught Place | 0.4s |
| ✅ | `check_address` | pincode=560001, city=Bangalore, state=Karnataka | 0.0s |
| ✅ | `check_address` | pincode=560001, city=Mumbai, state=Maharashtra | 0.0s |
| ✅ | `validate_gstin` | gstin=27AAPFU0939F1ZV | 0.0s |
| ✅ | `validate_gstin` | gstin=27AAPFU0939F1ZW | 0.0s |
| ✅ | `verify_vendor` | gstin=27AAPFU0939F1ZV, pan=AAPFU0939F, ifsc=HDFC0000001, pincode=400018, city=Mumbai, state=Maharashtra | 0.18s |
| ✅ | `verify_vendor` | gstin=27AAPFU0939F1ZV, pan=AAPFU0939G, ifsc=HDFC0000001, pincode=560001, city=Mumbai, state=Karnataka | 0.0s |

## Responses

### `lookup_ifsc` · ifsc=HDFC0000001

```json
{
  "found": true,
  "ifsc": "HDFC0000001",
  "bank": "HDFC Bank",
  "branch": "TULSIANI CHMBRS - NARIMAN PT",
  "address": "101-104 TULSIANI CHAMBERSFREE PRESS JOURNAL MARGNARIMAN POINTMUMBAI MAHARASHTRA 400 021",
  "city": "GREATER MUMBAI",
  "district": "MUMBAI",
  "state": "MAHARASHTRA",
  "contact": "+919890603333",
  "micr": "400240003",
  "swift": "HDFCINBB",
  "supports": {
    "upi": true,
    "neft": true,
    "rtgs": true,
    "imps": true
  }
}
```

### `lookup_ifsc` · ifsc=KKBK0000261

```json
{
  "found": true,
  "ifsc": "KKBK0000261",
  "bank": "Kotak Mahindra Bank",
  "branch": "GURGAON",
  "address": "KOTAK MAHINDRA BANK LTD. UNIT NO. 8&9, SEWA CORPORATE PARK, MG ROAD, REVENUE STATE OF SARHAUL TEHSIL, DISTT,- GURGAON- 122001",
  "city": "GURGAON",
  "district": "GURGAON",
  "state": "HARYANA",
  "contact": "+9118004100",
  "micr": "110485003",
  "swift": null,
  "supports": {
    "upi": true,
    "neft": true,
    "rtgs": true,
    "imps": true
  }
}
```

### `lookup_ifsc` · ifsc=SBIN0000691

```json
{
  "found": true,
  "ifsc": "SBIN0000691",
  "bank": "State Bank of India",
  "branch": "NEW DELHI MAIN BRANCH",
  "address": "11SANSAD MARG, NEW DELHI 110 001",
  "city": "NEW DELHI",
  "district": "NEW DELHI",
  "state": "DELHI",
  "contact": null,
  "micr": "110002087",
  "swift": "SBININBB104",
  "supports": {
    "upi": true,
    "neft": true,
    "rtgs": true,
    "imps": true
  }
}
```

### `lookup_ifsc` · ifsc=HDFC0ZZZZZZ

```json
{
  "found": false,
  "ifsc": "HDFC0ZZZZZZ",
  "bank": "HDFC Bank",
  "reason": "no branch with this IFSC (the bank code HDFC is valid, the branch part is not)"
}
```

### `lookup_pincode` · pincode=110001

```json
{
  "found": true,
  "pincode": "110001",
  "district": [
    "Central Delhi",
    "New Delhi"
  ],
  "state": "Delhi",
  "post_offices": [
    {
      "name": "Baroda House",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Bengali Market",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Bhagat Singh Market",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Connaught Place",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Constitution House",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Election Commission",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Janpath",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Krishi Bhawan",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Lady Harding Medical College",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "New Delhi ",
      "type": "Head Post Office",
      "delivers": true,
      "block": "New Delhi"
    },
    {
      "name": "North Avenue",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Parliament House",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Patiala House",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Pragati Maidan",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Pragati Maidan Camp",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Rail Bhawan",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Sansad Marg",
      "type": "Head Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Sansadiya Soudh",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Secretariat North",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Shastri Bhawan",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    },
    {
      "name": "Supreme Court",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "New Delhi"
    }
  ]
}
```

### `lookup_pincode` · pincode=560001

```json
{
  "found": true,
  "pincode": "560001",
  "district": "Bangalore",
  "state": "Karnataka",
  "post_offices": [
    {
      "name": "Bangalore ",
      "type": "Head Post Office",
      "delivers": true,
      "block": "Bangalore North"
    },
    {
      "name": "Bangalore Bazaar",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "Bangalore North"
    },
    {
      "name": "CMM Court Complex",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "Bangalore"
    },
    {
      "name": "Dr. Ambedkar Veedhi",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "Bangalore North"
    },
    {
      "name": "HighCourt",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "Bangalore North"
    },
    {
      "name": "Legislators Home",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "Bangalore North"
    },
    {
      "name": "Mahatma Gandhi Road",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "Bangalore North"
    },
    {
      "name": "Rajbhavan (Bangalore)",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "Bangalore North"
    },
    {
      "name": "Vasanthanagar",
      "type": "Sub Post Office",
      "delivers": false,
      "block": null
    },
    {
      "name": "Vidhana Soudha",
      "type": "Sub Post Office",
      "delivers": false,
      "block": "Bangalore North"
    }
  ]
}
```

### `lookup_pincode` · pincode=999999

```json
{
  "found": false,
  "pincode": "999999",
  "region": "Army Post Office / Field Post Office",
  "reason": "no post office has this PIN code"
}
```

### `find_pincode` · place=Connaught Place

```json
{
  "found": true,
  "place": "Connaught Place",
  "matches": 1,
  "results": [
    {
      "post_office": "Connaught Place",
      "pincode": "110001",
      "district": "Central Delhi",
      "state": "Delhi"
    }
  ],
  "truncated": false
}
```

### `check_address` · pincode=560001, city=Bangalore, state=Karnataka

```json
{
  "verdict": "match",
  "pincode": "560001",
  "checks": {
    "city": {
      "given": "Bangalore",
      "matches": true,
      "pincode_district": [
        "Bangalore"
      ]
    },
    "state": {
      "given": "Karnataka",
      "matches": true,
      "pincode_state": [
        "Karnataka"
      ]
    }
  },
  "post_offices": [
    "Bangalore ",
    "Bangalore Bazaar",
    "CMM Court Complex",
    "Dr. Ambedkar Veedhi",
    "HighCourt",
    "Legislators Home",
    "Mahatma Gandhi Road",
    "Rajbhavan (Bangalore)",
    "Vasanthanagar",
    "Vidhana Soudha"
  ]
}
```

### `check_address` · pincode=560001, city=Mumbai, state=Maharashtra

```json
{
  "verdict": "mismatch",
  "pincode": "560001",
  "checks": {
    "city": {
      "given": "Mumbai",
      "matches": false,
      "pincode_district": [
        "Bangalore"
      ]
    },
    "state": {
      "given": "Maharashtra",
      "matches": false,
      "pincode_state": [
        "Karnataka"
      ]
    }
  },
  "post_offices": [
    "Bangalore ",
    "Bangalore Bazaar",
    "CMM Court Complex",
    "Dr. Ambedkar Veedhi",
    "HighCourt",
    "Legislators Home",
    "Mahatma Gandhi Road",
    "Rajbhavan (Bangalore)",
    "Vasanthanagar",
    "Vidhana Soudha"
  ]
}
```

### `validate_gstin` · gstin=27AAPFU0939F1ZV

```json
{
  "gstin": "27AAPFU0939F1ZV",
  "valid": true,
  "state_code": "27",
  "state": "Maharashtra",
  "pan": "AAPFU0939F",
  "holder_type": "Firm / LLP",
  "registration_number": 1,
  "check_digit_ok": true,
  "problems": []
}
```

### `validate_gstin` · gstin=27AAPFU0939F1ZW

```json
{
  "gstin": "27AAPFU0939F1ZW",
  "valid": false,
  "state_code": "27",
  "state": "Maharashtra",
  "pan": "AAPFU0939F",
  "holder_type": "Firm / LLP",
  "registration_number": 1,
  "check_digit_ok": false,
  "problems": [
    "check digit is 'W' but should be 'V': probably a typo"
  ]
}
```

### `verify_vendor` · gstin=27AAPFU0939F1ZV, pan=AAPFU0939F, ifsc=HDFC0000001, pincode=400018, city=Mumbai, state=Maharashtra

```json
{
  "verdict": "pass",
  "red_flags": [],
  "checked": [
    "address",
    "bank",
    "gstin",
    "pan"
  ],
  "details": {
    "gstin": {
      "gstin": "27AAPFU0939F1ZV",
      "valid": true,
      "state_code": "27",
      "state": "Maharashtra",
      "pan": "AAPFU0939F",
      "holder_type": "Firm / LLP",
      "registration_number": 1,
      "check_digit_ok": true,
      "problems": []
    },
    "pan": {
      "pan": "AAPFU0939F",
      "valid_format": true,
      "holder_type": "Firm / LLP",
      "problems": []
    },
    "bank": {
      "found": true,
      "ifsc": "HDFC0000001",
      "bank": "HDFC Bank",
      "branch": "TULSIANI CHMBRS - NARIMAN PT",
      "address": "101-104 TULSIANI CHAMBERSFREE PRESS JOURNAL MARGNARIMAN POINTMUMBAI MAHARASHTRA 400 021",
      "city": "GREATER MUMBAI",
      "district": "MUMBAI",
      "state": "MAHARASHTRA",
      "contact": "+919890603333",
      "micr": "400240003",
      "swift": "HDFCINBB",
      "supports": {
        "upi": true,
        "neft": true,
        "rtgs": true,
        "imps": true
      }
    },
    "address": {
      "verdict": "match",
      "pincode": "400018",
      "checks": {
        "city": {
          "given": "Mumbai",
          "matches": true,
          "pincode_district": [
            "Mumbai"
          ]
        },
        "state": {
          "given": "Maharashtra",
          "matches": true,
          "pincode_state": [
            "Maharashtra"
          ]
        }
      },
      "post_offices": [
        "Worli",
        "Worli Naka"
      ]
    }
  }
}
```

### `verify_vendor` · gstin=27AAPFU0939F1ZV, pan=AAPFU0939G, ifsc=HDFC0000001, pincode=560001, city=Mumbai, state=Karnataka

```json
{
  "verdict": "fail",
  "red_flags": [
    "PAN AAPFU0939G is not the PAN inside the GSTIN (AAPFU0939F)",
    "city 'Mumbai' does not match PIN code 560001 (Bangalore)",
    "GST registration state (Maharashtra) differs from the address state (Karnataka)"
  ],
  "checked": [
    "address",
    "bank",
    "gstin",
    "pan"
  ],
  "details": {
    "gstin": {
      "gstin": "27AAPFU0939F1ZV",
      "valid": true,
      "state_code": "27",
      "state": "Maharashtra",
      "pan": "AAPFU0939F",
      "holder_type": "Firm / LLP",
      "registration_number": 1,
      "check_digit_ok": true,
      "problems": []
    },
    "pan": {
      "pan": "AAPFU0939G",
      "valid_format": true,
      "holder_type": "Firm / LLP",
      "problems": []
    },
    "bank": {
      "found": true,
      "ifsc": "HDFC0000001",
      "bank": "HDFC Bank",
      "branch": "TULSIANI CHMBRS - NARIMAN PT",
      "address": "101-104 TULSIANI CHAMBERSFREE PRESS JOURNAL MARGNARIMAN POINTMUMBAI MAHARASHTRA 400 021",
      "city": "GREATER MUMBAI",
      "district": "MUMBAI",
      "state": "MAHARASHTRA",
      "contact": "+919890603333",
      "micr": "400240003",
      "swift": "HDFCINBB",
      "supports": {
        "upi": true,
        "neft": true,
        "rtgs": true,
        "imps": true
      }
    },
    "address": {
      "verdict": "partial_match",
      "pincode": "560001",
      "checks": {
        "city": {
          "given": "Mumbai",
          "matches": false,
          "pincode_district": [
            "Bangalore"
          ]
        },
        "state": {
          "given": "Karnataka",
          "matches": true,
          "pincode_state": [
            "Karnataka"
          ]
        }
      },
      "post_offices": [
        "Bangalore ",
        "Bangalore Bazaar",
        "CMM Court Complex",
        "Dr. Ambedkar Veedhi",
        "HighCourt",
        "Legislators Home",
        "Mahatma Gandhi Road",
        "Rajbhavan (Bangalore)",
        "Vasanthanagar",
        "Vidhana Soudha"
      ]
    }
  }
}
```

