from __future__ import annotations



import html

import json
import os

from pathlib import Path



import folium

import gradio as gr

import pandas as pd

from dotenv import load_dotenv



ROOT = Path(__file__).parent

load_dotenv(ROOT / ".env")



from src.services.application import AmbulanceOptimizer

from src.services.real_world import (

    SYMPTOMS, find_nearby_hospitals, geocode_place, route_geometry, route_hospitals,

)

from src.utils.validation import validate_dataset



DATA = ROOT / "data" / "raw"

optimizer = AmbulanceOptimizer(DATA)

validation = validate_dataset(DATA)

case_rows = pd.read_csv(DATA / "emergency_cases.csv").head(100)

incident_rows = pd.read_csv(DATA / "incidents.csv").head(100)

CASE_CHOICES = [(f"{str(r.severity).title()} emergency · {str(r.required_service).replace('_',' ').title()} · Priority {int(r.severity_score)}/10", str(r.case_id)) for r in case_rows.itertuples()]

INCIDENT_CHOICES = [(f"{str(r.incident_type).replace('_',' ').title()} · {str(r.cause).replace('_',' ').title()} · {str(r.effect).replace('_',' ').title()}", str(r.incident_id)) for r in incident_rows.itertuples()]

CONDITIONS = list(SYMPTOMS)

LOCATION_PRESETS = [
    "Benz Circle, Vijayawada, Andhra Pradesh",
    "PNBS Bus Station, Vijayawada, Andhra Pradesh",
    "Vijayawada Railway Station, Andhra Pradesh",
    "Government General Hospital, Vijayawada, Andhra Pradesh",
    "Kanaka Durga Temple, Vijayawada, Andhra Pradesh",
    "Prakasam Barrage, Vijayawada, Andhra Pradesh",
    "Bhavani Island, Vijayawada, Andhra Pradesh",
    "Ramavarappadu Ring Road, Vijayawada, Andhra Pradesh",
    "Autonagar, Vijayawada, Andhra Pradesh",
    "Poranki, Vijayawada, Andhra Pradesh",
    "Mangalagiri, Andhra Pradesh",
    "Gannavaram Airport, Andhra Pradesh",
    "Patamata, Vijayawada, Andhra Pradesh",
    "Governorpet, Vijayawada, Andhra Pradesh",
    "Suryaraopet, Vijayawada, Andhra Pradesh",
    "Nunna, Vijayawada, Andhra Pradesh",
    "Ibrahimpatnam, Andhra Pradesh",
    "Enikepadu, Vijayawada, Andhra Pradesh",
]
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()





def esc(value):

    return html.escape(str(value), quote=True)





