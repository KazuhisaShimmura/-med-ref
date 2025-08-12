from .amed import fetch_amed
from .jst import fetch_jst

def fetch_funding():
    sources = []
    sources.extend(fetch_amed())
    sources.extend(fetch_jst())
    return sources
