import os
import json
import requests
from datetime import datetime
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

#Complete reference list of all DriveTest centres in Ontario
ALL_LOCATIONS = [
    "Bancroft", "Barrie", "Belleville", "Blind River", "Brampton", "Brantford",
    "Brockville", "Burlington", "Chatham", "Clinton", "Collingwood", "Cornwall",
    "Dryden", "Elliot Lake", "Espanola", "Fort Frances", "Guelph", "Hamilton",
    "Hawkesbury", "Hearst", "Huntsville", "Kapuskasing", "Kenora", "Kingston",
    "Kirkland Lake", "Kitchener", "Lindsay", "London", "Marathon", "Mississauga",
    "Moosonee", "New Liskeard", "Newmarket", "North Bay", "Oakville", "Orangeville",
    "Orillia", "Oshawa", "Ottawa Canotek", "Ottawa Walkley", "Owen Sound",
    "Parry Sound", "Pembroke", "Peterborough", "Port Hope", "Renfrew", "Sarnia",
    "Sault Ste Marie", "Simcoe", "Smiths Falls", "St Catharines", "Stratford",
    "Sudbury", "Thunder Bay", "Tillsonburg", "Timmins", "Toronto Downsview",
    "Toronto Etobicoke", "Toronto Metro East", "Toronto Port Union", "Walkerton",
    "Wawa", "Windsor", "Woodstock"
]
ALL_LICENSE_TYPES = ["G2", "G"]

#User configuration: change these to your preferred locations and license types
MY_LOCATIONS = ["Barrie", "Orillia"]
MY_LICENSE_TYPES = ["G"]
MY_NAME = "Artemis"
MY_APPOINTMENT = "Oct 20 2026" #Please use format like 'Oct 20 2026' or '2026-10-20'."


"""
Returns True if date_str is after cutoff_str; otherwise returns False.
"""
def is_after_cutoff(date_str, cutoff_str):
   
    # Parse the scraped date 
    try:
        date_obj = datetime.strptime(date_str, "%B %d, %Y")
    except ValueError:
        print(f"Warning: Could not parse scraped date '{date_str}'")
        return True # If we can't parse it, treat it as after cutoff (ignore it)

    # Parse the user cutoff date
    cutoff_obj = None
    for fmt in ("%b %d %Y", "%B %d, %Y", "%Y-%m-%d"):
        try:
            cutoff_obj = datetime.strptime(cutoff_str, fmt)
            break
        except ValueError:
            continue
            
    if cutoff_obj is None:
        print(f"Warning: Could not parse cutoff date '{cutoff_str}'. Please use format like 'Oct 20 2026' or '2026-10-20'.")
        return False # Default to False (don't ignore) if cutoff is misconfigured

    # Return True if the available date is strictly after the cutoff
    return date_obj > cutoff_obj



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
    
    # Extract every unique location currently on the site
    active_locations = sorted(list(set(row["location"] for row in all_available)))

    # Uncomment to print every location currently active on the site.
    # print("=================================================")
    # print("ALL ACTIVE LOCATIONS CURRENTLY ON SITE:")
    # print("=================================================")
    # for loc in active_locations:
    #     print(f'    "{loc}",')
    # print("=================================================\n")

    # Filter by your locations and license types, AND check the date cutoff
    my_available = []
    for row in all_available:
        if row["location"] in MY_LOCATIONS and row["test_type"] in MY_LICENSE_TYPES:
            # Only keep the appointment if it is NOT after the cutoff date
            if not is_after_cutoff(row["date"], MY_APPOINTMENT):
                my_available.append(row)

    # Load the list of appointments we've already emailed about
    notified = load_notified()

    # Find only the NEW appointments
    new_matches = []
    for match in my_available:
        # Create a unique ID for this specific appointment
        uid = f"{match['location']}|{match['test_type']}|{match['date']}"
        if uid not in notified:
            new_matches.append(match)
            notified.append(uid)

    print(f"Total dates found on site: {len(all_available)}")
    print(f"Dates matching your filters and cutoff date: {len(my_available)}")
    print(f"New dates not previously emailed: {len(new_matches)}")
    print("-----------------------------------------------")
    
    if not new_matches:
        print("No new dates found since last email. Skipping email.")
        save_notified(notified)  # Saves the file anyway to prevent GitHub Action errors
    else:
        print("Sending email for new dates...")
        send_email(new_matches)
        save_notified(notified)

if __name__ == "__main__":
    main()