# scripts/update_references.py
import os, re, time, json, yaml, hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dparser

UA = "med-ref-updater/1.1 (+https://github.com/KazuhisaShimmura/-med-ref)"
S = requests.Session()
S.headers.update({"User-Agent": UA})
TIMEOUT = 20

# 追加：テーマキーワード（医療・DX・介護・ケアを優先）
THEME_KEYWORDS = ("医療", "ヘルスケア", "介護", "ケア", "DX", "デジタル", "在宅", "リハ", "看護")

def http_get(url: str) -> str:
    r = S.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text

def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script","style","noscript"]): t.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())

def parse_date_safe(s: str):
    try:
        return dparser.parse(s, fuzzy=True).date().isoformat()
    except Exception:
        return None

def stable_id(title: str, link: str) -> str:
    h = hashlib.sha1()
    h.update((title.strip() + "|" + link.strip()).encode("utf-8"))
    return "sha1:" + h.hexdigest()

def infer_doc_type(text: str) -> str:
    t = text.lower()
    # ざっくり推定（日本語も単純一致）
    if any(k in text for k in ("公募", "募集", "応募", "採択", "助成")): return "call"
    if any(k in text for k in ("ガイドライン", "指針", "手引き", "Q&A", "FAQ")): return "guidance"
    if any(k in text for k in ("通知", "事務連絡")): return "notice"
    if any(k in text for k in ("回収", "安全性", "注意喚起")): return "safety"
    if "news" in t or "お知らせ" in text or "ニュース" in text: return "news"
    return "other"

def extract_deadline(text: str) -> str | None:
    # 「締切」「応募締め切り」などの近傍から日付を拾う簡易版
    m = re.search(r"(締切|締め切り|応募.*(期限|締切)).{0,20}?([0-9]{4}[-/年][0-9]{1,2}[-/月][0-9]{1,2})", text)
    if m:
        return parse_date_safe(m.group(3))
    # 直書き日付の拾い上げ（最初の一つ）
    m2 = re.search(r"([0-9]{4}[-/年][0-9]{1,2}[-/月][0-9]{1,2})", text)
    if m2:
        return parse_date_safe(m2.group(1))
    return None

def matches_theme(s: str) -> bool:
    return any(k in s for k in THEME_KEYWORDS)

