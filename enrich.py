import csv
import sys
import time
import requests
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# Headers to prevent blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Regex patterns
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
# Basic phone pattern: looks for + followed by digits/spaces/dashes, or (123) 456-7890
PHONE_PATTERN = re.compile(r'(?:\+?\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}')

def extract_contacts_from_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text(separator=" ")
    
    # Find all emails
    raw_emails = EMAIL_PATTERN.findall(text)
    # Filter out fake emails like example@domain or .png extensions
    emails = []
    for e in raw_emails:
        if "example" not in e.lower() and not e.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            emails.append(e)
            
    # Find all phones
    raw_phones = PHONE_PATTERN.findall(text)
    phones = [p.strip() for p in raw_phones if len(re.sub(r'\D', '', p)) >= 10]
    
    # Return the first found or empty
    return {
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else ""
    }

def scrape_company_website(website: str) -> dict:
    if not website or " " in website or "." not in website:
        return {}
        
    if not website.startswith("http"):
        website = "http://" + website
        
    try:
        # Visit Homepage
        res = requests.get(website, headers=HEADERS, timeout=8)
        contacts = extract_contacts_from_html(res.text)
        
        # If no email found, try to find a Contact page and scrape that
        if not contacts["email"] or not contacts["phone"]:
            soup = BeautifulSoup(res.text, "html.parser")
            contact_link = None
            for a in soup.find_all("a", href=True):
                if "contact" in a.text.lower() or "contact" in a["href"].lower():
                    contact_link = urljoin(website, a["href"])
                    break
                    
            if contact_link:
                try:
                    c_res = requests.get(contact_link, headers=HEADERS, timeout=10)
                    c_contacts = extract_contacts_from_html(c_res.text)
                    if not contacts["email"]: contacts["email"] = c_contacts["email"]
                    if not contacts["phone"]: contacts["phone"] = c_contacts["phone"]
                except Exception:
                    pass
                    
        return contacts
    except Exception as e:
        print(f"Error scraping {website}: {e}")
        return {}

def main():
    try:
        with open("businesses_data.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        print("businesses_data.csv not found. Please run main.py first.")
        sys.exit(1)

    enriched_rows = []
    
    print(f"Loaded {len(rows)} companies. Starting custom web scraping for contacts...")
    
    for row in rows:
        website = row.get("website", "")
        if not website:
            enriched_rows.append(row)
            continue
            
        print(f"Scraping: {row.get('company_name')} ({website})...")
        contacts = scrape_company_website(website)
        
        if contacts.get("email"):
            row["email"] = contacts["email"]
        if contacts.get("phone"):
            row["phone"] = contacts["phone"]
            
        enriched_rows.append(row)
        time.sleep(1) # Be nice to servers
        
    if enriched_rows:
        keys = enriched_rows[0].keys()
        with open("enriched_leads.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(enriched_rows)
        print(f"Saved {len(enriched_rows)} enriched companies to enriched_leads.csv")

if __name__ == "__main__":
    main()
