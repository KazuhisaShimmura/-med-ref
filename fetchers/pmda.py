from .common import make_source, get_html, extract_text, parse_date_safe, collect_links_from_html
from urllib.parse import urljoin

# Entry points (can be tuned later if PMDA IA changes)
BASE_PAGES = [
    # 医療機器の審査・安全対策関連のハブ
    "https://www.pmda.go.jp/review-services/inspections/0001.html",
    # 医療機器のお知らせ（トップ）
    "https://www.pmda.go.jp/medical_devices/",
]

KEYWORDS = ("医療機器", "お知らせ", "通知", "審査", "承認", "認証", "安全", "Q&A")

def fetch_pmda(max_pages=2, max_items_per_page=6):
    items = []
    for i, entry in enumerate(BASE_PAGES[:max_pages]):
        try:
            html = get_html(entry)
        except Exception:
            continue
        for href, label in collect_links_from_html(entry, html, KEYWORDS)[:max_items_per_page]:
            try:
                sub_html = get_html(href)
            except Exception:
                sub_html = ""
            text = extract_text(sub_html)[:1400] if sub_html else ""
            guess_date = parse_date_safe(label) or parse_date_safe(text[:220])
            # Simple summary
            summary = (text[:260] + ("…" if len(text) > 260 else "")) if text else "PMDAページの更新（要詳細確認）。"
            # key facts (heuristic)
            kfs = []
            # pick common words
            for kw in ("承認", "認証", "回収", "Q&A", "安全", "事務連絡"):
                if kw in (label + " " + text):
                    kfs.append(f"含意: {kw}")
            items.append({
                "title": label or "PMDA update",
                "date": guess_date,
                "region": "JP",
                "key_facts": kfs,
                "summary": summary,
                "quote": None,
                "citation": {"type": "web", "publisher": "PMDA", "link": href}
            })
    return [make_source("regulation_and_policy", "PMDA（医療機器・審査/通知）", BASE_PAGES[0], items)]
