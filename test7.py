import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.google.com/search?q=ai+companies+site:linkedin.com/company&start=10",
            magic=True
        )
        print("Length of HTML:", len(result.html))
        if "our systems have detected unusual traffic" in result.html.lower() or "sorry" in result.html.lower():
            print("BLOCKED")
        else:
            print("SUCCESS")

asyncio.run(main())
