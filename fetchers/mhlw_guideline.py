from .common import make_source, get_html, extract_text, parse_date_safe, collect_links_from_html
from urllib.parse import urljoin
import re

BASE_URL = "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryou/johoka/index.html"

KEYWORDS = ("医療情報システム", "安全管理", "ガイドライン")

def fetch_mhlw_guideline(max_links=8):
    html = get_html(BASE_URL)
    uniq = collect_links_from_html(BASE_URL, html, KEYWORDS, domain_filter="mhlw.go.jp")
    items = []
    for href, label in uniq[:max_links]:
        try:
            sub_html = get_html(href)
        except Exception:
            sub_html = ""
        text = extract_text(sub_html)[:1200] if sub_html else ""
        # try to guess a date from label or page text
        guess_date = parse_date_safe(label) or parse_date_safe(text[:200])
        # brief summary
        summary = (text[:260] + ("…" if len(text) > 260 else "")) if text else "厚労省ページの更新（要詳細確認）。"
        # simple key facts heuristic
        kfs = []
        m_ver = re.search(r"(第?\d+版|Ver\.?\s*\d+(\.\d+)*)", label + " " + text)
        if m_ver:
            kfs.append(f"版数: {m_ver.group(1)}")
        items.append({
            "title": label or "MHLW update",
            "date": guess_date,
            "region": "JP",
            "key_facts": kfs,
            "summary": summary,
            "quote": None,
            "citation": {"type": "web", "publisher": "MHLW", "link": href}
        })
    return [make_source("regulation_and_policy",
                        "厚労省 医療情報システム安全管理ガイドライン",
                        BASE_URL,
                        items)]
