import requests
from config import APOLLO_API_KEY

def test_apollo():
    url = "https://api.apollo.io/v1/people/search"
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json"
    }
    payload = {
        "api_key": APOLLO_API_KEY,
        "q_organization_domains": "google.com",
        "person_titles": ["ceo", "founder"],
        "per_page": 1
    }
    res = requests.post(url, headers=headers, json=payload)
    print("Status:", res.status_code)
    try:
        data = res.json()
        people = data.get('people', [])
        if people:
            p = people[0]
            print("Name:", p.get('first_name'), p.get('last_name'))
            print("Email:", p.get('email'))
            print("Phone (contact_number):", p.get('contact_number'))
            org = p.get('organization', {})
            print("Org phone:", org.get('primary_phone', {}))
    except Exception as e:
        print(e)

if __name__ == '__main__':
    test_apollo()
