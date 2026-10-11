# ReportSimple V3: what to add to the repo

Copy these into the root of `ReportSimpleV2.0` (next to `server.py`):

| File | What it is |
|---|---|
| `server.py` | Replaces the old one. `/` = V3 app, `/v2` = old report page, registers the V3 API |
| `app.html` | V3 web app. **Separate layouts:** phone = bottom tabs, PC = sidebar + two-column pages |
| `v3_api.py` | Interview, assessment, chat, evidence, medicine, interactions, places, PDF endpoints |
| `safety.py` | Red-flag rules (run before any AI text) |
| `evidence.py` | PubMed, Europe PMC, openFDA / DailyMed |
| `places.py` | OpenStreetMap (Overpass, Nominatim, OSRM) |
| `summary_pdf.py` | Doctor-ready symptom PDF |
| `check_live.py` | Checks that the public APIs answer from your network |
| `tests/test_safety.py`, `.github/workflows/*.yml` | Tests and GitHub Actions |

**Important:** `server.py` imports `rules`, but your repo file is named `rules-4.py`. Rename it to `rules.py`.
No new pip packages are needed. Keep `index.html` (it is the V2 report page, shown in the Reports tab).

## Run in Colab
```python
!git clone https://github.com/nabilgr847/ReportSimpleV2.0
%cd ReportSimpleV2.0
# upload the V3 files here, then:
!mv rules-4.py rules.py
!apt-get -qq install tesseract-ocr poppler-utils
!pip -q install -r requirements.txt
import os; from google.colab import userdata
os.environ["FEATHERLESS_API_KEY"] = userdata.get("FEATHERLESS_API_KEY")   # Colab Secrets
!python check_live.py     # every line should say PASS
```

## Secrets and Actions
- `FEATHERLESS_API_KEY`: Colab Secrets and your host's environment. Never in code.
- Actions run the tests. To go live, host the Docker/Flask app (Render, Hugging Face Spaces, etc.) and set `DEPLOY_HOOK_URL` in GitHub Secrets.

## Known limits (be honest in your submission)
- The 3D body is a simple stylised model with clickable regions, not a medical anatomy model. "Organs" is a schematic.
- Symptom analysis gives "possible conditions" with labels, never a diagnosis or percentages.
- Medicine info uses US labels (openFDA / DailyMed). It is not Bangladesh (DGDA) data.
- No doctor list, ratings, fees or pharmacy stock: no reliable public source exists.
- OpenStreetMap data is incomplete in Bangladesh. Public map servers have usage limits.
- The PDF prints Latin text only (Bangla shows as ?).
- 3D viewer, map and layouts were written and checked by code review and a script test, not on a real phone or PC browser yet.
