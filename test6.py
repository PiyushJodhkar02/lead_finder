import requests
from bs4 import BeautifulSoup
url = "https://html.duckduckgo.com/html/?q=ai+companies+site:linkedin.com/company"
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(r.text, 'html.parser')
form = soup.select_one('.nav-link form')
if form:
    print("Form action:", form.get('action'))
    for inp in form.select('input'):
        print(inp.get('name'), inp.get('value'))
else:
    print("No next form found")
