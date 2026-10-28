# Ambulance Route & Hospital Selection Optimizer 2.0

A dark-mode Gradio application combining a real-world map workflow with the original synthetic graph-algorithm lab. The original Dijkstra implementation, hospital suitability scoring and incident rerouting are preserved.

## What changed

- **Dark dispatch UI:** navy surfaces, orange action accents, cyan map markers, responsive cards and readable high-contrast labels.
- **Place/address search:** Nominatim geocoding converts the user's search into real coordinates.
- **Real road map:** OpenStreetMap tiles rendered with Folium/Leaflet; the pickup and nearby hospital markers are displayed on the map.
- **Road travel estimates:** OSRM supplies route distances, durations and the selected route geometry. The highlighted route updates when a different hospital is selected.
- **Patient intake:** emergency category, symptom checklist and urgency selector.
- **Nearby hospital discovery:** Overpass API finds named hospitals in the selected search radius. If the primary public endpoint is unavailable, the app tries configured public mirrors before reporting a service error.
- **Condition-aware comparison:** explicitly mapped specialty tags can influence ranking, with a small tie-breaker except for Immediate urgency. Unknown hospital capability is labelled unverified rather than assumed.
- **Synthetic Algorithm Lab:** original case-based hospital selection and road-incident rerouting remain available for demonstrating Dijkstra on the supplied synthetic graph.
- **Tests:** existing algorithm/workflow tests plus tests for geographic distance and the new routing logic.

## Important data limitations

The included CSV road graph is synthetic and its `x`/`y` fields are not real latitude/longitude. It is therefore **not** used to position real-world markers. The real-map workflow obtains geographic locations from external OpenStreetMap-based services. OpenStreetMap tags do not reliably provide live bed capacity, hospital acceptance, emergency department status or full specialty capability. The application does not claim those data are verified.

The public geocoder, Overpass and OSRM endpoints require internet access, have rate/availability limits, and are not intended to guarantee emergency-service performance. Travel times are estimates, not live-traffic predictions. The app is an academic prototype, not a medical triage or real dispatch system. In an actual emergency, contact local emergency services and confirm hospital acceptance and capability directly.

## Run locally (Windows PowerShell)

```powershell
cd ambulance-route-optimizer
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open the local URL printed by Gradio (normally `http://127.0.0.1:7860`). If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` for the current terminal, or install with `.venv\Scripts\python.exe -m pip install -r requirements.txt` and run `.venv\Scripts\python.exe app.py`.

## Run tests

```powershell
python -m pytest -q
```

## Configuration

Optional environment variables are documented in `.env.example`:

- `NOMINATIM_URL` — geocoding endpoint.
- `OVERPASS_URL` — primary nearby hospital discovery endpoint.
- `OVERPASS_FALLBACK_URLS` — comma-separated fallback Overpass endpoints, tried if the primary endpoint fails or returns no elements.
- `OSRM_URL` — road routing endpoint.
- `MAP_REQUEST_TIMEOUT` — HTTP timeout in seconds.
- `MAP_USER_AGENT` — descriptive application identifier; set a valid contact detail before sustained use of public geocoding services.

The app loads an optional local `.env` file at startup. Keep `.env` private; it is excluded by `.gitignore`. Environment variables supplied by your deployment host take precedence according to the host and dotenv configuration.

## Project structure

```text
app.py                         Gradio UI and workflow callbacks
src/algorithms/dijkstra.py     Original shortest-path algorithm
src/optimization/              Original hospital selection and rerouting
src/services/application.py    Original synthetic dataset workflow
src/services/real_world.py    Geocoding, hospital discovery and road routing
src/graph/                     Original synthetic graph implementation
src/models/                    Original domain models
data/raw/                      Original synthetic benchmark datasets
tests/                         Algorithm, workflow and real-world service tests
docs/                          Project and algorithm notes
```

## Deployment with Gradio

The application starts with `python app.py`. For a hosted deployment, configure the same environment variables in the host's environment settings and install `requirements.txt`. Do not enable public sharing or expose a production endpoint as an actual emergency dispatch service. For sustained or production use, select service providers with suitable usage terms, availability guarantees and privacy controls.
