"""
GPT Findability Tracker

This tiny FastAPI app just proves it's alive and listening.
More brains coming later... for now, it's a friendly healthcheck.
"""

from fastapi import FastAPI


app = FastAPI(
    title="GPT Findability Tracker",
    description=(
        "A tiny heartbeat service to say we're alive. No fluff, just ok."
    ),
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


