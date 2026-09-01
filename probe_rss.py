import requests
from bs4 import BeautifulSoup
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
r = requests.get('https://letterboxd.com/mfhcor/rss/', headers=headers)
soup = BeautifulSoup(r.content, 'xml')
items = soup.find_all('item')
print('Total items:', len(items))

for item in items[:3]:
    watched = item.find('letterboxd:watchedDate')
    desc = item.find('description')
    title_el = item.find('letterboxd:filmTitle')
    print('Title:', title_el.text.strip() if title_el else 'N/A')
    print('Watched:', watched.text.strip() if watched else 'N/A')
    print('Desc snippet:', repr(desc.text[:200]) if desc else 'N/A')
    img_match = re.search(r'img src="([^"]+)"', desc.text if desc else '')
    print('Poster:', img_match.group(1) if img_match else 'N/A')
    print()
