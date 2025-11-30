import main


def test_health_endpoint(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_metrics_endpoint(client) -> None:
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "# HELP" in body
    assert "python_gc_objects_collected_total" in body
    assert "api_request_latency_seconds" in body


def test_get_db_generator_yields_and_closes() -> None:
    gen = main.get_db()
    session = next(gen)
    assert session.bind is not None
    gen.close()

