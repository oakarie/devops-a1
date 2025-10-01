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
