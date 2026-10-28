import html

from app import dark_map_html


def test_dark_map_renders_real_route_iframe():
    origin = {"lat": 16.5, "lon": 80.6, "display_name": "Test Place"}
    hospitals = [{"id": "node/1", "name": "Test Hospital", "lat": 16.51, "lon": 80.61,
                  "tags": {}, "travel_time_min": 10, "distance_km": 5, "rank": 1,
                  "capability_note": "Not verified"}]
    rendered = dark_map_html(origin, hospitals, "node/1", [[80.6, 16.5], [80.61, 16.51]])
    assert "<iframe" in rendered
    decoded = html.unescape(rendered)
    assert "dark_all" in decoded
    assert "Test Hospital" in decoded
    assert "Selected road route" in decoded
