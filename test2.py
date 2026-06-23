import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import CosineStrategy
from bs4 import BeautifulSoup

async def test():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://html.duckduckgo.com/html/?q=enterprise+software+site:linkedin.com/company")
        
        soup = BeautifulSoup(result.html, "html.parser")
        
        # Find all result links
        results = soup.select(".result")
        print(f"Results found with .result: {len(results)}")
        
        results2 = soup.select(".result__a")
        print(f"Links found with .result__a: {len(results2)}")
        
        # Print first 3 results
        for r in results2[:3]:
            print("---")
            print("Text:", r.get_text())
            print("Href:", r.get("href"))

asyncio.run(test())