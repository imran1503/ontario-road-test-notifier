import json
import requests
from bs4 import BeautifulSoup
from urllib3 import Retry
from requests.adapters import HTTPAdapter

URL = "https://www.roadtestnotify.ca/available-dates/"

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
Fetches the HTML from the URL.
Retries up to 4 times on server errors, then returns the page text OR requests.exceptions.HTTPError / net error.
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

def parse_dates(html):
    soup = BeautifulSoup(html, "html.parser")
    available = []
    tables = soup.find_all("table")

    for table in tables:
        for row in table.find_all("tr"):
            cols = [col.get_text(strip=True) for col in row.find_all(["td", "th"])]
            if len(cols) >= 4:
                if cols[0].lower() in ["location", "centre"]:
                    continue
                available.append({
                    "location": cols[0],
                    "test_type": cols[1],
                    "date": cols[2],
                    "duration": cols[3]
                })
    return available

def main():
    html = fetch_data()
    all_available = parse_dates(html)
    
    # TEMPORARY DEBUG: Print every appointment on the site
    print("ALL AVAILABLE DATES ON SITE:")
    print(json.dumps(all_available, indent=2))
    return
    
    # The code below is paused for now
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