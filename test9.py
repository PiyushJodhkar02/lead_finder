import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.bing.com/search?q=ai+companies+site:linkedin.com/company",
            magic=True
        )
        print("Length of HTML:", len(result.html))
        if "CAPTCHA" in result.html or "Robot" in result.html:
            print("BLOCKED")
        else:
            print("SUCCESS")

asyncio.run(main())
