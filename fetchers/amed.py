from .common import make_source, get_html, extract_text, parse_date_safe
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# AMED: 公募情報・ニュース
BASE_PAGES = [
    "https://www.amed.go.jp/koubo/index.html",  # 公募情報
    "https://www.amed.go.jp/news/index.html",   # ニュース
]

KEYWORDS = ("公募", "募集", "採択", "研究開発", "事業", "令和", "公示", "助成")

def _collect_links(base_url, html):
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.find_all("a"):
        href = a.get("href") or ""
        text = (a.get_text() or "").strip()
        if not href:
            continue
        full = urljoin(base_url, href)
        if any(k in text for k in KEYWORDS):
            links.append((full, text or full))
    # de-dup
    seen, uniq = set(), []
    for u, t in links:
        if u in seen: 
            continue
        seen.add(u); uniq.append((u, t))
    return uniq

def fetch_amed(max_pages=2, max_items_per_page=8):
    items = []
    for entry in BASE_PAGES[:max_pages]:
        try:
            html = get_html(entry)
        except Exception:
            continue
        for href, label in _collect_links(entry, html)[:max_items_per_page]:
            try:
                sub_html = get_html(href)
            except Exception:
                sub_html = ""
            text = extract_text(sub_html)[:1400] if sub_html else ""
            guess_date = parse_date_safe(label) or parse_date_safe(text[:220])
            summary = (text[:260] + ("…" if len(text) > 260 else "")) if text else "AMEDページの更新（要詳細確認）。"
            kfs = []
            for kw in ("公募", "募集", "採択", "研究開発", "事業", "助成"):
                if kw in (label + " " + text):
                    kfs.append(f"含意: {kw}")
            items.append({
                "title": label or "AMED update",
                "date": guess_date,
                "region": "JP",
                "key_facts": kfs,
                "summary": summary,
                "quote": None,
                "citation": {"type": "web", "publisher": "AMED", "link": href}
            })
    return [make_source("funding_and_grants", "AMED（公募・ニュース）", BASE_PAGES[0], items)]
