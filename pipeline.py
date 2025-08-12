from fetchers.market import fetch_market
from fetchers.regulation import fetch_regulation
from fetchers.funding import fetch_funding
from summarizer.summarize import summarize_items
from pathlib import Path
import json, yaml, datetime

def run():
    all_sources = []
    for fetch in [fetch_market, fetch_regulation, fetch_funding]:
        all_sources.extend(fetch())

    # Summarize
    for s in all_sources:
        s['items'] = [summarize_items(i) for i in s.get('items', [])]

    bundle = {
        'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'sources': all_sources
    }

    Path('datastore').mkdir(exist_ok=True)
    with open('datastore/references.yaml', 'w', encoding='utf-8') as f:
        yaml.safe_dump(bundle, f, allow_unicode=True, sort_keys=False)
    with open('datastore/references.json', 'w', encoding='utf-8') as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    run()
