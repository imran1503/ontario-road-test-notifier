import requests

URL = "https://www.roadtestnotification.ca/available-dates/"

response = requests.get(URL)

print(response.status_code)
print(response.text[:500])