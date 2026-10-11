"""Run this in Colab (or locally) to check the public APIs really answer. No API key needed.
    python check_live.py
Prints PASS/FAIL for each source so you know what works from your network."""
import evidence, places

def show(name, ok, extra=""):
    print(("PASS " if ok else "FAIL ") + name, extra)

r = evidence.pubmed("chest pain", 3);               show("PubMed", bool(r), r[0]["title"][:60] if r else "")
r = evidence.europepmc("chest pain", 3);            show("Europe PMC", bool(r), r[0]["title"][:60] if r else "")
r = evidence.medicine_info("paracetamol");          show("openFDA label (paracetamol)", bool(r), r["generic_name"] if r else "")
r = evidence.medicines_for_condition("hypertension", 3); show("openFDA by condition", bool(r), ", ".join(x["generic_name"] for x in r))
g = places.geocode("Cumilla");                      show("Nominatim geocode", bool(g), str(g and (g["lat"], g["lon"])))
if g:
    items, ok = places.nearby(g["lat"], g["lon"], "hospital", 5000)
    show("Overpass hospitals near Cumilla", ok and bool(items), f"{len(items)} found; first: {items[0]['name'] if items else '-'}")
    if items:
        rt = places.route(g["lat"], g["lon"], items[0]["lat"], items[0]["lon"]); show("OSRM route", bool(rt), str(rt))
