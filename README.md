# Visibility Tracker (Assignment 2)

## 1. Overview
Small FastAPI service + SQLite database that scores how “visible” a business is across classic SEO, local GEO signals, and GPT-style assistant cues (contact page, reviews, etc.).  
Stack: FastAPI, SQLAlchemy, SQLite, Prometheus metrics, Pytest, plus a plain HTML/JS frontend that talks to the API directly. Everything is deterministic, rule-based, and offline-friendly so it runs well in a classroom or lab. Today it’s a simple visibility scorer; later it could power GPT probes without changing the core API.

## 2. Local setup
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
That boots the API on http://127.0.0.1:8000 with live reload for easier debugging.

## 3. Running the frontend
- Open `frontend/index.html` in a browser, or (once GitHub Pages is enabled) visit `https://<your-github-username>.github.io/devops-a2/`.
- The UI collects company metadata, lets you toggle the ten signals, and then calls `/companies` followed by `/evaluate` to show the score, badge, and evidence card.

## 4. API overview
- `GET /health` – sanity check used by tests and Docker health probes.
- `POST /companies` / `GET /companies` / `GET|PATCH|DELETE /companies/{id}` – CRUD around the SQLite table.
- `POST /evaluate` – stores an evaluation tied to a company and returns score, badge, and evidence list.
- `GET /metrics` – Prometheus text exposition with request counters and latency histograms.

## 5. Docker usage
```bash
docker build -t gpt-findability:latest .
docker run --rm -p 8000:8000 gpt-findability:latest
```
The container installs requirements, copies the repo into `/app`, and starts `uvicorn main:app --host 0.0.0.0 --port 8000`.

## 6. Tests & coverage
```bash
pytest --maxfail=1 --cov=. --cov-report=term-missing --cov-fail-under=70
```
The same command runs locally and inside CI; it fails the build if coverage dips under 70%.

## 7. CI & CD
- `.github/workflows/ci.yml` runs on every push/PR, installs deps on Python 3.11, and executes the test+coverage command above.
- `.github/workflows/deploy-backend.yml` triggers only when `main` updates, repeats the tests, builds `gpt-findability-backend`, and includes a placeholder step where Render/Fly/EC2 deployment would plug in (expects secrets such as `CLOUD_API_KEY` / `SERVICE_ID`).
- `.github/workflows/deploy-frontend.yml` publishes the static `frontend/` folder to GitHub Pages whenever `main` changes, so the UI auto-hosts without extra infra.

## 8. Monitoring
Every HTTP request passes through a Prometheus-instrumented middleware.  
`GET /metrics` exposes `api_request_count{method,path,status_code}` and `api_request_latency_seconds{method,path}` so we can plug Grafana/Prometheus in later or just curl it during demos.

## 9. Assignment 2 report
[Assignment 2 Report (PDF)](assignment-2-report.pdf) – placeholder copy lives in the repo so graders have a stable link; replace it with the final deliverable as needed.
