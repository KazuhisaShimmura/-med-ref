# med-ref (Healthcare Business Reference Crawler)

This repository hosts a minimal pipeline that **fetches key healthcare-business references**, summarizes them,
and publishes machine-readable outputs (`references.yaml` / `references.json`) that you can point your *custom GPT* to.

- Output files are in: `datastore/`
- GitHub Pages serves them at: `https://KazuhisaShimmura.github.io/-med-ref/datastore/references.yaml` (and `.json`)
- A scheduled GitHub Action runs daily at **06:00 JST** to refresh data.

## Quick Start

1) Create a new GitHub repo (e.g., `-med-ref`) and push these files.
2) In GitHub, go to **Settings → Pages** and set:
   - Source: **GitHub Actions**

#### ステップC: クリーンアップ内容をプッシュする

上記の整理が完了したら、その内容をコミットしてプッシュします。

```bash
# 1. ここまでの削除と修正をすべてステージングします
git add .

# 2. 整理内容をコミットします
git commit -m "Refactor: Consolidate to new crawler system and remove obsolete code"

# 3. GitHubにプッシュします
git push
3) The scheduled job (`.github/workflows/update_references.yml`) will generate/commit `datastore/references.*`.
4) Access:
   - `https://KazuhisaShimmura.github.io/-med-ref/`
   - `https://KazuhisaShimmura.github.io/-med-ref/datastore/references.yaml`
   - `https://KazuhisaShimmura.github.io/-med-ref/datastore/references.json`

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