def dark_map_html(origin, hospitals, selected_id=None, geometry=None):
    # If a Google Maps JavaScript API key is supplied in .env, use Google Maps.
    # Otherwise use OpenStreetMap tiles, which need no API key.
    if GOOGLE_MAPS_API_KEY:
        map_data = {
            "origin": {"lat": float(origin["lat"]), "lon": float(origin["lon"])},
            "hospitals": [
                {
                    "id": str(h.get("id")),
                    "name": str(h.get("name", "Hospital")),
                    "lat": float(h["lat"]),
                    "lon": float(h["lon"]),
                    "rank": h.get("rank", "?"),
                    "eta": round(float(h.get("travel_time_min", 0)), 1),
                    "distance": round(float(h.get("distance_km", 0)), 1),
                    "selected": str(h.get("id")) == str(selected_id),
                }
                for h in hospitals
            ],
            "geometry": geometry or [],
        }
        config = json.dumps(map_data).replace("</", "<\\/")
        key = html.escape(GOOGLE_MAPS_API_KEY, quote=True)
        google_doc = f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
        <style>html,body,#map{{height:100%;width:100%;margin:0;background:#0b1423}} .gm-style{{font-family:Inter,Arial,sans-serif}}</style></head>
        <body><div id="map"></div><script>
        const cfg={config};
        function initMap(){{
          const origin={{lat:cfg.origin.lat,lng:cfg.origin.lon}};
          const map=new google.maps.Map(document.getElementById('map'),{{center:origin,zoom:13,fullscreenControl:true,streetViewControl:false,mapTypeControl:true,
            styles:[
              {{elementType:'geometry',stylers:[{{color:'#172437'}}]}},
              {{elementType:'labels.text.fill',stylers:[{{color:'#d3deeb'}}]}},
              {{elementType:'labels.text.stroke',stylers:[{{color:'#101a29'}}]}},
              {{featureType:'road',elementType:'geometry',stylers:[{{color:'#31445a'}}]}},
              {{featureType:'road',elementType:'geometry.stroke',stylers:[{{color:'#0b1423'}}]}},
              {{featureType:'water',elementType:'geometry',stylers:[{{color:'#091d30'}}]}},
              {{featureType:'poi',elementType:'geometry',stylers:[{{color:'#203449'}}]}}
            ]}});
          new google.maps.Marker({{position:origin,map,title:'Emergency pickup',label:{{text:'A',color:'#ffffff'}}}});
          const bounds=new google.maps.LatLngBounds(); bounds.extend(origin);
          cfg.hospitals.forEach(h=>{{
            const pos={{lat:h.lat,lng:h.lon}}; bounds.extend(pos);
            const marker=new google.maps.Marker({{position:pos,map,title:'#'+h.rank+' '+h.name+' · '+h.eta+' min',
              icon:h.selected?undefined:{{path:google.maps.SymbolPath.CIRCLE,scale:7,fillColor:'#48d7c5',fillOpacity:1,strokeColor:'#0b1423',strokeWeight:2}}}});
            const info=new google.maps.InfoWindow({{content:'<b>'+String(h.name).replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]))+'</b><br>'+h.eta+' min · '+h.distance+' km'}});
            marker.addListener('click',()=>info.open({{anchor:marker,map}});
          }});
          if(cfg.geometry.length){{const path=cfg.geometry.map(p=>({{lat:Number(p[1]),lng:Number(p[0])}}));path.forEach(p=>bounds.extend(p));new google.maps.Polyline({{path,map,strokeColor:'#ff8a4c',strokeOpacity:1,strokeWeight:6}});}}
          if(cfg.hospitals.length)map.fitBounds(bounds);
        }}
        </script><script async defer src="https://maps.googleapis.com/maps/api/js?key={key}&callback=initMap"></script></body></html>"""
        return "<iframe title='Google Maps emergency route' style='width:100%;height:520px;border:0;border-radius:18px;background:#0b1220' loading='lazy' srcdoc=\"" + esc(google_doc) + "\"></iframe>"

    m = folium.Map(location=[origin["lat"], origin["lon"]], zoom_start=13, tiles="OpenStreetMap", control_scale=True)

    folium.CircleMarker([origin["lat"], origin["lon"]], radius=8, color="#ff9a62", weight=3, fill=True, fill_color="#ff8a4c", fill_opacity=1, tooltip="Emergency pickup").add_to(m)

    folium.Marker([origin["lat"], origin["lon"]], tooltip="Pickup location", icon=folium.DivIcon(html="<div style='font-size:22px'>🚑</div>")).add_to(m)

    for h in hospitals:

        selected = str(h.get("id")) == str(selected_id)

        label = f"<b>{esc(h['name'])}</b><br>{h.get('travel_time_min', 0):.1f} min · {h.get('distance_km', 0):.1f} km<br>{esc(h.get('capability_note', ''))}"

        folium.CircleMarker([h["lat"], h["lon"]], radius=8 if selected else 6, color="#ff9a62" if selected else "#48d7c5", weight=3, fill=True, fill_color="#ff8a4c" if selected else "#0f9f9a", fill_opacity=.95, tooltip=f"#{h.get('rank','?')} {h['name']}", popup=folium.Popup(label, max_width=300)).add_to(m)

    if geometry:

        coords = [(lat, lon) for lon, lat in geometry]

        folium.PolyLine(coords, color="#ff8a4c", weight=6, opacity=.92, tooltip="Selected road route").add_to(m)

        if coords:

            m.fit_bounds(coords, padding=(30, 30))

    else:

        points = [[origin["lat"], origin["lon"]]] + [[h["lat"], h["lon"]] for h in hospitals]

        m.fit_bounds(points, padding=(30, 30))

    body = m.get_root().render()

    return "<iframe title='Interactive road map' style='width:100%;height:520px;border:0;border-radius:16px;background:#0b1220' loading='lazy' srcdoc=\"" + esc(body) + "\"></iframe>"





def hospital_rows_html(hospitals):

    if not hospitals:

        return "<div class='empty-state'>No hospitals to display. Search for a location first.</div>"

    cards = []

    for h in hospitals:

        match = h.get("capability_match")

        capability = "Capability tag found" if match is True else ("Specialty mismatch indicated" if match is False else "Capability unverified")

        cls = "good" if match is True else ("warn" if match is False else "neutral")

        cards.append(f"""

        <div class='hospital-card'>

          <div class='hospital-top'><div class='rank-pill'>{int(h.get('rank', 0)):02d}</div><div class='hospital-main'><div class='hospital-name'>{esc(h['name'])}</div><div class='hospital-address'>{esc(h.get('address') or 'Address not listed in map data')}</div></div><div class='hospital-eta'>{h['travel_time_min']:.0f}<small>min</small></div></div>

          <div class='hospital-bottom'><span class='chip {cls}'>{esc(capability)}</span><span class='chip neutral'>{h['distance_km']:.1f} km by road</span><span class='hospital-action'>Select on map</span></div>

          <div class='hospital-explain'>{esc(h.get('capability_note',''))}</div>

        </div>""")

    return "<div class='hospital-list'>" + "".join(cards) + "</div>"





def condition_changed(condition):

    return gr.update(choices=SYMPTOMS.get(condition, []), value=[])





def search_and_rank(place, condition, symptoms, urgency, radius_km, state):

    try:

        origin = geocode_place(place)

        hospitals = find_nearby_hospitals(origin["lat"], origin["lon"], int(float(radius_km) * 1000))

        ranked = route_hospitals(origin, hospitals, condition, limit=8, urgency=urgency)

        state_data = {"origin": origin, "hospitals": ranked, "condition": condition, "symptoms": symptoms or [], "urgency": urgency, "place_query": place}

        chosen = ranked[0]

        route = route_geometry(origin, chosen)

        # Keep the OSRM route metrics authoritative for the selected path.

        chosen["travel_time_min"] = route["travel_time_min"]

        chosen["distance_km"] = route["distance_km"]

        map_html = dark_map_html(origin, ranked, chosen["id"], route["geometry"])

        summary = f"""

        <div class='recommendation'><div class='eyebrow'>TOP ROAD-ROUTE RECOMMENDATION</div><div class='recommendation-title'>{esc(chosen['name'])}</div><div class='recommendation-sub'>{esc(origin['display_name'])}</div><div class='stats'><div><span>Estimated drive</span><strong>{route['travel_time_min']:.0f} min</strong></div><div><span>Road distance</span><strong>{route['distance_km']:.1f} km</strong></div><div><span>Urgency</span><strong>{esc(urgency)}</strong></div></div><div class='note'>Symptoms recorded: {esc(', '.join(symptoms or []) or 'None selected')}. Immediate urgency prioritizes travel time over specialty-tag tie-breaks. Hospital capacity and clinical suitability are not verified by OpenStreetMap.</div></div>"""

        status = f"Found {len(ranked)} routable hospitals around the searched location. Map data and travel estimates are from external services; availability is unverified."

        hospital_options = [(f"#{h['rank']} · {h['name']} · {h['travel_time_min']:.0f} min", h["id"]) for h in ranked]

        return state_data, summary, gr.update(choices=hospital_options, value=chosen["id"]), map_html, hospital_rows_html(ranked), status, gr.update(choices=hospital_options, value=[]), "<div class='empty-state'>Select at least two hospitals and click Compare.</div>"

    except (ValueError, RuntimeError) as ex:

        return None, f"<div class='error-card'><b>Could not calculate a recommendation</b><p>{esc(ex)}</p></div>", gr.update(choices=[], value=None), "<div class='map-empty'>Map will appear after a successful location search.</div>", "<div class='empty-state'>No results yet.</div>", str(ex), gr.update(choices=[], value=[]), "<div class='empty-state'>Hospital comparison is unavailable until a successful search.</div>"





def choose_hospital(hospital_id, state):

    if not state or not state.get("origin"):

        raise gr.Error("Search for a location before selecting a hospital.")

    chosen = next((h for h in state["hospitals"] if str(h["id"]) == str(hospital_id)), None)

    if chosen is None:

        raise gr.Error("That hospital is no longer in the current results. Search again.")

    try:

        route = route_geometry(state["origin"], chosen)

    except (ValueError, RuntimeError) as ex:

        raise gr.Error(str(ex))

    chosen["travel_time_min"] = route["travel_time_min"]

    chosen["distance_km"] = route["distance_km"]

    state["selected_id"] = chosen["id"]

    summary = f"""

    <div class='recommendation'><div class='eyebrow'>SELECTED HOSPITAL</div><div class='recommendation-title'>{esc(chosen['name'])}</div><div class='recommendation-sub'>Selected by operator · {esc(state['condition'])}</div><div class='stats'><div><span>Estimated drive</span><strong>{route['travel_time_min']:.0f} min</strong></div><div><span>Road distance</span><strong>{route['distance_km']:.1f} km</strong></div><div><span>Urgency</span><strong>{esc(state['urgency'])}</strong></div></div><div class='note'>The highlighted route is calculated by the external road-routing service. Hospital capability, live capacity and clinical suitability must be verified independently.</div></div>"""

    return state, summary, dark_map_html(state["origin"], state["hospitals"], chosen["id"], route["geometry"]), hospital_rows_html(state["hospitals"])





def compare_hospitals(hospital_ids, state):

    if not state or not state.get("hospitals"):

        return "<div class='empty-state'>Search for a pickup location first, then select hospitals to compare.</div>"

    ids = {str(x) for x in (hospital_ids or [])}

    if len(ids) < 2:

        return "<div class='empty-state'>Select at least two hospitals to compare them side by side.</div>"

    chosen = [h for h in state["hospitals"] if str(h["id"]) in ids]

    rows = []

    for h in chosen:

        match = h.get("capability_match")

        capability = "Indicated by map tags" if match is True else ("Possible mismatch — verify" if match is False else "Not verified")

        rows.append("<tr>" + f"<td><b>{esc(h['name'])}</b><div class='compare-muted'>Rank #{int(h.get('rank', 0))}</div></td><td>{float(h.get('travel_time_min', 0)):.0f} min</td><td>{float(h.get('distance_km', 0)):.1f} km</td><td>{esc(capability)}</td><td>{esc(h.get('address') or 'Address not listed')}</td>" + "</tr>")

    return "<div class='compare-wrap'><div class='compare-heading'>SIDE-BY-SIDE HOSPITAL COMPARISON</div><div class='compare-scroll'><table class='compare-table'><thead><tr><th>Hospital</th><th>Road ETA</th><th>Road distance</th><th>Capability indication</th><th>Address</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div><div class='compare-note'>Road estimates come from the routing service. Map tags do not verify clinical capability, bed availability or hospital acceptance.</div></div>"



def synthetic_optimize(case_id):

    try:

        e, selected, candidates = optimizer.optimize(case_id)

    except ValueError as ex:

        raise gr.Error(str(ex))

    if selected is None:

        return "No suitable hospital found in the synthetic graph.", "No reachable hospitals.", "Dijkstra found no reachable destination."

    summary = f"### Recommended synthetic hospital: {selected.hospital.name}\n\n- Travel time: **{selected.travel_time_min:.1f} min**\n- Distance: **{selected.distance_km:.2f} km**\n- Suitability score: **{selected.score:.1%}**\n- Required service: **{e.required_service}**"

    ranking = "\n".join(f"{i}. **{c.hospital.name}** — {c.travel_time_min:.1f} min · {c.distance_km:.2f} km · {c.score:.1%}" for i, c in enumerate(candidates[:8], 1))

    tech = f"**Algorithm:** Dijkstra + weighted hospital scoring\n\n**Synthetic graph route:** `{' → '.join(selected.route)}`\n\n**Case:** `{e.case_id}` · **Node:** `{e.ambulance_node}`"

    return summary, ranking, tech





def synthetic_reroute(case_id, incident_id):

    try:

        e, selected, result = optimizer.reroute_for_incident(case_id, incident_id)

    except ValueError as ex:

        raise gr.Error(str(ex))

    row = optimizer.incidents[optimizer.incidents.incident_id.astype(str) == str(incident_id)].iloc[0]

    if not result.reachable:

        return "No alternate route exists in the synthetic graph after blocking this road.", f"Incident `{incident_id}` blocked road `{row['road_id']}`. Dijkstra explored {result.nodes_explored} nodes."

    return f"### Alternative route: {selected.hospital.name}\n\n- Travel time: **{result.total_time_min:.1f} min**\n- Distance: **{result.total_distance_km:.2f} km**\n- Road segments: **{max(len(result.path)-1, 0)}**", f"Incident `{incident_id}` blocked road `{row['road_id']}`.\n\n**Dijkstra route:** `{' → '.join(result.path)}`"





CSS = r"""

