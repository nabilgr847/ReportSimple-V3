"""Nearby hospitals, clinics, pharmacies from OpenStreetMap. No API key needed.

Only fields present in OSM are returned. Missing phone/website stay empty, nothing is invented.
OSM coverage in Bangladesh is incomplete, so the UI must say so.
Standard library only.
"""
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "ReportSimpleV3/1.0 (educational project)"
OVERPASS = "https://overpass-api.de/api/interpreter"
TTL = 1800
_cache = {}

KINDS = {
    "hospital": ['["amenity"="hospital"]'],
    "clinic": ['["amenity"~"^(clinic|doctors)$"]'],
    "pharmacy": ['["amenity"="pharmacy"]'],
    "diagnostic": ['["healthcare"="laboratory"]', '["healthcare"="diagnostic_centre"]'],
}


def _call(url, data=None, timeout=25):
    key = (url, data)
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]
    req = urllib.request.Request(url, data=data.encode() if data else None,
                                 headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None
    _cache[key] = (time.time(), out)
    return out


def geocode(query, country="bd"):
    q = urllib.parse.quote(query)
    cc = f"&countrycodes={country}" if country else ""
    d = _call(f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1{cc}")
    if not d:
        return None
    return {"lat": float(d[0]["lat"]), "lon": float(d[0]["lon"]), "name": d[0].get("display_name", "")}


def haversine_km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2 +
         math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


def _address(t):
    parts = [t.get("addr:housenumber"), t.get("addr:street"), t.get("addr:suburb") or t.get("addr:neighbourhood"),
             t.get("addr:city") or t.get("addr:district")]
    return ", ".join(p for p in parts if p) or t.get("addr:full", "")


def nearby(lat, lon, kind="hospital", radius_m=5000, limit=30):
    """Returns (items, ok). ok=False means the map server did not answer."""
    if kind not in KINDS:
        return [], False
    radius_m = max(500, min(int(radius_m), 20000))
    sel = "".join(f"nwr{s}(around:{radius_m},{lat},{lon});" for s in KINDS[kind])
    q = f"[out:json][timeout:20];({sel});out center tags 80;"
    d = _call(OVERPASS, data="data=" + urllib.parse.quote(q))
    if d is None:
        return [], False
    items = []
    for e in d.get("elements", []):
        t = e.get("tags", {})
        la = e.get("lat") or (e.get("center") or {}).get("lat")
        lo = e.get("lon") or (e.get("center") or {}).get("lon")
        if la is None or lo is None:
            continue
        items.append({
            "name": t.get("name:en") or t.get("name") or "(name not in map data)",
            "kind": kind,
            "address": _address(t),
            "phone": t.get("phone") or t.get("contact:phone") or "",
            "website": t.get("website") or t.get("contact:website") or "",
            "opening_hours": t.get("opening_hours", ""),
            "emergency": t.get("emergency") == "yes",
            "lat": la, "lon": lo,
            "distance_km": round(haversine_km(lat, lon, la, lo), 2),
            "directions_url": f"https://www.google.com/maps/dir/?api=1&destination={la},{lo}",
            "osm_url": f"https://www.openstreetmap.org/{e.get('type', 'node')}/{e.get('id')}",
        })
    items.sort(key=lambda x: x["distance_km"])
    return items[:limit], True


def route(lat1, lon1, lat2, lon2):
    d = _call(f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false")
    try:
        r = d["routes"][0]
        return {"distance_km": round(r["distance"] / 1000, 1), "minutes": round(r["duration"] / 60)}
    except (TypeError, KeyError, IndexError):
        return None


MAP_NOTE = "Map data is from OpenStreetMap and may be incomplete in Bangladesh. In an emergency call 999."
