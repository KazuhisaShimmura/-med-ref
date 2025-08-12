from .common import make_source
from .mhlw_guideline import fetch_mhlw_guideline
from .pmda_medical_devices import fetch_pmda_medical_devices
from .fda import fetch_fda
from .eu_mdr import fetch_eu_mdr
import logging

def fetch_regulation():
    sources = []
    fetchers = {
        "MHLW Guideline": fetch_mhlw_guideline,
        "PMDA Medical Devices": fetch_pmda_medical_devices,
        "FDA Digital Health": fetch_fda,
        "EU MDR": fetch_eu_mdr,
    }
    for name, fetcher in fetchers.items():
        try:
            logging.info(f"Running regulation fetcher: {name}")
            sources.extend(fetcher())
        except Exception as e:
            logging.error(f"Regulation fetcher {name} failed: {e}", exc_info=True)
    return sources
