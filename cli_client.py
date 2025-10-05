import json
import sys
from typing import Dict, List

import requests


API = "http://127.0.0.1:8000"


SIGNALS: List[str] = [
    "contact page",
    "clear services page",
    "maps/GMB listing",
    "recent updates",
    "reviews/testimonials",
    "online booking/form",
    "basic schema markup",
    "NAP consistent",
    "loads fast",
    "content matches intent",
]


def prompt(msg: str) -> str:
    try:
        return input(msg).strip()
    except EOFError:
        print("\nBye!", file=sys.stderr)
        sys.exit(1)


def prompt_yes_no(msg: str) -> bool:
    while True:
        ans = prompt(msg + " [y/n]: ").lower()
        if ans in {"y", "yes"}:
            return True
        if ans in {"n", "no"}:
            return False
        print("Please answer y/yes or n/no.")


def find_or_create_company() -> int:
    print("Let's grab the company details (only name is required).")
    name = ""
    while not name:
        name = prompt("Name: ")
        if not name:
            print("Name is required — give it a shot.")

    website = prompt("Website (optional): ") or None
    country = prompt("Country (optional): ") or None
    state = prompt("State (optional): ") or None
    city = prompt("City (optional): ") or None
    industry = prompt("Industry (optional): ") or None
    niche = prompt("Niche (optional): ") or None

    # Try to reuse an existing company by case-insensitive name
    try:
        r = requests.get(f"{API}/companies")
        r.raise_for_status()
        existing = r.json()
    except Exception as exc:
        print(f"Couldn't list companies: {exc}", file=sys.stderr)
        sys.exit(1)

    for c in existing:
        if c["name"].strip().lower() == name.strip().lower():
            print(f"Reusing company id {c['id']} ({c['name']}).")
            return c["id"]

    payload: Dict[str, str] = {"name": name}
    if website:
        payload["website"] = website
    if country:
        payload["country"] = country
    if state:
        payload["state"] = state
    if city:
        payload["city"] = city
    if industry:
        payload["industry"] = industry
    if niche:
        payload["niche"] = niche

    try:
        r = requests.post(f"{API}/companies", json=payload)
        r.raise_for_status()
        company_id = r.json()["id"]
        print(f"Created company with id {company_id}.")
        return company_id
    except requests.HTTPError as http_err:
        print(f"API said no: {http_err.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Couldn't create company: {exc}", file=sys.stderr)
        sys.exit(1)


def collect_signals() -> Dict[str, bool]:
    print("Now let's capture a few quick signals — just y/n.")
    answers: Dict[str, bool] = {}
    for name in SIGNALS:
        answers[name] = prompt_yes_no(f"Does it have: {name}?")
    return answers


def main() -> None:
    company_id = find_or_create_company()
    signals = collect_signals()

    body = {
        "company_id": company_id,
        "has_contact_page": signals["contact page"],
        "has_clear_services_page": signals["clear services page"],
        "has_gmb_or_maps_listing": signals["maps/GMB listing"],
        "has_recent_updates": signals["recent updates"],
        "has_reviews_or_testimonials": signals["reviews/testimonials"],
        "has_online_booking_or_form": signals["online booking/form"],
        "uses_basic_schema_markup": signals["basic schema markup"],
        "has_consistent_name_address_phone": signals["NAP consistent"],
        "has_fast_load_time_claim": signals["loads fast"],
        "content_matches_intent": signals["content matches intent"],
    }

    try:
        r = requests.post(f"{API}/evaluate", json=body)
        r.raise_for_status()
    except requests.HTTPError as http_err:
        print(f"API said no: {http_err.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Couldn't call evaluate: {exc}", file=sys.stderr)
        sys.exit(1)

    data = r.json()
    print("\nNice, here's your score:\n")
    print(json.dumps({
        "company_id": data.get("company_id"),
        "score": data.get("score"),
        "badge": data.get("badge"),
        "evidence": data.get("evidence"),
    }, indent=2))

    print("\nNext steps:")
    print("  1) start API  →  uvicorn main:app --reload")
    print("  2) run CLI   →  python cli_client.py")


if __name__ == "__main__":
    main()


