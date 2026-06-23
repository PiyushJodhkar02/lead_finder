# AI Lead Finder — Project Blueprint

## What this project does
This is a Python tool for an AI services company.
It finds potential client companies by searching LinkedIn via Google,
scores each company using Gemini AI, enriches contact data via Apollo.io,
and exports a ranked list to CSV and Excel.

## Our company context
We are an AI services company providing:
- Custom AI agent development
- AI workflow automation  
- AI chatbot development
- Machine learning model development
- Data pipeline automation

Our ideal customers are mid-size to enterprise companies (50–5000 employees)
with manual repetitive processes, large data volumes, or customer service
operations that could benefit from AI automation.

## Two input modes
Mode A: User describes their service → Gemini extracts search keywords
Mode B: User types a keyword directly → used as-is

## Tech stack
- Python 3.11+
- crawl4ai (web scraping)
- playwright (browser automation)
- google-generativeai (Gemini Flash API — free)
- requests (Apollo.io API calls)
- python-dotenv (env vars)
- pydantic (data models)
- openpyxl (Excel export)

## API keys needed
- GEMINI_API_KEY → get free at aistudio.google.com
- APOLLO_API_KEY → get free at apollo.io (10k credits/month free)
Both stored in .env file only. Never hardcoded.

## File structure to create
.env                  - API keys (template only)
requirements.txt      - all pip dependencies
GEMINI.md             - this file
config.py             - all settings, prompts, constants
models/business.py    - Pydantic data model for a company
main.py               - scraper + keyword extractor + scorer
enrich.py             - Apollo.io contact enrichment
export.py             - CSV + Excel export with color coding

## Data model (models/business.py)
Each company record has:
company_name, industry, linkedin_url, website,
description, company_size, location,
email, phone, fit_score (0-100), fit_reason

## Scraping logic (main.py)
- Search URL: https://www.google.com/search?q={keyword}+company+site:linkedin.com/company&start={page}
- CSS selector: #search
- Pages per keyword: 3 (= ~30 results)
- Max total companies: 100
- Deduplicate by company_name (case insensitive)
- Pass scraped HTML to Gemini to extract structured company JSON
- Then score each company with a second Gemini call
- Add 1 second delay between Gemini calls

## Gemini prompt for keyword extraction
Given a description of an AI services company,
return 5 specific B2B industry keywords to find potential customers.
Return as JSON: { "keywords": ["...", "...", "...", "...", "..."] }

## Gemini prompt for scraping
From Google search result HTML, extract company info as JSON array:
[{ company_name, linkedin_url, website, industry, description, company_size }]
Only return companies. Ignore job postings and individual profiles.
Strip any markdown code blocks before parsing JSON.

## Gemini scoring prompt
Rate each company's fit for our AI services on a scale of 0-100.
Return JSON: { "fit_score": number, "fit_reason": "one sentence" }
Score guide:
80-100 = perfect fit (clear AI automation use cases)
60-79  = good fit (likely pain points)
40-59  = possible fit
0-39   = poor fit

## Apollo.io enrichment (enrich.py)
Endpoint: GET https://api.apollo.io/v1/organizations/enrich
Params: api_key, domain (extracted from website URL)
Extract: primary_phone, email, estimated_num_employees, city, country
Add 2 second delay between calls
Skip rows where website is empty
Save to enriched_leads.csv

## Export (export.py)
1. Print top 20 companies as a table in terminal
2. Save to final_leads.xlsx with:
   - Bold header row
   - Auto-sized columns
   - Color coded rows: green (80+), yellow (60-79), orange (40-59), red (below 40)
3. Print summary: total / avg score / emails found / phones found

## Error handling rules
- Wrap every API call in try/except
- If Gemini returns markdown code blocks, strip ```json and ``` before parsing
- If Apollo returns no data, keep original values and continue
- Print clear progress messages throughout: "Scraping page 1 for keyword: logistics..."

## Run order
python main.py              # scrape + score → businesses_data.csv
python main.py "keyword"    # same but with direct keyword
python enrich.py            # enrich → enriched_leads.csv
python export.py            # export → final_leads.xlsx