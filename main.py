import sys
import json
import csv
import time
import random
import asyncio
import urllib.parse
from bs4 import BeautifulSoup
from groq import Groq
from google import genai
import os
from crawl4ai import AsyncWebCrawler
from config import (
    GROQ_API_KEY, GEMINI_API_KEY, MAX_COMPANIES,
    DELAY_BETWEEN_GEMINI_CALLS, KEYWORD_EXTRACTION_PROMPT,
    SCORING_PROMPT
)
from models.business import Business

if not GROQ_API_KEY or not GEMINI_API_KEY:
    print("Warning: Missing API keys in .env. Falling back to whichever is available.")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

GROQ_MODEL = "llama-3.1-8b-instant"
GEMINI_MODEL = "gemini-2.0-flash"

def clean_json_response(text: str) -> str:
    if not text:
        return "[]"
    # Find the first '[' and last ']'
    start_idx = text.find('[')
    end_idx = text.rfind(']')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx+1]
        
    # Fallback to dictionary extraction if array not found
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx+1]
        
    return text.replace("```json", "").replace("```", "").strip()

def generate_with_retry(prompt: str) -> str:
    max_retries = 3
    for attempt in range(max_retries):
        # Primary: Groq
        if groq_client:
            try:
                response = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                print("[API] Groq success")
                return response.choices[0].message.content
            except Exception as e:
                print(f"[API] Groq error: {e}")
        
        # Fallback: Gemini
        if gemini_client:
            try:
                response = gemini_client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                )
                print("[API] Gemini success")
                return response.text
            except Exception as e:
                print(f"[API] Gemini error: {e}")
                
        # If both fail, wait and retry
        wait_time = 15 * (attempt + 1)
        print(f"Both APIs hit limits or failed. Waiting {wait_time}s before retrying...")
        time.sleep(wait_time)
        
    return ""

def get_keywords(description: str) -> list[str]:
    print("Extracting keywords using Gemini...")
    prompt = KEYWORD_EXTRACTION_PROMPT.format(description=description)
    try:
        text = generate_with_retry(prompt)
        if not text:
            return []
        data = json.loads(clean_json_response(text))
        return data.get("keywords", [])
    except Exception as e:
        print(f"Error parsing keywords: {e}")
        return []

def extract_companies_from_ddg(html: str) -> list[dict]:
    # Parse HTML to reduce payload size to Gemini
    soup = BeautifulSoup(html, "html.parser")
    results = soup.select(".result")
    
    snippets = []
    for r in results:
        snippets.append(r.get_text(" ", strip=True))
    
    clean_text = "\n".join(snippets)
    
    # Use config prompt and format it
    from config import SCRAPING_PROMPT
    prompt = SCRAPING_PROMPT.format(html=clean_text)
    
    print("Extracting company details via Gemini/Groq...")
    text = generate_with_retry(prompt)
    if not text:
        return []
        
    try:
        companies = json.loads(clean_json_response(text))
        if isinstance(companies, list):
            return companies
        return []
    except Exception as e:
        print(f"Error parsing extraction JSON: {e}")
        return []

def score_company(company_info: dict) -> tuple[int, str]:
    prompt = SCORING_PROMPT.format(company_info=json.dumps(company_info))
    try:
        time.sleep(DELAY_BETWEEN_GEMINI_CALLS)
        text = generate_with_retry(prompt)
        if not text:
            return 0, ""
        data = json.loads(clean_json_response(text))
        return data.get("fit_score", 0), data.get("fit_reason", "")
    except Exception as e:
        print(f"Error scoring company: {e}")
        return 0, ""

async def scrape_duckduckgo(crawler: AsyncWebCrawler, keyword: str, seen_companies: set) -> list[Business]:
    businesses = []
    
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(keyword)}+site:linkedin.com/company"
    print(f"Scraping DuckDuckGo for keyword: {keyword}...")
    
    try:
        time.sleep(random.uniform(2, 4))
        result = await crawler.arun(
            url=url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            },
            wait_for="css:.result",
            delay_before_return_html=2.0,
            magic=True
        )
        
        if not result.html:
            print("Failed to fetch page. No HTML returned.")
            return businesses
            
        html = result.html
        raw_companies = extract_companies_from_ddg(html)
        
        for c_data in raw_companies:
            c_name = c_data.get("company_name", "")
            if not c_name or c_name.lower() in seen_companies:
                continue
                
            seen_companies.add(c_name.lower())
            print(f"Found: {c_name}. Scoring...")
            score, reason = score_company(c_data)
            c_data["fit_score"] = score
            c_data["fit_reason"] = reason
            
            try:
                business = Business(**c_data)
                businesses.append(business)
            except Exception as e:
                print(f"Error mapping to Business model: {e}")
    except Exception as e:
        print(f"Error scraping DuckDuckGo: {e}")
            
    return businesses

def load_existing_businesses() -> tuple[list, set]:
    businesses = []
    seen = set()
    try:
        with open("businesses_data.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    b = Business(**row)
                    businesses.append(b)
                    if b.company_name:
                        seen.add(b.company_name.lower())
                except Exception as e:
                    pass
    except FileNotFoundError:
        pass
    return businesses, seen

async def run_main(keywords: list[str]):
    all_businesses, seen_companies = load_existing_businesses()
    initial_count = len(all_businesses)
    
    print(f"Loaded {initial_count} existing companies from businesses_data.csv")
    
    # We create 3 variations of each keyword to get ~30 companies total
    expanded_keywords = []
    for kw in keywords:
        expanded_keywords.append(f"{kw}")
        expanded_keywords.append(f"{kw} software")
        expanded_keywords.append(f"{kw} services")
    
    async with AsyncWebCrawler() as crawler:
        for kw in expanded_keywords:
            if len(all_businesses) - initial_count >= MAX_COMPANIES:
                break
            results = await scrape_duckduckgo(crawler, kw, seen_companies)
            all_businesses.extend(results)
        
    # Truncate to MAX_COMPANIES of newly found + existing
    all_businesses = all_businesses[:initial_count + MAX_COMPANIES]
    
    # Save to CSV
    if not all_businesses:
        print("No companies found.")
        return

    # Use explicit keys to match the user request order
    keys = ["company_name", "linkedin_url", "website", "industry", "description", "company_size", "location", "email", "phone", "fit_score", "fit_reason"]
    try:
        with open("businesses_data.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            for b in all_businesses:
                writer.writerow(b.model_dump())
        print(f"Saved {len(all_businesses)} companies to businesses_data.csv")
    except PermissionError:
        fallback = "businesses_data_fallback.csv"
        print(f"\n[WARNING] businesses_data.csv is open in another program (like Excel)!")
        with open(fallback, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            for b in all_businesses:
                writer.writerow(b.model_dump())
        print(f"Saved {len(all_businesses)} companies to {fallback} instead.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
        print(f"Using direct keyword: {keyword}")
        keywords = [keyword]
    else:
        print("Mode A: Enter a description of your AI services to generate keywords.")
        desc = input("Description: ")
        if not desc.strip():
            desc = "We provide custom AI agent development and workflow automation for mid-size companies."
        keywords = get_keywords(desc)
        print(f"Generated keywords: {keywords}")
        
    asyncio.run(run_main(keywords))
