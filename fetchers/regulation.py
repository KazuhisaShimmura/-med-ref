from .common import make_source
from .mhlw_guideline import fetch_mhlw_guideline
from .pmda_medical_devices import fetch_pmda_medical_devices

REG_URLS = [
    ("regulation_and_policy", "FDA – Digital Health", "https://www.fda.gov/medical-devices/digital-health-center-excellence"),
    ("regulation_and_policy", "EU MDR", "https://health.ec.europa.eu/medical-devices-sector/new-regulations_en"),
]

def fetch_regulation():
    sources = []
    # Real fetchers
    sources.extend(fetch_mhlw_guideline())
    sources.extend(fetch_pmda_medical_devices())
    # Stubs for others (replace later)
    for cat, name, url in REG_URLS:
        items = [{
            'title': 'Placeholder regulation update',
            'date': None,
            'region': 'JP/EU/US',
            'key_facts': ['Replace with parsed revision dates / scope'],
            'summary': 'Stub: Implement real fetch & parse.',
            'quote': None,
            'citation': {'type': 'web', 'publisher': name, 'link': url}
        }]
        sources.append(make_source(cat, name, url, items))
    return sources
