from src.services.real_world import _capability_match, haversine_km, route_hospitals


def test_haversine_same_point_is_zero():
    assert haversine_km(16.5, 80.6, 16.5, 80.6) == 0


def test_capability_match_reports_unknown_instead_of_assuming():
    match, note = _capability_match({"tags": {"name": "Example Hospital"}}, "Stroke-like symptoms")
    assert match is None
    assert "not verified" in note.lower()


def test_route_hospitals_uses_road_table_and_immediate_urgency(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {"durations": [[600, 720]], "distances": [[5000, 6000]]}

    class Session:
        def __init__(self):
            self.headers = {}
        def get(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr("src.services.real_world._session", Session)
    origin = {"lat": 16.5, "lon": 80.6}
    hospitals = [
        {"id": "a", "name": "Specialty Hospital", "lat": 16.51, "lon": 80.61, "tags": {"healthcare:speciality": "cardiology"}},
        {"id": "b", "name": "General Hospital", "lat": 16.52, "lon": 80.62, "tags": {}},
    ]
    immediate = route_hospitals(origin, hospitals, "Chest pain / suspected cardiac emergency", urgency="Immediate")
    assert len(immediate) == 2
    assert immediate[0]["travel_time_min"] == 10
    assert immediate[0]["distance_km"] == 5


def test_nearby_hospital_search_falls_back_when_primary_overpass_is_down(monkeypatch):
    from src.services import real_world

    calls = []

    class Response:
        def __init__(self, payload=None, error=False):
            self.payload = payload or {}
            self.error = error
        def raise_for_status(self):
            if self.error:
                import requests
                raise requests.HTTPError("service unavailable")
        def json(self):
            return self.payload

    class Session:
        headers = {}
        def post(self, url, *args, **kwargs):
            calls.append(url)
            if "primary.example" in url:
                return Response(error=True)
            return Response({"elements": [{
                "type": "node", "id": 123, "lat": 16.5, "lon": 80.6,
                "tags": {"name": "Example Hospital", "amenity": "hospital"}
            }]})

    monkeypatch.setattr(real_world, "OVERPASS_URL", "https://primary.example/api/interpreter")
    monkeypatch.setattr(real_world, "OVERPASS_FALLBACK_URLS", ["https://fallback.example/api/interpreter"])
    monkeypatch.setattr(real_world, "_session", lambda: Session())

    hospitals = real_world.find_nearby_hospitals(16.5, 80.6, 15000)
    assert len(hospitals) == 1
    assert hospitals[0]["name"] == "Example Hospital"
    assert calls == [
        "https://primary.example/api/interpreter",
        "https://fallback.example/api/interpreter",
    ]
