from .common import make_source, get_html, extract_text, parse_date_safe
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.pmda.go.jp/review-services/inspections/0001.html"

def fetch_pmda_medical_devices(max_links=8):
    html = get_html(BASE_URL)
    soup = BeautifulSoup(html, "lxml")
    # Find anchor tags that link to relevant updates (assume in main content area)
    main = soup.find("main") or soup
    links = main.find_all("a")
    items = []
    seen = set()
    for a in links:
        href = a.get("href") or ""
        text = (a.get_text() or "").strip()
        if not href or href in seen:
            continue
        seen.add(href)
        # Only capture relevant internal links
        if not href.startswith("http"):
            full_url = urljoin(BASE_URL, href)
        else:
            full_url = href
        if "pmda.go.jp" not in full_url:
            continue
        # Simple filter: skip top-level anchors without context
        if len(text) < 4:
            continue
        # Fetch subpage to get snippet
        try:
            sub_html = get_html(full_url)
        except Exception:
            sub_html = ""
        text_excerpt = extract_text(sub_html)[:1200] if sub_html else ""
        guess_date = parse_date_safe(text) or parse_date_safe(text_excerpt[:200])
        summary = (text_excerpt[:260] + ("…" if len(text_excerpt) > 260 else "")) if text_excerpt else "PMDAページの更新（要詳細確認）。"
        items.append({
            "title": text or "PMDA update",
            "date": guess_date,
            "region": "JP",
            "key_facts": [],
            "summary": summary,
            "quote": None,
            "citation": {"type": "web", "publisher": "PMDA", "link": full_url}
        })
        if len(items) >= max_links:
            break
    return [make_source("regulation_and_policy",
                        "PMDA – 医療機器関連通知・お知らせ",
                        BASE_URL,
                        items)]
