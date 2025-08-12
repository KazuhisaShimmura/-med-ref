from .common import make_source, get_html, extract_text, parse_date_safe, collect_links_from_html

BASE_URL = "https://www.fda.gov/medical-devices/digital-health-center-excellence"

# FDA Digital Health Center Excellence: news/updates live under the same hub or child pages
KEYWORDS = ("Digital Health", "AI", "SaMD", "software", "guidance", "news", "update", "framework")

def fetch_fda(max_items=8):
    items = []
    try:
        html = get_html(BASE_URL)
    except Exception:
        html = ""
    if html:
        for href, label in _collect_links(BASE_URL, html)[:max_items]:
            try:
                sub_html = get_html(href)
            except Exception:
                sub_html = ""
            text = extract_text(sub_html)[:1600] if sub_html else ""
            guess_date = parse_date_safe(label) or parse_date_safe(text[:280])
            # short summary
            summary = (text[:260] + ("…" if len(text) > 260 else "")) if text else "FDA Digital Health hub update（要詳細確認）。"
            # key facts heuristic
            kfs = []
            for kw in ("guidance", "policy", "AI", "SaMD", "framework", "draft", "final"):
                if kw.lower() in (label + " " + text).lower():
                    kfs.append(f"含意: {kw}")
            items.append({
                "title": label or "FDA Digital Health update",
                "date": guess_date,
                "region": "US",
                "key_facts": kfs,
                "summary": summary,
                "quote": None,
                "citation": {"type": "web", "publisher": "FDA", "link": href}
            })
    return [make_source("regulation_and_policy", "FDA Digital Health Center of Excellence", BASE_URL, items)]
