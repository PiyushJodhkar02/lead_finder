import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")

# Constants
MAX_PAGES_PER_KEYWORD = 3
MAX_COMPANIES = 100
DELAY_BETWEEN_GEMINI_CALLS = 4.0
DELAY_BETWEEN_APOLLO_CALLS = 2.0

# Prompts
KEYWORD_EXTRACTION_PROMPT = """
Given a description of an AI services company,
return 5 specific B2B industry keywords to find potential customers.
Return as JSON: {{ "keywords": ["...", "...", "...", "...", "..."] }}

Description:
{description}
"""

SCRAPING_PROMPT = """
From the following Google search result HTML, extract company info as a JSON array of objects.
Keys should exactly be: company_name, linkedin_url, website, industry, description, company_size
Only return companies. Ignore job postings and individual profiles.
Return ONLY valid JSON array.

HTML:
{html}
"""

SCORING_PROMPT = """
Rate this company's fit for our AI services on a scale of 0-100 based on their profile.
Our AI services include custom agent development, workflow automation, chatbots, ML models, data pipelines.
Ideal customers are mid-size to enterprise (50-5000 employees) with manual repetitive processes, large data volumes, or customer service operations.

Score guide:
80-100 = perfect fit (clear AI automation use cases)
60-79  = good fit (likely pain points)
40-59  = possible fit
0-39   = poor fit

Return ONLY JSON: {{ "fit_score": number, "fit_reason": "one sentence" }}

Company Info:
{company_info}
"""
