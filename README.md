# Google Maps Scraper API

A FastAPI service for scraping Google Maps results with Playwright. Built to be called from automation tools like ToolJet or n8n.

## API
- `GET|POST /google_maps/scrape` — query Google Maps. Query params: `query` (required), `max_places` (optional int), `lang` (default `en`), `headless` (default `true`).
- `GET /` and `GET /health` — basic health checks.

## Environment
Set these in `.env` (see `.env.example`):
- `PORT` — API port (default `8001`).
- `ALLOWED_ORIGINS` — comma-separated origins for CORS (set your ToolJet URL).
- Database: either `DB_URI` or `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- `ENVIRONMENT`, `LOG_LEVEL` (optional).

## Local development
```bash
poetry install
poetry run playwright install chromium
poetry run uvicorn slade_digital_scrapers.infrastructure.api.api:app --reload --port 8001
```
API docs available at `http://localhost:8001/docs`.

## Docker / production
```bash
cp .env.example .env   # update values for your server/ToolJet origin and database
docker network create shark # or change the network name in docker-compose.yml
docker compose up --build -d
curl http://localhost:8001/health
```
The compose file maps `${PORT:-8001}` on the host to the same port in the container. The image installs Playwright Chromium and required system deps.

## ToolJet usage
1. Add a REST API data source with base URL `http(s)://<server>:<PORT>`.
2. Enable CORS by setting `ALLOWED_ORIGINS` in `.env` to your ToolJet URL if the request is browser-initiated.
3. Create a query that calls `GET /google_maps/scrape` with query params, e.g.:
   - `query=hotels in Seattle`
   - `max_places=25`
   - `lang=en`
4. Bind the returned list to your table/list components.

## Notes
- Playwright can be rate-limited by Google; tune `max_places` or add delays if needed.
- For production, put this behind a reverse proxy (NGINX/Caddy) and add authentication if exposing publicly.
