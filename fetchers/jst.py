from .common import make_source, get_html, extract_text, parse_date_safe
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# JST: 公募情報（総合）
BASE_PAGES = [
    "https://www.jst.go.jp/koubo/",
]

KEYWORDS = ("公募", "募集", "予告", "採択", "助成", "研究", "事業", "学術", "プログラム")

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

def fetch_jst(max_pages=1, max_items_per_page=10):
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
            summary = (text[:260] + ("…" if len(text) > 260 else "")) if text else "JSTページの更新（要詳細確認）。"
            kfs = []
            for kw in ("公募", "募集", "予告", "採択", "助成", "研究", "事業"):
                if kw in (label + " " + text):
                    kfs.append(f"含意: {kw}")
            items.append({
                "title": label or "JST update",
                "date": guess_date,
                "region": "JP",
                "key_facts": kfs,
                "summary": summary,
                "quote": None,
                "citation": {"type": "web", "publisher": "JST", "link": href}
            })
    return [make_source("funding_and_grants", "JST（公募情報）", BASE_PAGES[0], items)]
