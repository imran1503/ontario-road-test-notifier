import json
import requests
from urllib3 import Retry


URL = "https://www.roadtestnotify.ca/statistics_data/bookable_dates.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

ALL_LOCATIONS = [
    "Barrie",
    "Belleville",
    "Brantford",
    "Burlington",
    "Collingwood",
    "Fort Frances",
    "Guelph",
    "Kingston",
    "Kitchener",
    "London",
    "Mississauga",
    "Newmarket",
    "Oakville",
    "Orangeville",
    "Oshawa",
    "Ottawa Walkley",
    "Smiths Falls",
    "St Catharines",
    "Stratford",
    "Sudbury",
    "Toronto Downsview",
    "Toronto Etobicoke",
    "Toronto Port Union",
    "Walkerton",
    "Winchester"
]
ALL_LICENSE_TYPES = ["G2", "G"]
#Where you set what locations you want to monitor. You can add more locations from the ALL_LOCATIONS list above.
MY_LOCATIONS = ["Barrie"]
MY_LICENSE_TYPES = ["G"]

"""
Fetches the JSON from the URL.
Retries up to 4 times on server errors, then returns the JSON text OR requests.exceptions.HTTPError / net error.
"""
def fetch_data():
    session = requests.Session()
    
    retries = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True
    )
    
    session.mount("https://", HTTPAdapter(max_retries=retries))
    
    response = session.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status() 
    return response.text

def parse_dates(json_text):
    payload = json.loads(json_text)
    raw_rows = payload.get("rows", [])
    
    available = []
    for row in raw_rows:
        available.append({
            "location": row.get("testCentre", ""),
            "test_type": row.get("testType", ""),
            "date": row.get("availableDateLabel") or row.get("availableDate", ""),
            "duration": row.get("updatedAtEpochMs", "")
        })
    return available

def main():
    json_text = fetch_data()
    all_available = parse_dates(json_text)
    
    my_available = [
        row for row in all_available 
        if row["location"] in MY_LOCATIONS and row["test_type"] in MY_LICENSE_TYPES
    ]

    print(f"Total dates found on site: {len(all_available)}")
    print(f"Dates matching your hardcoded locations: {len(my_available)}")
    print("-----------------------------------------------")
    
    if not my_available:
        print("No dates found for your selected locations right now.")
    else:
        print(json.dumps(my_available, indent=2))

if __name__ == "__main__":
    main()