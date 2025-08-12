import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as dparser

HEADERS = {'User-Agent': 'med-ref-crawler/1.0 (+https://github.com/<you>/med-ref)'}

def get_html(url: str, timeout=20) -> str:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text

def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, 'lxml')
    # Simple readability-ish: remove scripts/styles
    for tag in soup(['script','style','noscript']):
        tag.decompose()
    return ' '.join(soup.get_text(separator=' ', strip=True).split())

def parse_date_safe(s: str):
    try:
        return dparser.parse(s, fuzzy=True).date().isoformat()
    except Exception:
        return None

def make_source(category: str, name: str, url: str, items: list):
    return {
        'category': category,
        'name': name,
        'url': url,
        'fetched_at': datetime.utcnow().isoformat() + 'Z',
        'items': items
    }
