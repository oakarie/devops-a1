from typing import Any, Dict, List


def test_create_company_happy_path(client) -> None:
    payload = {"name": "Acme Co", "website": "https://acme.example"}
    r = client.post("/companies", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] > 0
    assert body["name"] == "Acme Co"
    assert body["website"] == "https://acme.example"


def test_list_companies_and_query_filter(client) -> None:
    companies = [
        {"name": "Acme Co"},
        {"name": "Beta Labs"},
        {"name": "Acme Widgets"},
    ]
    for c in companies:
        assert client.post("/companies", json=c).status_code == 201

    r = client.get("/companies")
    assert r.status_code == 200
    names = [c["name"] for c in r.json()]
    assert names == ["Acme Co", "Beta Labs", "Acme Widgets"]

    r = client.get("/companies?q=acme")
    assert r.status_code == 200
    names = [c["name"] for c in r.json()]
    assert names == ["Acme Co", "Acme Widgets"]


def test_get_company_by_id(client) -> None:
    created = client.post("/companies", json={"name": "Solo Co"}).json()
    cid = created["id"]
    r = client.get(f"/companies/{cid}")
    assert r.status_code == 200
    assert r.json()["name"] == "Solo Co"


def test_update_company_partial(client) -> None:
    created = client.post("/companies", json={"name": "Old Name"}).json()
    cid = created["id"]
    r = client.patch(f"/companies/{cid}", json={"name": "New Name", "city": "LA"})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "New Name"
    assert body["city"] == "LA"


def test_delete_company_and_404_after(client) -> None:
    created = client.post("/companies", json={"name": "Temp Co"}).json()
    cid = created["id"]
    r = client.delete(f"/companies/{cid}")
    assert r.status_code == 204

    # And poof — it's gone
    r = client.get(f"/companies/{cid}")
    assert r.status_code == 404

