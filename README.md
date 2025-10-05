# GPT Findability Tracker

A lightweight FastAPI application that measures how "findable" a business is based on simple web presence signals.  
There’s no AI, no external calls — everything runs locally using deterministic rules.

The app includes:
- A FastAPI backend with SQLite for storage
- CRUD endpoints for managing companies
- An evaluation endpoint that scores web visibility signals
- A simple CLI client for local testing
- Automated tests with Pytest and coverage reporting

---

## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the API
```bash
uvicorn main:app --reload
```

If successful, you’ll see:
```
Uvicorn running on http://127.0.0.1:8000
```

### 3. Check that it’s running
```bash
curl http://127.0.0.1:8000/health
```
Expected output:
```json
{"status": "ok"}
```

### 4. (Optional) View the docs
You can open the interactive API docs at:
```
http://127.0.0.1:8000/docs
```

---

## Example Workflow

### Create a company
```bash
curl -X POST http://127.0.0.1:8000/companies \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Co", "website": "https://acme.example"}'
```

### List all companies
```bash
curl http://127.0.0.1:8000/companies
```

### Get one company by ID
```bash
curl http://127.0.0.1:8000/companies/1
```

### Update company details
```bash
curl -X PATCH http://127.0.0.1:8000/companies/1 \
  -H "Content-Type: application/json" \
  -d '{"city": "New York"}'
```

### Delete a company
```bash
curl -X DELETE http://127.0.0.1:8000/companies/1
```

---

## Evaluating a Company

Each company can be evaluated based on ten basic web signals.

Example request:
```bash
curl -X POST http://127.0.0.1:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 1,
    "has_contact_page": true,
    "has_clear_services_page": true,
    "has_gmb_or_maps_listing": true,
    "has_recent_updates": false,
    "has_reviews_or_testimonials": true,
    "has_online_booking_or_form": false,
    "uses_basic_schema_markup": true,
    "has_consistent_name_address_phone": true,
    "has_fast_load_time_claim": true,
    "content_matches_intent": true
  }'
```

Typical response:
```json
{
  "id": 1,
  "company_id": 1,
  "score": 0.84,
  "badge": "excellent",
  "evidence": ["+ contact page", "+ clear services page"],
  "created_at": "2025-10-05T20:41:30"
}
```

---

## CLI Usage

If you prefer a quick interactive run:
```bash
python cli_client.py
```

The CLI will:
1. Ask for company details (name, website, etc.)
2. Ask yes/no questions for each signal
3. Submit to the API and print the score, badge, and evidence

Make sure the API is running first:
```bash
uvicorn main:app --reload
```

---

## Running Tests

Run all tests:
```bash
pytest --maxfail=1 -q
```

Run with coverage:
```bash
pytest --cov=. --cov-report=term-missing
```

HTML coverage report:
```bash
pytest --cov=. --cov-report=html
```
Then open `htmlcov/index.html` in your browser.

---

## Project Structure

```
.
├── main.py                # FastAPI app with routes and models
├── cli_client.py          # CLI helper for testing the API
├── requirements.txt
├── tests/                 # Pytest suite
│   ├── test_companies.py
│   ├── test_evaluations.py
│   └── test_scoring.py
└── README.md
```

---

## Notes

- No external dependencies beyond what’s listed in `requirements.txt`.
- No API keys or network access required.
- Built small on purpose — clear enough to extend later for DevOps or scaling tasks.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Port already in use | Run `uvicorn main:app --reload --port 8080` |
| "Connection refused" | Make sure the API is running before using the CLI |
| Validation error (422) | Check your JSON keys and values |
| Database not updating | Delete `gpt_findability.db` and restart |
| Tests fail unexpectedly | Ensure Python ≥ 3.11 and reinstall dependencies |


