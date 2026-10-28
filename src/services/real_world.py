"""Real-world geocoding, nearby hospital discovery and road routing.

External data are retrieved on demand. No synthetic coordinates are presented as real.
"""
from __future__ import annotations

import math
import os
from typing import Any

import requests

NOMINATIM_URL = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")
OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
# Public Overpass instances can rate-limit or time out independently. Try mirrors
# in sequence so one unavailable endpoint does not disable the entire workflow.
OVERPASS_FALLBACK_URLS = [
    url.strip()
    for url in os.getenv(
        "OVERPASS_FALLBACK_URLS",
        "https://overpass.kumi.systems/api/interpreter,https://overpass.private.coffee/api/interpreter",
    ).split(",")
    if url.strip() and url.strip() != OVERPASS_URL
]
OSRM_URL = os.getenv("OSRM_URL", "https://router.project-osrm.org")
USER_AGENT = os.getenv("MAP_USER_AGENT", "AmbulanceRouteOptimizerAcademicProject/2.0 (contact: configure MAP_USER_AGENT)")
TIMEOUT = float(os.getenv("MAP_REQUEST_TIMEOUT", "18"))

CONDITION_RULES = {
    "Road traffic accident / major trauma": ("trauma", "emergency", "surgery"),
    "Chest pain / suspected cardiac emergency": ("cardiology", "cardiac", "heart"),
    "Difficulty breathing": ("pulmonology", "respiratory", "emergency"),
    "Stroke-like symptoms": ("stroke", "neurology", "neurological"),
    "Severe bleeding": ("trauma", "emergency", "surgery"),
    "Burns": ("burn", "plastic_surgery", "surgery"),
    "Unconsciousness": ("emergency", "neurology", "intensive_care"),
    "Pregnancy-related emergency": ("maternity", "obstetrics", "gynaecology"),
    "Other medical emergency": ("emergency", "general"),
}

SYMPTOMS = {
    "Road traffic accident / major trauma": ["Suspected serious injury", "Head or neck injury", "Possible fracture", "Multiple injuries"],
    "Chest pain / suspected cardiac emergency": ["Chest pain or pressure", "Pain spreading to arm/jaw", "Sweating", "Dizziness"],
    "Difficulty breathing": ["Severe shortness of breath", "Wheezing", "Blue lips/skin", "Unable to speak full sentences"],
    "Stroke-like symptoms": ["Face drooping", "Arm weakness", "Speech difficulty", "Sudden confusion"],
    "Severe bleeding": ["Uncontrolled bleeding", "Deep wound", "Signs of shock"],
    "Burns": ["Large-area burn", "Face/airway burn", "Chemical or electrical burn"],
    "Unconsciousness": ["Unresponsive", "Seizure", "Sudden collapse"],
    "Pregnancy-related emergency": ["Heavy bleeding", "Severe abdominal pain", "Labour complication"],
    "Other medical emergency": ["High fever", "Severe pain", "Other urgent symptoms"],
}


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return s


def geocode_place(query: str) -> dict[str, Any]:
    query = (query or "").strip()
    if len(query) < 3:
        raise ValueError("Enter a place name or address with at least 3 characters.")
    try:
        response = _session().get(NOMINATIM_URL, params={"q": query, "format": "jsonv2", "limit": 1, "addressdetails": 1}, timeout=TIMEOUT)
        response.raise_for_status()
        rows = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError("Location search is temporarily unavailable. Check your connection and try again.") from exc
    if not rows:
        raise ValueError("No matching location was found. Try a more specific address, landmark or locality.")
    row = rows[0]
    return {"lat": float(row["lat"]), "lon": float(row["lon"]), "display_name": row.get("display_name", query)}


