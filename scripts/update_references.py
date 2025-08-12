# scripts/update_references.py
import os, re, time, json, yaml
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dparser

UA = "med-ref-updater/1.0 (+https://github.com/KazuhisaShimmura/-med-ref)"
S = requests.Session()
S.headers.update({"User-Agent": UA})
TIMEOUT = 20

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

def make_source(category, name, url, items):
    return {
        "category": category,
        "name": name,
        "url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }

# ---- フェッチャ（国内・重要度高の4本：MHLW/PMDA/AMED/JST）----

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
        items.append({
            "title": label or "MHLW update",
            "date": guess_date,
            "region": "JP",
            "key_facts": kf,
            "summary": summary,
            "quote": None,
            "citation": {"type":"web","publisher":"MHLW","link":href}
        })
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
                "date": guess_date,
                "region": "JP",
                "key_facts": kf,
                "summary": summary,
                "quote": None,
                "citation": {"type":"web","publisher":"PMDA","link":href}
            })
    return [make_source("regulation_and_policy","PMDA（医療機器・審査/通知）", BASES[0], items)]

def fetch_amed(max_pages=1, max_items=8):
    BASES = ["https://www.amed.go.jp/koubo/index.html"]
    KEY = ("公募","募集","採択","研究開発","事業","助成","令和","公示")
    items=[]
    for base in BASES[:max_pages]:
        try:
            html=http_get(base)
        except Exception:
            continue
        soup=BeautifulSoup(html,"lxml")
        links=[]
        for a in soup.find_all("a"):
            href=a.get("href") or ""
            text=(a.get_text() or "").strip()
            if not href: continue
            full = href if href.startswith("http") else urljoin(base, href)
            if any(k in text for k in KEY): links.append((full, text or full))
        seen, uniq=set(),[]
        for u,t in links:
            if u in seen: continue
            seen.add(u); uniq.append((u,t))
        for href, label in uniq[:max_items]:
            try:
                sub=http_get(href); text=extract_text(sub)
            except Exception:
                text=""
            guess_date = parse_date_safe(label) or parse_date_safe(text[:220])
            kf=[f"含意: {kw}" for kw in ("公募","募集","採択","研究開発","事業","助成") if kw in (label + " " + text)]
            summary = (text[:260] + ("…" if len(text)>260 else "")) if text else "AMEDの関連更新（要詳細確認）。"
            items.append({
                "title": label or "AMED update",
                "date": guess_date,
                "region": "JP",
                "key_facts": kf,
                "summary": summary,
                "quote": None,
                "citation": {"type":"web","publisher":"AMED","link":href}
            })
    return [make_source("funding_and_grants","AMED（公募）", BASES[0], items)]

def fetch_jst(max_pages=1, max_items=10):
    BASES=["https://www.jst.go.jp/koubo/"]
    KEY=("公募","募集","予告","採択","助成","研究","事業","プログラム")
    items=[]
    for base in BASES[:max_pages]:
        try:
            html=http_get(base)
        except Exception:
            continue
        soup=BeautifulSoup(html,"lxml")
        links=[]
        for a in soup.find_all("a"):
            href=a.get("href") or ""
            text=(a.get_text() or "").strip()
            if not href: continue
            full = href if href.startswith("http") else urljoin(base, href)
            if any(k in text for k in KEY): links.append((full, text or full))
        seen, uniq=set(),[]
        for u,t in links:
            if u in seen: continue
            seen.add(u); uniq.append((u,t))
        for href, label in uniq[:max_items]:
            try:
                sub=http_get(href); text=extract_text(sub)
            except Exception:
                text=""
            guess_date = parse_date_safe(label) or parse_date_safe(text[:220])
            kf=[f"含意: {kw}" for kw in ("公募","募集","予告","採択","助成","研究","事業") if kw in (label + " " + text)]
            summary = (text[:260] + ("…" if len(text)>260 else "")) if text else "JSTの関連更新（要詳細確認）。"
            items.append({
                "title": label or "JST update",
                "date": guess_date,
                "region": "JP",
                "key_facts": kf,
                "summary": summary,
                "quote": None,
                "citation": {"type":"web","publisher":"JST","link":href}
            })
    return [make_source("funding_and_grants","JST（公募）", BASES[0], items)]

def main():
    os.makedirs("datastore", exist_ok=True)
    all_sources = []
    for fetch in (fetch_mhlw, fetch_pmda, fetch_amed, fetch_jst):
        try:
            all_sources.extend(fetch())
            time.sleep(0.5)  # 優しめのレート
        except Exception as e:
            print(f"[WARN] fetch error: {e}")

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
