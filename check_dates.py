import os
import json
import requests
from urllib3 import Retry
from requests.adapters import HTTPAdapter

# Try to load .env file for local testing
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

URL = "https://www.roadtestnotify.ca/statistics_data/bookable_dates.json"
NOTIFIED_FILE = "notified_dates.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

ALL_LOCATIONS = [
    "Barrie", "Belleville", "Brantford", "Burlington", "Collingwood",
    "Fort Frances", "Guelph", "Kingston", "Kitchener", "London",
    "Mississauga", "Newmarket", "Oakville", "Orangeville", "Oshawa",
    "Ottawa Walkley", "Smiths Falls", "St Catharines", "Stratford",
    "Sudbury", "Toronto Downsview", "Toronto Etobicoke", "Toronto Port Union",
    "Walkerton", "Winchester"
]
ALL_LICENSE_TYPES = ["G2", "G"]

#User configuration: change these to your preferred locations and license types
MY_LOCATIONS = ["Barrie"]
MY_LICENSE_TYPES = ["G2"]
MY_NAME = "Artemis"



def fetch_data():
    session = requests.Session()
    
    retries = Retry(
        total=4, connect=4, read=4, backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"], respect_retry_after_header=True
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

def load_notified():
    if os.path.exists(NOTIFIED_FILE):
        with open(NOTIFIED_FILE, "r") as f:
            return json.load(f)
    return []

def save_notified(notified_list):
    # Keep only the last 200 entries so the file doesn't grow forever
    notified_list = notified_list[-200:]
    with open(NOTIFIED_FILE, "w") as f:
        json.dump(notified_list, f, indent=2)

def send_email(matches):
    service_id = os.getenv("EMAILJS_SERVICE_ID")
    template_id = os.getenv("EMAILJS_TEMPLATE_ID")
    public_key = os.getenv("EMAILJS_PUBLIC_KEY")
    private_key = os.getenv("EMAILJS_PRIVATE_KEY")

    if not all([service_id, template_id, public_key]):
        print("EmailJS credentials not set. Skipping email.")
        return

    rows_html = ""
    for match in matches:
        rows_html += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{match['location']}</td>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>{match['test_type']}</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{match['date']}</td>
        </tr>
        """

    body_html = f"""
    <table style="border-collapse: collapse; width: 100%; max-width: 600px; font-family: Arial, sans-serif;">
        <thead>
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Location</th>
                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Type</th>
                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Date</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """

    url = "https://api.emailjs.com/api/v1.0/email/send"
    headers = { "Content-Type": "application/json" }
    payload = {
        "service_id": service_id,
        "template_id": template_id,
        "user_id": public_key,
        "template_params": {
            "from_name": "Road Test Bot",
            "user_email": "bot@roadtestnotifier.ca",
            "user_name": MY_NAME,
            "message": body_html
        }
    }
    
    if private_key:
        payload["accessToken"] = private_key

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("Email sent successfully via EmailJS!")
        else:
            print(f"Failed to send EmailJS. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Failed to send EmailJS: {e}")

def main():
    json_text = fetch_data()
    all_available = parse_dates(json_text)
    
    # 1. Filter by your locations and license types
    my_available = [
        row for row in all_available 
        if row["location"] in MY_LOCATIONS and row["test_type"] in MY_LICENSE_TYPES
    ]

    # 2. Load the list of appointments we've already emailed about
    notified = load_notified()

    # 3. Find only the NEW appointments
    new_matches = []
    for match in my_available:
        # Create a unique ID for this specific appointment
        uid = f"{match['location']}|{match['test_type']}|{match['date']}"
        if uid not in notified:
            new_matches.append(match)
            notified.append(uid)

    print(f"Total dates found on site: {len(all_available)}")
    print(f"Dates matching your selected locations: {len(my_available)}")
    print(f"New dates not previously emailed: {len(new_matches)}")
    print("-----------------------------------------------")
    
    if not new_matches:
        print("No new dates found since last email. Skipping email.")
    else:
        print("Sending email for new dates...")
        send_email(new_matches)
        save_notified(notified)

if __name__ == "__main__":
    main()