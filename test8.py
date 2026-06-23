import requests
url = "https://html.duckduckgo.com/html/?q=ai+companies+site:linkedin.com/company"
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'})
print(r.text[:500])