def make_source(category, name, url, items):
    return {
        "category": category,
        "name": name,
        "url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }

# ---------- フェッチャ ----------
def fetch_mhlw(max_items=6):
    BASE = "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryou/johoka/index.html"
    KEY = ("医療情報システム","安全管理","ガイドライン","通知","留意")
    try:
        html = http_get(BASE)
    except Exception:
        return []
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.find_all("a"):
        href = a.get("href") or ""
        text = (a.get_text() or "").strip()
        if not href: continue
        full = href if href.startswith("http") else urljoin(BASE, href)
        if any(k in text for k in KEY) or "johoka" in href:
            links.append((full, text or full))
    seen, uniq = set(), []
    for u,t in links:
        if u in seen: continue
        seen.add(u); uniq.append((u,t))
    items=[]
    for href, label in uniq[:max_items]:
        try:
            sub = http_get(href); text = extract_text(sub)
        except Exception:
            text = ""
        guess_date = parse_date_safe(label) or parse_date_safe(text[:200])
        ver = re.search(r"(第?\d+版|Ver\.?\s*\d+(?:\.\d+)*)", label + " " + text)
        kf = [f"版数: {ver.group(1)}"] if ver else []
        summary = (text[:260] + ("…" if len(text)>260 else "")) if text else "厚労省の関連更新（要詳細確認）。"
        item = {
            "title": label or "MHLW update",
            "id": stable_id(label or "MHLW update", href),
            "date": guess_date,
            "jurisdiction": "JP",
            "doc_type": infer_doc_type(label + " " + text),
            "key_facts": kf,
            "summary": summary,
            "deadline": None,
            "citation": {"type":"web","publisher":"MHLW","link":href}
        }
        items.append(item)
    return [make_source("regulation_and_policy","厚労省 医療情報システム安全管理ガイドライン", BASE, items)]

def fetch_pmda(max_pages=2, max_items_per_page=6):
    BASES = [
        "https://www.pmda.go.jp/review-services/inspections/0001.html",
        "https://www.pmda.go.jp/medical_devices/",
    ]
    KEY = ("医療機器","お知らせ","通知","審査","承認","認証","安全","Q&A","事務連絡","回収")
    items=[]
    for base in BASES[:max_pages]:
        try:
            html = http_get(base)
        except Exception:
            continue
        soup = BeautifulSoup(html, "lxml")
        links=[]
        for a in soup.find_all("a"):
            href=a.get("href") or ""
            text=(a.get_text() or "").strip()
            if not href: continue
            full = href if href.startswith("http") else urljoin(base, href)
            if any(k in text for k in KEY) or any(k in href for k in ("medical_devices","notice","qa","info")):
                links.append((full, text or full))
        seen, uniq=set(),[]
        for u,t in links:
            if u in seen: continue
            seen.add(u); uniq.append((u,t))
        for href, label in uniq[:max_items_per_page]:
            try:
                sub=http_get(href); text=extract_text(sub)
            except Exception:
                text=""
            guess_date = parse_date_safe(label) or parse_date_safe(text[:220])
            kf=[f"含意: {kw}" for kw in ("承認","認証","回収","Q&A","安全","事務連絡") if kw in (label + " " + text)]
            summary = (text[:260] + ("…" if len(text)>260 else "")) if text else "PMDAの関連更新（要詳細確認）。"
            items.append({
                "title": label or "PMDA update",
                "id": stable_id(label or "PMDA update", href),
                "date": guess_date,
                "jurisdiction": "JP",
                "doc_type": infer_doc_type(label + " " + text),
                "key_facts": kf,
                "summary": summary,
                "deadline": None,
                "citation": {"type":"web","publisher":"PMDA","link":href}
            })
    return [make_source("regulation_and_policy","PMDA（医療機器・審査/通知）", BASES[0], items)]

def _collect_links(base, html, keywords):
    soup = BeautifulSoup(html, "lxml")
    links=[]
    for a in soup.find_all("a"):
        href=a.get("href") or ""
        text=(a.get_text() or "").strip()
        if not href: continue
        full = href if href.startswith("http") else urljoin(base, href)
        if any(k in text for k in keywords):
            links.append((full, text or full))
    seen, uniq=set(),[]
    for u,t in links:
        if u in seen: continue
        seen.add(u); uniq.append((u,t))
    return uniq

def fetch_amed(max_pages=1, max_items=12):
    BASES = ["https://www.amed.go.jp/koubo/index.html"]
    KEY = ("公募","募集","採択","研究開発","事業","助成","令和","公示")
    items=[]
    for base in BASES[:max_pages]:
        try:
            html=http_get(base)
        except Exception:
            continue
        for href, label in _collect_links(base, html, KEY)[:max_items]:
            try:
                sub=http_get(href); text=extract_text(sub)
            except Exception:
                text=""
            if text and not matches_theme(label + " " + text):
                continue  # テーマ外はスキップ（医療/DX/介護/ケアを優先）
            guess_date = parse_date_safe(label) or parse_date_safe(text[:220])
            kf=[f"含意: {kw}" for kw in ("公募","募集","採択","研究開発","事業","助成") if kw in (label + " " + text)]
            summary = (text[:260] + ("…" if len(text)>260 else "")) if text else "AMEDの関連更新（要詳細確認）。"
            items.append({
                "title": label or "AMED update",
                "id": stable_id(label or "AMED update", href),
                "date": guess_date,
                "jurisdiction": "JP",
                "doc_type": "call",
                "key_facts": kf,
                "summary": summary,
                "deadline": extract_deadline(label + " " + text),
                "citation": {"type":"web","publisher":"AMED","link":href}
            })
    return [make_source("funding_and_grants","AMED（公募）", BASES[0], items)]

def fetch_jst(max_pages=1, max_items=15):
    BASES=["https://www.jst.go.jp/koubo/"]
    KEY=("公募","募集","予告","採択","助成","研究","事業","プログラム")
    items=[]
    for base in BASES[:max_pages]:
        try:
            html=http_get(base)
        except Exception:
            continue
        for href, label in _collect_links(base, html, KEY)[:max_items]:
            try:
                sub=http_get(href); text=extract_text(sub)
            except Exception:
                text=""
            if text and not matches_theme(label + " " + text):
                continue
            guess_date = parse_date_safe(label) or parse_date_safe(text[:220])
            kf=[f"含意: {kw}" for kw in ("公募","募集","予告","採択","助成","研究","事業") if kw in (label + " " + text)]
            summary = (text[:260] + ("…" if len(text)>260 else "")) if text else "JSTの関連更新（要詳細確認）。"
            items.append({
                "title": label or "JST update",
                "id": stable_id(label or "JST update", href),
                "date": guess_date,
                "jurisdiction": "JP",
                "doc_type": "call",
                "key_facts": kf,
                "summary": summary,
                "deadline": extract_deadline(label + " " + text),
                "citation": {"type":"web","publisher":"JST","link":href}
            })
    return [make_source("funding_and_grants","JST（公募）", BASES[0], items)]

def fetch_nedo(max_pages=2, max_items=12):
    # NEDO: 公募・ニュース（キーワードで医療/DX/介護/ケア寄りに）
    BASES = [
        "https://www.nedo.go.jp/koubo/index.html",  # 公募
        "https://www.nedo.go.jp/news/",             # ニュース
    ]
    KEY_CALL = ("公募","募集","助成","提案")
    items=[]
    for base in BASES[:max_pages]:
        try:
            html=http_get(base)
        except Exception:
            continue
        soup = BeautifulSoup(html, "lxml")
        links=[]
        for a in soup.find_all("a"):
            href=a.get("href") or ""
            text=(a.get_text() or "").strip()
            if not href: continue
            full = href if href.startswith("http") else urljoin(base, href)
            if any(k in text for k in (KEY_CALL + ("ニュース","お知らせ","報道","発表"))):
                links.append((full, text or full))
        seen, uniq=set(),[]
        for u,t in links:
            if u in seen: continue
            seen.add(u); uniq.append((u,t))
        for href, label in uniq[:max_items]:
            try:
                sub=http_get(href); text=extract_text(sub)
            except Exception:
                text=""
            # テーマフィルタ
            if text and not matches_theme(label + " " + text):
                continue
            guess_date = parse_date_safe(label) or parse_date_safe(text[:220])
            dt = infer_doc_type(label + " " + text)
            if base.endswith("/koubo/index.html"):
                dt = "call"
            summary = (text[:260] + ("…" if len(text)>260 else "")) if text else "NEDOの関連更新（要詳細確認）。"
            items.append({
                "title": label or "NEDO update",
                "id": stable_id(label or "NEDO update", href),
                "date": guess_date,
                "jurisdiction": "JP",
                "doc_type": dt,
                "key_facts": [],
                "summary": summary,
                "deadline": extract_deadline(label + " " + text) if dt=="call" else None,
                "citation": {"type":"web","publisher":"NEDO","link":href}
            })
    return [make_source("funding_and_grants","NEDO（公募・ニュース）", BASES[0], items)]

# ---------- 差分検知 ----------
def load_previous_links():
    prev_path = "datastore/references.json"
    if not os.path.exists(prev_path):
        return {}
    try:
        with open(prev_path, "r", encoding="utf-8") as f:
            prev = json.load(f)
        link_map = {}
        for src in prev.get("sources", []):
            for it in src.get("items", []):
                link = (it.get("citation") or {}).get("link")
                if link:
                    link_map[link] = {"date": it.get("date"), "id": it.get("id"), "summary": it.get("summary")}
        return link_map
    except Exception:
        return {}

def apply_change_type(all_sources, prev_link_map):
    for src in all_sources:
        for it in src["items"]:
            link = (it.get("citation") or {}).get("link")
            prev = prev_link_map.get(link)
            if not prev:
                it["change_type"] = "new"
            else:
                # ざっくり更新判定：日付 or 要約が変わっていれば updated
                if (it.get("date") and it.get("date") != prev.get("date")) or \
                   (it.get("summary") and prev.get("summary") and it["summary"][:120] != prev["summary"][:120]):
                    it["change_type"] = "updated"
                else:
                    it["change_type"] = "unchanged"

# ---------- メイン ----------
def main():
    os.makedirs("datastore", exist_ok=True)

    prev_link_map = load_previous_links()

    all_sources = []
    for fetch in (fetch_mhlw, fetch_pmda, fetch_amed, fetch_jst, fetch_nedo):
        try:
            all_sources.extend(fetch())
            time.sleep(0.5)
        except Exception as e:
            print(f"[WARN] fetch error: {e}")

    # 差分付与
    apply_change_type(all_sources, prev_link_map)

    bundle = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": all_sources
    }

    with open("datastore/references.json", "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)

    with open("datastore/references.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(bundle, f, allow_unicode=True, sort_keys=False)

    print("[OK] datastore/references.(json|yaml) updated.")

if __name__ == "__main__":
    main()
