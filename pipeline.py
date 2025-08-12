from fetchers.market import fetch_market
from fetchers.regulation import fetch_regulation
from fetchers.funding import fetch_funding
from summarizer.summarize import summarize_items
from pathlib import Path
import json, yaml, datetime, logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run():
    all_sources = []
    fetch_functions = {
        "market": fetch_market,
        "regulation": fetch_regulation,
        "funding": fetch_funding
    }

    for name, fetch_func in fetch_functions.items():
        try:
            logging.info(f"Fetching {name} sources...")
            sources = fetch_func()
            all_sources.extend(sources)
            logging.info(f"Successfully fetched {len(sources)} source(s) from {name}.")
        except Exception as e:
            logging.error(f"Failed to fetch {name} sources: {e}", exc_info=True)

    # Summarize
    for s in all_sources:
        summarized_items = []
        for item in s.get('items', []):
            try:
                # Attempt to summarize each item
                summarized_items.append(summarize_items(item))
            except Exception as e:
                logging.error(f"Failed to summarize item '{item.get('title', 'N/A')}': {e}", exc_info=True)
                # If summarization fails, append the original item to avoid data loss
                summarized_items.append(item)
        s['items'] = summarized_items

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