def find_nearby_hospitals(lat: float, lon: float, radius_m: int = 15000) -> list[dict[str, Any]]:
    radius_m = max(1000, min(int(radius_m), 30000))
    query = f"[out:json][timeout:20];(node[amenity=hospital](around:{radius_m},{lat},{lon});way[amenity=hospital](around:{radius_m},{lat},{lon});relation[amenity=hospital](around:{radius_m},{lat},{lon});node[healthcare=hospital](around:{radius_m},{lat},{lon});way[healthcare=hospital](around:{radius_m},{lat},{lon}););out center tags;"
    endpoints = [OVERPASS_URL, *OVERPASS_FALLBACK_URLS]
    last_error = None
    elements = None
    for endpoint in endpoints:
        try:
            response = _session().post(endpoint, data={"data": query}, timeout=TIMEOUT + 5)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or not isinstance(payload.get("elements", []), list):
                raise ValueError("The map service returned an unexpected response.")
            elements = payload.get("elements", [])
            # A successful empty response can be caused by a regional mirror's
            # data lag, so try the next endpoint before declaring no hospitals.
            if elements:
                break
        except (requests.RequestException, ValueError, TypeError) as exc:
            last_error = exc
            continue
    if elements is None:
        raise RuntimeError(
            "Nearby hospital data could not be reached from the available OpenStreetMap query services. "
            "Check internet access, then retry. You can also change OVERPASS_URL or "
            "OVERPASS_FALLBACK_URLS in .env."
        ) from last_error
    hospitals = []
    seen = set()
    for item in elements:
        tags = item.get("tags", {})
        name = tags.get("name") or tags.get("name:en")
        center = item.get("center", {})
        hlat, hlon = item.get("lat", center.get("lat")), item.get("lon", center.get("lon"))
        if not name or hlat is None or hlon is None:
            continue
        key = (str(name).strip().lower(), round(float(hlat), 4), round(float(hlon), 4))
        if key in seen:
            continue
        seen.add(key)
        hospitals.append({"id": f"{item.get('type','node')}/{item.get('id')}", "name": str(name), "lat": float(hlat), "lon": float(hlon), "tags": tags, "address": ", ".join(filter(None, [tags.get("addr:street"), tags.get("addr:city"), tags.get("addr:postcode")]))})
    if not hospitals:
        raise ValueError(
            "No named hospitals were found in the selected radius. Increase the search radius or try a nearby city/locality."
        )
    return hospitals


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _capability_match(hospital: dict[str, Any], condition: str) -> tuple[bool | None, str]:
    tags = hospital.get("tags", {})
    searchable = " ".join(str(v) for k, v in tags.items() if k in {"healthcare:speciality", "healthcare:specialty", "speciality", "specialty", "emergency", "healthcare", "name", "description"}).lower()
    keywords = CONDITION_RULES.get(condition, ())
    if any(k.replace("_", " ") in searchable or k in searchable for k in keywords):
        return True, "Relevant capability indicated by map tags"
    if any(k in tags for k in ("healthcare:speciality", "healthcare:specialty", "speciality", "specialty")):
        return False, "Specialty tags do not confirm a match; verify directly"
    return None, "Specialty/capacity not verified in map data"


def route_hospitals(origin: dict[str, Any], hospitals: list[dict[str, Any]], condition: str, limit: int = 8, urgency: str = "Urgent") -> list[dict[str, Any]]:
    # Keep the routing request bounded: choose nearest candidates geographically, then use road-network durations.
    candidates = sorted(hospitals, key=lambda h: haversine_km(origin["lat"], origin["lon"], h["lat"], h["lon"]))[:max(1, min(limit, 8))]
    coords = [(origin["lon"], origin["lat"])] + [(h["lon"], h["lat"]) for h in candidates]
    coord_text = ";".join(f"{lon:.6f},{lat:.6f}" for lon, lat in coords)
    url = f"{OSRM_URL.rstrip('/')}/table/v1/driving/{coord_text}"
    try:
        response = _session().get(url, params={"sources": "0", "destinations": ";".join(str(i) for i in range(1, len(coords))), "annotations": "duration,distance"}, timeout=TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        durations = payload.get("durations", [[]])[0]
        distances = payload.get("distances", [[]])[0]
    except (requests.RequestException, ValueError, IndexError, TypeError) as exc:
        raise RuntimeError("Road routing is temporarily unavailable. The app has not substituted straight-line distance for a road route.") from exc
    out = []
    for i, h in enumerate(candidates):
        duration = durations[i] if i < len(durations) else None
        distance = distances[i] if i < len(distances) else None
        if duration is None or distance is None:
            continue
        match, explanation = _capability_match(h, condition)
        # Verified match is a small tie-breaker; unknown capability is not treated as confirmed.
        match_bonus = (0 if urgency == "Immediate" else 2 if urgency == "Urgent" else 3) if match is True else 0
        out.append({**h, "travel_time_min": float(duration) / 60, "distance_km": float(distance) / 1000, "capability_match": match, "capability_note": explanation, "rank_score": float(duration) / 60 - match_bonus})
    out.sort(key=lambda h: (h["rank_score"], h["travel_time_min"]))
    for i, h in enumerate(out, 1):
        h["rank"] = i
    if not out:
        raise ValueError("The routing service could not calculate a drivable route to the nearby hospitals.")
    return out


def route_geometry(origin: dict[str, Any], hospital: dict[str, Any]) -> dict[str, Any]:
    coord_text = f"{origin['lon']:.6f},{origin['lat']:.6f};{hospital['lon']:.6f},{hospital['lat']:.6f}"
    url = f"{OSRM_URL.rstrip('/')}/route/v1/driving/{coord_text}"
    try:
        response = _session().get(url, params={"overview": "full", "geometries": "geojson", "steps": "false"}, timeout=TIMEOUT)
        response.raise_for_status()
        routes = response.json().get("routes", [])
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError("Could not load the selected road route. Please select the hospital again.") from exc
    if not routes:
        raise ValueError("No drivable route was found to the selected hospital.")
    r = routes[0]
    return {"geometry": r["geometry"]["coordinates"], "distance_km": float(r["distance"]) / 1000, "travel_time_min": float(r["duration"]) / 60}