:root { color-scheme: dark; --bg:#070d18; --panel:#101b2b; --panel2:#142337; --line:#283d52; --text:#edf7ff; --muted:#91a9c0; --orange:#ff8a4c; --cyan:#48d7c5; }

body, .gradio-container { background:radial-gradient(ellipse at 15% 5%,#10273a 0%,transparent 34%),radial-gradient(ellipse at 90% 35%,#18223b 0%,transparent 32%),#070d18 !important; color:var(--text) !important; }
.gradio-container { position:relative; isolation:isolate; }
.gradio-container:before { content:"";position:fixed;z-index:-1;inset:-15%;pointer-events:none;background:conic-gradient(from 0deg at 50% 50%,transparent 0 25%,#48d7c508 30%,transparent 40% 62%,#ff8a4c0a 72%,transparent 85%);filter:blur(40px);animation:ambientOrbit 32s linear infinite; }
@keyframes ambientOrbit { from { transform:rotate(0deg) scale(1); } to { transform:rotate(360deg) scale(1.08); } }
@keyframes floatOrb { 0%,100% { transform:translate3d(0,0,0) rotateX(0deg) rotateY(0deg); } 50% { transform:translate3d(-12px,12px,0) rotateX(8deg) rotateY(-8deg); } }

.gradio-container { max-width:1480px !important; margin:auto !important; }

footer {display:none !important}

\#app-header {position:relative;isolation:isolate;overflow:hidden;border:1px solid #294459;border-radius:26px;padding:34px 38px;margin-bottom:22px;background:radial-gradient(circle at 84% 22%,#ff8a4c24,transparent 22%),radial-gradient(circle at 72% 85%,#48d7c516,transparent 28%),linear-gradient(130deg,#122236,#0b1423 60%,#101d31);box-shadow:0 24px 70px #0006;transform-style:preserve-3d}

\#app-header:before {content:"";position:absolute;z-index:-1;right:8%;top:-95px;width:290px;height:290px;border-radius:50%;border:1px solid #48d7c52b;box-shadow:0 0 0 22px #48d7c508,0 0 0 48px #48d7c506,inset -18px -12px 42px #ff8a4c15;animation:floatOrb 9s ease-in-out infinite}
#app-header:after {content:"";position:absolute;z-index:-1;right:15%;bottom:-115px;width:240px;height:180px;border:1px solid #ff8a4c22;border-radius:50%;transform:rotateX(68deg) rotateZ(-20deg);box-shadow:0 0 0 22px #ff8a4c08,0 0 0 45px #48d7c506;animation:floatOrb 12s ease-in-out infinite reverse}

.brandline {display:flex;align-items:center;gap:12px;margin-bottom:16px}.brandmark {display:grid;place-items:center;width:42px;height:42px;border-radius:13px;background:linear-gradient(135deg,#ff9a62,#ea580c);font-size:22px;box-shadow:0 8px 24px #ff8a4c33}.brandname {font-size:11px;letter-spacing:2px;font-weight:800;color:#fdba74}.hero-title {font-size:clamp(27px,4vw,42px);font-weight:850;letter-spacing:-1.4px;line-height:1.1;margin:0 0 10px}.hero-copy {max-width:780px;color:#aab8cc;font-size:14px;line-height:1.7}.header-tags {display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}.header-tag {font-size:11px;color:#c7d3e4;border:1px solid #304057;border-radius:999px;padding:7px 11px;background:#ffffff06}

.panel-title {font-size:18px;font-weight:800;letter-spacing:-.3px;color:#f4f7fc}.panel-sub {font-size:12px;color:#91a1b8;line-height:1.6;margin-top:4px}.eyebrow {font-size:10px;font-weight:850;letter-spacing:1.7px;color:#ff9a62}.recommendation,.glass-panel,.hospital-card,.empty-state,.error-card {background:linear-gradient(145deg,#121d2d,#0f1725);border:1px solid #27364b;border-radius:18px}.recommendation {padding:23px;position:relative;overflow:hidden}.recommendation:before {content:'';position:absolute;right:-40px;top:-60px;width:180px;height:180px;background:#ff8a4c12;border-radius:50%}.recommendation-title {font-size:26px;font-weight:850;letter-spacing:-.6px;margin:7px 0}.recommendation-sub {font-size:12px;color:#9eafc5;line-height:1.5}.stats {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin:19px 0}.stats>div {background:#0a111d;border:1px solid #26354a;border-radius:12px;padding:13px}.stats span {display:block;color:#8ea0b8;font-size:10px;text-transform:uppercase;letter-spacing:.8px}.stats strong {display:block;font-size:21px;color:#f8fafc;margin-top:5px}.note {border-top:1px solid #28364a;padding-top:13px;color:#93a4bb;font-size:11px;line-height:1.65}.hospital-list {display:grid;gap:10px}.hospital-card {padding:15px 16px;transition:transform .15s,border-color .15s}.hospital-card:hover {transform:translateY(-2px);border-color:#52627a}.hospital-top {display:flex;align-items:center;gap:12px}.rank-pill {width:34px;height:34px;flex-shrink:0;display:grid;place-items:center;border-radius:10px;background:#202d40;color:#fdba74;font-weight:850;font-size:12px}.hospital-main {min-width:0;flex:1}.hospital-name {font-size:14px;font-weight:750;color:#f1f5fb;overflow-wrap:anywhere}.hospital-address {font-size:10px;color:#8294ad;margin-top:4px}.hospital-eta {font-size:22px;font-weight:850;color:#ff9a62;text-align:right;white-space:nowrap}.hospital-eta small {display:block;font-size:9px;text-transform:uppercase;letter-spacing:1px;color:#a4b3c7}.hospital-bottom {display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-top:13px}.chip {border-radius:999px;padding:5px 8px;font-size:9px;font-weight:750;letter-spacing:.15px}.chip.good {background:#063b35;color:#6ee7b7}.chip.warn {background:#48231d;color:#fdba74}.chip.neutral {background:#202b3c;color:#bdcadd}.hospital-action {margin-left:auto;color:#48d7c5;font-size:10px}.hospital-explain {font-size:10px;color:#8597af;line-height:1.5;margin-top:10px}.empty-state,.error-card {padding:18px;color:#9eafc5;font-size:12px}.error-card {border-color:#7f302b;color:#fecaca}.error-card b {color:#fca5a5}.map-empty {height:300px;display:grid;place-items:center;border:1px dashed #344258;border-radius:16px;color:#7f91a9;background:#0d1522}

button.primary {background:linear-gradient(135deg,#ff9a62,#ea580c) !important;border:0 !important;color:#160b04 !important;font-weight:850 !important;box-shadow:0 8px 22px #ff8a4c28}.tabs {border-color:#253449 !important}.tab-nav button {color:#9aabc1 !important}.tab-nav button.selected {color:#fdba74 !important;border-color:#ff8a4c !important}.block,.form,.panel {border-color:#26364b !important}.label-wrap span,.wrap label {color:#cbd5e1 !important}.prose, .markdown-text {color:#cbd5e1 !important}.disclaimer {text-align:center;color:#6d7e95;font-size:10px;padding:18px 0 5px;line-height:1.6}.gradio-container input:not([type="checkbox"]):not([type="radio"]),.gradio-container textarea {background:#0a1220 !important;border-color:#2a3a51 !important;color:#f1f5f9 !important}.gradio-container input[type="checkbox"],.gradio-container input[type="radio"] {accent-color:#ff8a4c !important;opacity:1 !important;cursor:pointer !important;appearance:auto !important;width:16px !important;height:16px !important;flex:0 0 auto !important}.gradio-container label:has(input[type="checkbox"]),.gradio-container label:has(input[type="radio"]) {cursor:pointer !important;opacity:1 !important;color:#d7e2f0 !important}.gradio-container input::placeholder {color:#64748b !important}.header-tag {display:inline-flex;align-items:center;text-decoration:none !important;cursor:pointer;transition:all .18s ease}.header-tag:hover {border-color:#ff9a62;background:#ff8a4c20;color:#fff !important;transform:translateY(-1px)}.compare-wrap {margin-top:10px;padding:18px;border:1px solid #2a3a51;border-radius:16px;background:linear-gradient(145deg,#121d2d,#0d1522)}.compare-heading {font-size:11px;letter-spacing:1.5px;font-weight:850;color:#ff9a62;margin-bottom:12px}.compare-scroll {overflow-x:auto}.compare-table {width:100%;border-collapse:separate;border-spacing:0;min-width:650px}.compare-table th {text-align:left;color:#94a8c2;font-size:10px;text-transform:uppercase;letter-spacing:.7px;padding:11px 10px;border-bottom:1px solid #2a3a51}.compare-table td {padding:12px 10px;color:#e5edf8;font-size:12px;border-bottom:1px solid #202d40}.compare-table tr:last-child td {border-bottom:0}.compare-muted,.compare-note {font-size:10px;color:#8294ad;margin-top:4px}.compare-note {border-top:1px solid #27364b;padding-top:12px;line-height:1.6}

.gradio-container .tabs {margin-top:10px}.gradio-container .tab-nav {gap:8px;padding:6px;border:1px solid #23364a;border-radius:15px;background:#0c1523}.tab-nav button {border-radius:10px !important;padding:10px 15px !important}.gradio-container .block,.gradio-container .form {box-shadow:none !important}.gradio-container .wrap[data-testid="checkboxgroup"] {background:#111d2d !important;border:1px solid #2b4056 !important;border-radius:15px !important;padding:12px !important}.gradio-container button {transition:transform .18s ease,filter .18s ease,border-color .18s ease !important}.gradio-container button:hover {filter:brightness(1.08);transform:translateY(-1px)}.gradio-container button.secondary {background:linear-gradient(135deg,#20364a,#16283a) !important;border:1px solid #35516a !important;color:#e7f5ff !important}.gradio-container .panel-title {margin-top:5px}.map-empty {background:radial-gradient(circle at 20% 10%,#163047,#0c1625 70%);border-color:#2a4359}
@media(max-width:800px){#app-header{padding:23px 20px}.stats{grid-template-columns:repeat(3,minmax(0,1fr))}.stats strong{font-size:17px}.hospital-action{margin-left:0}}

"""



with gr.Blocks(
    title="Emergency Route Optimizer | Dispatch Console",
    theme=gr.themes.Base(
        primary_hue="teal",
        secondary_hue="orange",
        neutral_hue="slate",
        font=[
            gr.themes.GoogleFont("Inter"),
            "ui-sans-serif",
            "system-ui",
        ],
    ),
    css=CSS,
) as demo:

    real_state = gr.State(None)

    gr.HTML("""

    <header id='app-header'>

      <div class='brandline'><div class='brandmark'>✚</div><div class='brandname'>FIELD OPERATIONS / ROUTE OPTIMIZER</div></div>

      <h1 class='hero-title'>Ambulance Route Optimizer</h1>

      <div class='hero-copy'>A location-aware dispatch decision console combining road-based travel estimates, nearby hospital discovery and condition-informed comparison. Built for academic demonstration, with transparent data limitations.</div>

      <nav class='header-tags' aria-label='Quick navigation'><a class='header-tag' href='#emergency-intake'>● EMERGENCY INTAKE</a><a class='header-tag' href='#geo-panel'>OPENSTREETMAP MAP</a><a class='header-tag' href='#route-panel'>ROAD ROUTING</a><a class='header-tag' href='#hospital-comparison'>HOSPITAL COMPARISON</a></nav>

    </header>

    """)

    with gr.Tabs():

        with gr.Tab("Road Map & Hospital Search", id="live"):

            with gr.Row(equal_height=False):

                with gr.Column(scale=4, min_width=300):

                    gr.HTML("<div id='emergency-intake' class='panel-title'>01 / Emergency intake</div><div class='panel-sub'>Search for a real place or address, then describe the emergency. A road route is calculated only when routing data is available.</div>")

                    location_preset = gr.Dropdown(
                        choices=LOCATION_PRESETS,
                        value=LOCATION_PRESETS[0],
                        label="Quick location (Vijayawada region)",
                        info="Choose a preset or type any address below.",
                        interactive=True,
                    )
                    place = gr.Textbox(label="Pickup location", value=LOCATION_PRESETS[0], placeholder="Type any place or address", lines=1)
                    location_preset.change(lambda value: value, inputs=location_preset, outputs=place)

                    with gr.Row():

                        condition = gr.Dropdown(choices=CONDITIONS, value=CONDITIONS[0], label="Emergency category", interactive=True)

                        urgency = gr.Dropdown(choices=["Immediate", "Urgent", "Priority", "Standard"], value="Urgent", label="Urgency", interactive=True)

                    symptoms = gr.CheckboxGroup(choices=SYMPTOMS[CONDITIONS[0]], label="Observed symptoms (select all that apply)", interactive=True, value=[])

                    radius = gr.Slider(minimum=3, maximum=30, value=15, step=1, label="Hospital search radius (km)")

                    search_btn = gr.Button("Find hospitals & calculate routes", variant="primary", size="lg")

                    search_status = gr.Markdown("Enter a location to begin. External map services require an internet connection.")

                    gr.HTML("<div class='panel-sub'>Data note: this prototype cannot verify live bed availability, ambulance GPS, traffic conditions or clinical suitability.</div>")

                with gr.Column(scale=7, min_width=350):

                    gr.HTML("<div id='geo-panel' class='panel-title'>02 / Geographic situation</div><div class='panel-sub'>Road map, pickup location, hospital markers and the selected route appear here.</div>")

                    route_map = gr.HTML("<div class='map-empty'>Interactive road map will appear after a successful search.</div>")

            gr.HTML("<div id='route-panel' style='height:18px'></div><div class='panel-title'>03 / Recommendation & route selection</div><div class='panel-sub'>Ranked using road travel estimates and limited specialty tags when present. Verify hospital capability directly before relying on it.</div>")

            recommendation = gr.HTML("<div class='empty-state'>No recommendation yet. Search for a pickup location above.</div>")

            with gr.Row():

                with gr.Column(scale=5):

                    hospital_choice = gr.Dropdown(choices=[], label="Choose a hospital to display its road route", interactive=True)

                    select_route_btn = gr.Button("Display selected hospital route", variant="secondary")

                with gr.Column(scale=7):

                    ranking = gr.HTML("<div class='empty-state'>Hospital results will appear here.</div>")

            with gr.Group(elem_id="hospital-comparison"):

                gr.HTML("<div class='panel-title'>04 / Compare hospitals</div><div class='panel-sub'>Select two or more hospitals from the current results to compare road ETA, distance and available capability indications.</div>")

                hospital_compare_choices = gr.CheckboxGroup(choices=[], label="Hospitals to compare (select multiple)", interactive=True, value=[])

                compare_btn = gr.Button("Compare selected hospitals", variant="secondary")

                compare_output = gr.HTML("<div class='empty-state'>Your side-by-side comparison will appear here.</div>")

            search_btn.click(search_and_rank, inputs=[place, condition, symptoms, urgency, radius, real_state], outputs=[real_state, recommendation, hospital_choice, route_map, ranking, search_status, hospital_compare_choices, compare_output])

            condition.change(condition_changed, inputs=condition, outputs=symptoms)

            compare_btn.click(compare_hospitals, inputs=[hospital_compare_choices, real_state], outputs=compare_output)

            select_route_btn.click(choose_hospital, inputs=[hospital_choice, real_state], outputs=[real_state, recommendation, route_map, ranking])

            hospital_choice.change(choose_hospital, inputs=[hospital_choice, real_state], outputs=[real_state, recommendation, route_map, ranking], show_progress="minimal")



        with gr.Tab("Synthetic Algorithm Lab", id="synthetic"):

            gr.HTML("<div class='panel-title'>Benchmark graph / algorithm demonstration</div><div class='panel-sub'>This preserves the existing synthetic dataset workflow for explaining Dijkstra, weighted hospital scoring and road-incident rerouting. Synthetic graph nodes are not shown as real geographic locations.</div>")

            with gr.Row():

                with gr.Column():

                    synthetic_case = gr.Dropdown(choices=CASE_CHOICES, value=CASE_CHOICES[0][1], label="Synthetic emergency case")

                    synthetic_find = gr.Button("Run hospital selection", variant="primary")

                with gr.Column():

                    synthetic_incident_case = gr.Dropdown(choices=CASE_CHOICES, value=CASE_CHOICES[0][1], label="Emergency for incident rerouting")

                    synthetic_incident = gr.Dropdown(choices=INCIDENT_CHOICES, value=INCIDENT_CHOICES[0][1], label="Road incident")

                    synthetic_reroute_btn = gr.Button("Recalculate after road closure", variant="secondary")

            with gr.Row():

                synthetic_summary = gr.Markdown()

                synthetic_ranking = gr.Markdown()

            synthetic_technical = gr.Markdown()

            reroute_summary = gr.Markdown()

            reroute_technical = gr.Markdown()

            synthetic_find.click(synthetic_optimize, inputs=synthetic_case, outputs=[synthetic_summary, synthetic_ranking, synthetic_technical])

            synthetic_reroute_btn.click(synthetic_reroute, inputs=[synthetic_incident_case, synthetic_incident], outputs=[reroute_summary, reroute_technical])



    gr.HTML("<div class='disclaimer'>ACADEMIC DECISION-SUPPORT PROTOTYPE · Not a real emergency dispatch service or medical triage system. In an actual emergency, contact local emergency services and confirm hospital acceptance and capability.</div>")



if __name__ == "__main__":
    demo.launch()
