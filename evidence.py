"""Medical evidence and drug-label lookups from public sources. No API key needed.

Rules: every item returned comes from the source's own response (title, year, link).
Nothing is invented. If a source fails, we return [] / None, never made-up data.
Standard library only.
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "ReportSimpleV3/1.0 (educational project)"
TTL = 3600
_cache = {}

# openFDA uses US drug names
ALIASES = {"paracetamol": "acetaminophen", "salbutamol": "albuterol", "adrenaline": "epinephrine",
           "noradrenaline": "norepinephrine", "frusemide": "furosemide"}


def _get(url, timeout=12):
    hit = _cache.get(url)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None
    _cache[url] = (time.time(), data)
    return data


def _clean(s, n=600):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s[:n]


def pubmed(query, n=5):
    q = urllib.parse.quote(query)
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    s = _get(f"{base}esearch.fcgi?db=pubmed&retmode=json&retmax={n}&sort=relevance&term={q}")
    ids = (((s or {}).get("esearchresult") or {}).get("idlist")) or []
    if not ids:
        return []
    d = _get(f"{base}esummary.fcgi?db=pubmed&retmode=json&id={','.join(ids)}") or {}
    out = []
    for i in ids:
        r = (d.get("result") or {}).get(i)
        if not r:
            continue
        doi = next((a.get("value") for a in r.get("articleids", []) if a.get("idtype") == "doi"), "")
        out.append({"source": "PubMed", "type": "research", "title": _clean(r.get("title"), 300),
                    "journal": _clean(r.get("source"), 100), "year": _clean(r.get("pubdate"), 4),
                    "doi": doi, "url": f"https://pubmed.ncbi.nlm.nih.gov/{i}/"})
    return out


def europepmc(query, n=5):
    q = urllib.parse.quote(query)
    d = _get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&format=json&resultType=lite&pageSize={n}")
    out = []
    for r in ((d or {}).get("resultList") or {}).get("result", []):
        src, rid = r.get("source", "MED"), r.get("id", "")
        out.append({"source": "Europe PMC", "type": "research", "title": _clean(r.get("title"), 300),
                    "journal": _clean(r.get("journalTitle"), 100), "year": _clean(r.get("pubYear"), 4),
                    "doi": r.get("doi", ""), "url": f"https://europepmc.org/article/{src}/{rid}"})
    return out


def research(query, n=5):
    """PubMed first, Europe PMC fills the rest. De-duplicated by DOI/title."""
    items, seen = [], set()
    for it in pubmed(query, n) + europepmc(query, n):
        key = (it["doi"] or it["title"]).lower()
        if key and key not in seen:
            seen.add(key)
            items.append(it)
    return items[:n]


def _label_item(r):
    of = r.get("openfda") or {}
    sid = r.get("set_id", "")
    pick = lambda k: _clean(" ".join(r.get(k, []) or []), 700)
    return {
        "generic_name": (of.get("generic_name") or [""])[0].lower(),
        "brand_names": (of.get("brand_name") or [])[:5],
        "indications": pick("indications_and_usage"),
        "contraindications": pick("contraindications"),
        "warnings": pick("warnings") or pick("warnings_and_cautions"),
        "interactions": pick("drug_interactions"),
        "side_effects": pick("adverse_reactions"),
        "label_date": _clean(r.get("effective_time"), 8),
        "source": "openFDA / DailyMed (US label)",
        "url": f"https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid={sid}" if sid else "https://dailymed.nlm.nih.gov/",
        "note": "US label. Check the Bangladesh (DGDA) status and local brand before use.",
    }


def medicine_info(name):
    """Label facts for one medicine (generic or common name). None if not found."""
    n = ALIASES.get(name.strip().lower(), name.strip().lower())
    if not re.fullmatch(r"[a-z0-9 \-]{2,60}", n):
        return None
    s = urllib.parse.quote(f'openfda.generic_name:"{n}"')
    d = _get(f"https://api.fda.gov/drug/label.json?search={s}&limit=1")
    res = (d or {}).get("results") or []
    return _label_item(res[0]) if res else None


def medicines_for_condition(condition, n=8):
    """Medicines whose official label lists this condition as an indication. Not a prescription."""
    c = condition.strip().lower()
    if not re.fullmatch(r"[a-z0-9 \-]{3,60}", c):
        return []
    s = urllib.parse.quote(f'indications_and_usage:"{c}"')
    d = _get(f"https://api.fda.gov/drug/label.json?search={s}&limit=25")
    out, seen = [], set()
    for r in (d or {}).get("results", []):
        it = _label_item(r)
        g = it["generic_name"]
        if g and g not in seen:
            seen.add(g)
            out.append(it)
        if len(out) >= n:
            break
    return out


def interactions(names):
    """Interaction text from each medicine's own label. Not a complete interaction checker."""
    res = []
    for nm in names[:6]:
        info = medicine_info(nm)
        res.append({"name": nm, "found": bool(info),
                    "interactions": info["interactions"] if info else "",
                    "url": info["url"] if info else ""})
    return res


MED_WARNING = ("Do not take any medicine without a registered doctor's permission. "
               "This shows what official labels say, not a prescription or a dose for you. "
               "Antibiotics need a doctor's prescription.")
