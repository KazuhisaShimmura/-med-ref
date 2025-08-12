from .common import make_source, get_html, extract_text, parse_date_safe, collect_links_from_html
from urllib.parse import urljoin

BASE_URL = "https://health.ec.europa.eu/medical-devices-sector/new-regulations_en"

KEYWORDS = ("MDR", "IVDR", "guidance", "transition", "regulation", "notice", "Q&A", "FAQ", "implementing", "delegated")

def fetch_eu_mdr(max_items=8):
    items = []
    try:
        html = get_html(BASE_URL)
    except Exception:
        html = ""
    if html:
        for href, label in collect_links_from_html(BASE_URL, html, KEYWORDS, domain_filter="ec.europa.eu")[:max_items]:
            try:
                sub_html = get_html(href)
            except Exception:
                sub_html = ""
            text = extract_text(sub_html)[:1600] if sub_html else ""
            guess_date = parse_date_safe(label) or parse_date_safe(text[:280])
            summary = (text[:260] + ("…" if len(text) > 260 else "")) if text else "EU MDR hub update（要詳細確認）。"
            kfs = []
            for kw in ("MDR", "IVDR", "guidance", "transition", "implementing act", "delegated act", "Q&A", "FAQ"):
                if kw.lower() in (label + " " + text).lower():
                    kfs.append(f"含意: {kw}")
            items.append({
                "title": label or "EU MDR update",
                "date": guess_date,
                "region": "EU",
                "key_facts": kfs,
                "summary": summary,
                "quote": None,
                "citation": {"type": "web", "publisher": "EC DG SANTE", "link": href}
            })
    return [make_source("regulation_and_policy", "EU MDR (DG SANTE)", BASE_URL, items)]
