import requests
from urllib3 import Retry

URL = "https://www.roadtestnotify.ca/available-dates/"

retry = Retry(
    total=4,
    connect=4,
    read=4,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    respect_retry_after_header=True,
)
response = requests.get(URL)

print(response.status_code)
print(response.text[:500])