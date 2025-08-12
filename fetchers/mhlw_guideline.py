from .common import make_source, get_html, extract_text, parse_date_safe
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryou/johoka/index.html"

KEYWORDS = ("医療情報システム", "安全管理", "ガイドライン")

def _is_target_link(a):
    text = (a.get_text() or "").strip()
    href = a.get("href") or ""
    if not href:
        return False
    # prioritize same-domain & johoka subtree
    if not href.startswith("http"):
        href_full = urljoin(BASE_URL, href)
    else:
        href_full = href
    # keyword-based filter
    hit_kw = any(k in text for k in KEYWORDS) or any(k in href for k in ("johoka", "guideline", "gl"))
    return hit_kw, href_full, text if text else href_full

def fetch_mhlw_guideline(max_links=8):
    html = get_html(BASE_URL)
    soup = BeautifulSoup(html, "lxml")
    links = soup.find_all("a")
    candidates = []
    for a in links:
        ok, href_full, label = _is_target_link(a)
        if ok:
            candidates.append((href_full, label))
    # de-dup while preserving order
    seen = set()
    uniq = []
    for href, label in candidates:
        if href in seen: 
            continue
        seen.add(href)
        uniq.append((href, label))

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
