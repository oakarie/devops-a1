## GPT Findability Tracker

A teeny FastAPI app that scores a company's basic web findability. No AI, no internet calls — just deterministic rules you can read with coffee in hand.

### Quickstart in 60 seconds

1) Install deps

```
pip install -r requirements.txt
```

2) Run the API

```
uvicorn main:app --reload
```

3) Run the CLI (optional but comfy)

```
python cli_client.py
```

### Quickstart

1) Install deps

```
pip install -r requirements.txt
```

2) Run the server

```
uvicorn main:app --reload
```

3) Healthcheck

```
curl http://127.0.0.1:8000/health
```

### API tour (tiny and friendly)

- Healthcheck

```
curl http://127.0.0.1:8000/health
```

- Create a company

```
curl -s -X POST http://127.0.0.1:8000/companies \
  -H 'Content-Type: application/json' \
  -d '{"name": "Acme Co", "website": "https://acme.example"}'
```

- List companies (+ optional name filter)

```
curl -s 'http://127.0.0.1:8000/companies?q=acme'
```

- Get one by id

```
curl -s http://127.0.0.1:8000/companies/1
```

- Update (partial)

```
curl -s -X PATCH http://127.0.0.1:8000/companies/1 \
  -H 'Content-Type: application/json' \
  -d '{"city": "New York"}'
```

- Delete

```
curl -i -X DELETE http://127.0.0.1:8000/companies/1
```

- Evaluate (score signals → save Evaluation)

```
curl -s -X POST http://127.0.0.1:8000/evaluate \
  -H 'Content-Type: application/json' \
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

Typical response keys:

```
{ "id": 123, "company_id": 1, "score": 0.84, "badge": "excellent", "evidence": ["+ contact page", "..."] }
```

Create one (name is the only must-have):

```
curl -s -X POST http://127.0.0.1:8000/companies \
  -H 'Content-Type: application/json' \
  -d '{"name": "Acme Co", "website": "https://acme.example"}'
```

List them (optionally filter by name):

```
curl -s 'http://127.0.0.1:8000/companies?q=acme'
```

Update one (partial update — only what you send changes):

```
curl -s -X PATCH http://127.0.0.1:8000/companies/1 \
  -H 'Content-Type: application/json' \
  -d '{"name": "Acme Incorporated", "city": "New York"}'
```

Delete one (bye bye):

```
curl -i -X DELETE http://127.0.0.1:8000/companies/1
```

### Evaluate a company

Sample request body:

```
{
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
}
```

Call it:

```
curl -s -X POST http://127.0.0.1:8000/evaluate \
  -H 'Content-Type: application/json' \
  -d @body.json
```

Typical response keys:

```
{
  "id": 123,
  "company_id": 1,
  "score": 0.84,
  "badge": "excellent",
  "evidence": ["+ contact page", "..."],
  "created_at": "..."
}
```

### Tests (and coverage)

Run tests:

```
pytest --maxfail=1 -q
```

With coverage:

```
pytest --maxfail=1 -q --cov=.
```

Coverage goal: ~90% so we catch the basics without chasing ghosts.

Exact coverage commands:

```
pytest --maxfail=1 -q --cov=.
```

The report prints in the terminal by default; if you want HTML too:

```
pytest --cov=. --cov-report=term-missing --cov-report=html
```

### CLI helper

If you prefer typing answers instead of crafting JSON, there's a tiny CLI:

```
python cli_client.py
```

It will:
- ask for company details (reuses an existing one by name if found)
- ask y/n for the 10 signals (same order as scoring)
- call /evaluate and pretty-print the score, badge, and evidence

Pro tip (in two steps):
1) start API → `uvicorn main:app --reload`
2) run CLI → `python cli_client.py`

### Architecture (ASCII edition)

```
[ CLI ]  --->  [ FastAPI app ]  <-->  [ SQLite DB ]
                 ^   ^
                 |   |
           compute_findability (pure, deterministic)
```

### Notes

- No AI, no external services. Deterministic scoring with transparent rules.
- Built small on purpose — perfect for DevOps follow-up tasks.
- Tone: friendly, not corporate. Bring your own coffee.

### CLI helper

If you prefer typing answers instead of crafting JSON, there's a tiny CLI:

```
python cli_client.py
```

It will:
- ask for company details (reuses an existing one by name if found)
- ask y/n for the 10 signals (same order as scoring)
- call /evaluate and pretty-print the score, badge, and evidence

Pro tip (in two steps):
1) start API → `uvicorn main:app --reload`
2) run CLI → `python cli_client.py`
