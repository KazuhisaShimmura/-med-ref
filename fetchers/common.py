import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as dparser

from urllib.parse import urljoin
HEADERS = {'User-Agent': 'med-ref-crawler/1.0 (+https://github.com/KazuhisaShimmura/-med-ref)'}

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

def collect_links_from_html(base_url: str, html: str, keywords: tuple) -> list[tuple[str, str]]:
    """Generic link collector based on keywords in link text or href."""
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.find_all("a"):
        href = a.get("href") or ""
        text = (a.get_text() or "").strip()
        if not href:
            continue
        
        if any(k in text for k in keywords) or any(k in href for k in ("medical_devices", "notice", "qa", "info")):
            full_url = urljoin(base_url, href)
            links.append((full_url, text or full_url))
            
    seen, uniq = set(), []
    for url, text in links:
        if url not in seen:
            seen.add(url); uniq.append((url, text))
    return uniq
