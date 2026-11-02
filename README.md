# Soundway — Seattle transit planner

Python / FastAPI · PostgreSQL · React · Leaflet

An interactive map of King County GTFS stops with departure-time-aware journey planning that minimizes transfers, then arrival time. No fabricated routes or sample schedules are displayed. The map populates after the real feed is imported.

## Run

Install Docker Desktop, then from this directory:

```sh
docker compose up --build -d
docker compose exec api python import_gtfs.py
```

Open http://localhost:8080. API documentation: http://localhost:8000/docs.

The importer downloads https://metro.kingcounty.gov/gtfs/google_transit.zip. Review the agency's data terms at https://kingcounty.gov/en/dept/metro/rider-tools/mobile-and-web-apps. To use an already downloaded ZIP:

```sh
docker compose cp /absolute/path/google_transit.zip api:/tmp/feed.zip
docker compose exec api python import_gtfs.py /tmp/feed.zip
```

Import is transactional: an error rolls back to the prior feed. Tables, indexes, and COPY streaming support the full feed without constructing all CSV rows in memory. PostgreSQL data persists in a named Docker volume. Run the importer again to refresh service; refresh the browser afterward. Stop with `docker compose down`.

## Use

Search and choose exact stops, or select them from the map. Choose a departure in Seattle local time and a transfer limit. The result lists boarding/alighting stops, route identifiers, headsigns, departure/arrival times, and the number of transfers. Changing a stop clears the previous itinerary. Route connectors are explicitly schematic straight lines, not GTFS shapes or road paths. OpenStreetMap/CARTO tiles and Google Fonts require internet access.

## Routing

The API expands active service for the previous, selected, and next service day, including calendar exceptions and GTFS hours beyond 24:00. Every round adds one boarding. It scans trips in stop order, boarding only after the traveler can reach the stop. Transfers require 120 seconds at the same stop ID. The first round reaching the destination gives fewest transfers; earliest arrival breaks ties within that round. Search is bounded to 24 hours and at most six transfers. A direct slower trip is deliberately preferred to a faster trip with a transfer.

Limitations: static schedules only; no walking links between distinct stop IDs, accessibility constraints, fares, frequency-based service, interlining, shape geometry, or live arrivals. Unscheduled intermediate stop-time rows are skipped, rather than inventing times. Current implementation reads active stop times per request and is intended as a single-user prototype; a production service should cache service-day trip arrays, add request limits, refresh feeds on a scheduler, and profile routing latency. Use an explicit ISO timestamp with offset for ambiguous daylight-saving times through the API; the UI uses local Seattle wall time.

## Development / checks

```sh
python3 -m unittest discover -s tests -v
```

For frontend development with Node 22 installed, run `npm install` then `npm run dev` in `frontend`; configure a Vite `/api` proxy to port 8000, or use the provided Docker/Nginx setup. PostgreSQL and dependencies are isolated in Docker. Default database credentials are for local development only; database port is not exposed to the host.
