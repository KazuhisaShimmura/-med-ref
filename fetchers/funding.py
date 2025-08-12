from .amed import fetch_amed
from .jst import fetch_jst
import logging

def fetch_funding():
    sources = []
    fetchers = {
        "AMED": fetch_amed,
        "JST": fetch_jst,
    }
    for name, fetcher in fetchers.items():
        try:
            logging.info(f"Running funding fetcher: {name}")
            sources.extend(fetcher())
        except Exception as e:
            logging.error(f"Funding fetcher {name} failed: {e}", exc_info=True)
    return sources
