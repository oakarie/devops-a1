## GPT Findability Tracker

A teeny FastAPI app whose only job (for now) is to say it's alive.

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

### Companies

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
