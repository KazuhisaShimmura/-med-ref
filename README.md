# med-ref (Healthcare Business Reference Crawler)

This repository hosts a minimal pipeline that **fetches key healthcare-business references**, summarizes them,
and publishes machine-readable outputs (`references.yaml` / `references.json`) that you can point your *custom GPT* to.

- **Privacy Policy**: Read the Privacy Policy for the custom GPT
- **Live Data**: `references.yaml` / `references.json`
- **GitHub Pages**: `https://KazuhisaShimmura.github.io/-med-ref/`
- A scheduled GitHub Action runs daily at **06:00 JST** to refresh data.

## Quick Start

1.  **Create Repository**: Create a new GitHub repository from this template (or clone/fork and push to your own).
2.  **Enable GitHub Pages**: In your repository, go to **Settings → Pages**. Under "Build and deployment", set the **Source** to **GitHub Actions**. This allows the workflow to publish the site.
3.  **Run Workflow**: The scheduled job in `.github/workflows/update_references.yml` will run automatically. You can also trigger it manually from the **Actions** tab to generate the initial `datastore/` files.
4.  **Access Published Files**: Once the workflow has run successfully, your site and files will be available.
    - The privacy policy will be at: `https://<your-username>.github.io/<your-repo-name>/privacy_policy.html`
    - Data files will be at: `https://<your-username>.github.io/<your-repo-name>/datastore/references.yaml` (and `.json`)

## Local Run

```bash
pip install -r requirements.txt
python scripts/update_references.py
python -m http.server 8000
# open http://localhost:8000/datastore/references.yaml
```

## Notes
- The fetchers here are **stubs + examples**; replace with real parsers or RSS/API calls.
- Keep quotes under 25 words to be copyright-friendly.
- Prefer official/public sources (ministries/regulators, standards bodies) over vendor marketing pages.



## Funding Fetchers
- **AMED**: `fetchers/amed.py` – Crawls public calls & news
- **JST**:  `fetchers/jst.py` – Crawls public calls
The pipeline merges results under `funding_and_grants` category.
