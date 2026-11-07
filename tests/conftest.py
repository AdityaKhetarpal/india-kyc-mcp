"""Fake versions of the two public APIs, so the tests run offline and never depend on someone else's server.
The shapes follow the real responses (Razorpay IFSC API, api.postalpincode.in)."""
import httpx
import pytest

from india_kyc_mcp import server as server_module
from india_kyc_mcp.lookups import Lookups

IFSC = {
    "HDFC0000001": {
        "BANK": "HDFC Bank", "IFSC": "HDFC0000001", "BRANCH": "SANDOZ HOUSE", "ADDRESS": "SANDOZ HOUSE, WORLI, MUMBAI",
        "CITY": "MUMBAI", "DISTRICT": "MUMBAI", "STATE": "MAHARASHTRA", "CONTACT": "+912261606161",
        "MICR": "400240002", "SWIFT": "HDFCINBB", "UPI": True, "NEFT": True, "RTGS": True, "IMPS": True, "BANKCODE": "HDFC",
    },
    "KKBK0000261": {
        "BANK": "Kotak Mahindra Bank", "IFSC": "KKBK0000261", "BRANCH": "GURGAON", "ADDRESS": "JMD REGENT SQUARE, GURGAON",
        "CITY": "GURGAON", "DISTRICT": "GURGAON", "STATE": "HARYANA", "CONTACT": "", "MICR": "110485003", "SWIFT": "",
        "UPI": True, "NEFT": True, "RTGS": True, "IMPS": True, "BANKCODE": "KKBK",
    },
}


def office(name, district, state, pin, delivery="Delivery", branch="Sub Post Office", block="NA"):
    return {"Name": name, "BranchType": branch, "DeliveryStatus": delivery, "District": district, "State": state,
            "Block": block, "Pincode": pin, "Country": "India"}


PINS = {
    "110001": [office("Connaught Place", "Central Delhi", "Delhi", "110001", branch="Head Post Office", block="New Delhi"),
               office("Baroda House", "New Delhi", "Delhi", "110001", "Non-Delivery")],
    "560001": [office("Bangalore G.P.O.", "Bengaluru", "Karnataka", "560001", branch="Head Post Office", block="Bangalore North"),
               office("Vidhana Soudha", "Bengaluru", "Karnataka", "560001")],
    "400018": [office("Worli", "Mumbai", "Maharashtra", "400018")],
}
PLACES = {"connaught place": [office("Connaught Place", "Central Delhi", "Delhi", "110001")]}


FLAKY = {"left": 0}


def handler(request: httpx.Request) -> httpx.Response:
    host, path = request.url.host, request.url.path
    if host == "ifsc.razorpay.com":
        code = path.strip("/")
        if code == "HDFC0000503":  # pretend the service is down for this one
            return httpx.Response(503, text="Service Unavailable")
        if code == "HDFC0000504" and FLAKY["left"] > 0:  # down once, then fine
            FLAKY["left"] -= 1
            return httpx.Response(503, text="Service Unavailable")
        if code == "HDFC0000504":
            return httpx.Response(200, json={**IFSC["HDFC0000001"], "IFSC": "HDFC0000504"})
        return httpx.Response(200, json=IFSC[code]) if code in IFSC else httpx.Response(404, text='"Not Found"')
    if host == "api.postalpincode.in" and path.startswith("/pincode/"):
        pin = path.rsplit("/", 1)[1]
        if pin in PINS:
            return httpx.Response(200, json=[{"Message": f"Number of pincode(s) found:{len(PINS[pin])}",
                                              "Status": "Success", "PostOffice": PINS[pin]}])
        return httpx.Response(200, json=[{"Message": "No records found", "Status": "Error", "PostOffice": None}])
    if host == "api.postalpincode.in" and path.startswith("/postoffice/"):
        name = httpx.URL(str(request.url)).path.rsplit("/", 1)[1].lower()
        rows = PLACES.get(name)
        if rows:
            return httpx.Response(200, json=[{"Message": "found", "Status": "Success", "PostOffice": rows}])
        return httpx.Response(200, json=[{"Message": "No records found", "Status": "Error", "PostOffice": None}])
    return httpx.Response(500)


class Counter:
    def __init__(self):
        self.calls = 0

    def __call__(self, request):
        self.calls += 1
        return handler(request)


@pytest.fixture
def fake_api(monkeypatch):
    monkeypatch.setattr("india_kyc_mcp.lookups.RETRY_DELAY", 0)
    counter = Counter()
    client = httpx.AsyncClient(transport=httpx.MockTransport(counter))
    fresh = Lookups(client=client)
    monkeypatch.setattr(server_module, "lookups", fresh)
    fresh.counter = counter
    return fresh
