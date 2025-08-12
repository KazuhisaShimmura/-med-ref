from .common import make_source, get_html, extract_text, parse_date_safe, collect_links_from_html

BASE_URL = "https://www.pmda.go.jp/review-services/inspections/0001.html"
# Use keywords to find relevant links, similar to other PMDA fetchers
KEYWORDS = ("医療機器", "審査", "安全", "通知", "お知らせ", "回収", "不具合", "事務連絡")

def fetch_pmda_medical_devices(max_links=8):
    html = get_html(BASE_URL)
    # Use the robust, common link collector for consistency
    links = collect_links_from_html(BASE_URL, html, KEYWORDS, domain_filter="pmda.go.jp")

    items = []
    for full_url, text in links[:max_links]:
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
            "key_facts": [], # Key fact extraction can be added later if needed
            "summary": summary,
            "quote": None,
            "citation": {"type": "web", "publisher": "PMDA", "link": full_url}
        })

    return [make_source("regulation_and_policy",
                        "PMDA – 医療機器関連通知・お知らせ",
                        BASE_URL,
                        items)]
