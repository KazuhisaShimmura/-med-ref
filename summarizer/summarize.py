def shorten(s: str, max_chars=260):
    if not s: return s
    s = s.strip().replace('\n',' ')
    return s[:max_chars] + ('…' if len(s) > max_chars else '')

def summarize_items(item: dict) -> dict:
    # If real text exists, generate a simple summary; keep API-free for now.
    base = item.copy()
    if not base.get('summary'):
        text = ' '.join((base.get('title') or '', *(base.get('key_facts') or [])))
        base['summary'] = shorten(text, 240)
    # Ensure quote is <= 25 words if present
    q = base.get('quote')
    if q:
        words = q.split()
        if len(words) > 25:
            base['quote'] = ' '.join(words[:25]) + '…'
    return base
