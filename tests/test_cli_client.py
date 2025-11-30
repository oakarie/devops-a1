"""Basic coverage for CLI flow: reuse/create company, signal collection, and a
mocked happy-path main() invocation."""

import builtins
from typing import Iterable, List

import pytest
import requests

import cli_client


class DummyResponse:
    """Minimal response stub with the methods cli_client expects."""

    def __init__(self, payload):
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


def _fake_input_factory(responses: Iterable[str]):
    iterator = iter(responses)

    def _fake_input(_prompt: str) -> str:
        try:
            return next(iterator)
        except StopIteration:
            pytest.fail("Ran out of fake input responses")

    return _fake_input


def _blank_optional_prompts() -> List[str]:
    """Return empty answers for the six optional company fields."""
    return ["", "", "", "", "", ""]


def _http_error(response_text: str) -> requests.HTTPError:
    err = requests.HTTPError("boom")
    err.response = type("Resp", (), {"text": response_text})()
    return err


def test_cli_find_or_create_company_reuses_existing(monkeypatch):
    responses = ["Acme Co", *_blank_optional_prompts()]
    monkeypatch.setattr(builtins, "input", _fake_input_factory(responses))

    existing_id = 7

    def fake_get(url, *_, **__):
        assert url == f"{cli_client.API}/companies"
        return DummyResponse([{"id": existing_id, "name": "Acme Co"}])

    def fake_post(*_, **__):
        pytest.fail("Should not POST when company already exists")

    monkeypatch.setattr(cli_client.requests, "get", fake_get)
    monkeypatch.setattr(cli_client.requests, "post", fake_post)

    company_id = cli_client.find_or_create_company()
    assert company_id == existing_id


def test_cli_find_or_create_company_creates_new(monkeypatch):
    responses = [
        "Rocket Co",
        "https://rocket.example",
        "USA",
        "CA",
        "San Francisco",
        "",
        "",
    ]
    monkeypatch.setattr(builtins, "input", _fake_input_factory(responses))

    def fake_get(url, *_, **__):
        assert url == f"{cli_client.API}/companies"
        return DummyResponse([])

    captured_payload = {}

    def fake_post(url, *, json=None, **__):
        assert url == f"{cli_client.API}/companies"
        captured_payload.update(json or {})
        return DummyResponse({"id": 42})

    monkeypatch.setattr(cli_client.requests, "get", fake_get)
    monkeypatch.setattr(cli_client.requests, "post", fake_post)

    company_id = cli_client.find_or_create_company()
    assert company_id == 42
    assert captured_payload == {
        "name": "Rocket Co",
        "website": "https://rocket.example",
        "country": "USA",
        "state": "CA",
        "city": "San Francisco",
    }


def test_cli_collect_signals_all_yes(monkeypatch):
    responses = ["y"] * len(cli_client.SIGNALS)
    monkeypatch.setattr(builtins, "input", _fake_input_factory(responses))

    answers = cli_client.collect_signals()
    assert all(answers[name] is True for name in cli_client.SIGNALS)


def test_cli_main_happy_path(monkeypatch, capsys):
    signal_inputs = ["y", "n", "y", "y", "n", "y", "n", "y", "y", "n"]
    responses = ["CLI Co", *_blank_optional_prompts(), *signal_inputs]
    monkeypatch.setattr(builtins, "input", _fake_input_factory(responses))

    def fake_get(url, *_, **__):
        assert url == f"{cli_client.API}/companies"
        return DummyResponse([])

    company_posts: List[dict] = []
    evaluate_posts: List[dict] = []

    def fake_post(url, *, json=None, **__):
        if url == f"{cli_client.API}/companies":
            company_posts.append(json or {})
            return DummyResponse({"id": 1})
        if url == f"{cli_client.API}/evaluate":
            evaluate_posts.append(json or {})
            return DummyResponse(
                {
                    "company_id": json["company_id"],
                    "score": 0.93,
                    "badge": "excellent",
                    "evidence": ["+ contact page", "+ clear services page"],
                }
            )
        pytest.fail(f"Unexpected POST to {url}")

    monkeypatch.setattr(cli_client.requests, "get", fake_get)
    monkeypatch.setattr(cli_client.requests, "post", fake_post)

    cli_client.main()

    captured = capsys.readouterr()
    assert '"company_id": 1' in captured.out
    assert '"badge": "excellent"' in captured.out
    assert company_posts == [{"name": "CLI Co"}]

    expected_signal_bools = {
        name: answer == "y" for name, answer in zip(cli_client.SIGNALS, signal_inputs)
    }

    assert evaluate_posts == [
        {
            "company_id": 1,
            "has_contact_page": expected_signal_bools["contact page"],
            "has_clear_services_page": expected_signal_bools["clear services page"],
            "has_gmb_or_maps_listing": expected_signal_bools["maps/GMB listing"],
            "has_recent_updates": expected_signal_bools["recent updates"],
            "has_reviews_or_testimonials": expected_signal_bools[
                "reviews/testimonials"
            ],
            "has_online_booking_or_form": expected_signal_bools["online booking/form"],
            "uses_basic_schema_markup": expected_signal_bools["basic schema markup"],
            "has_consistent_name_address_phone": expected_signal_bools[
                "NAP consistent"
            ],
            "has_fast_load_time_claim": expected_signal_bools["loads fast"],
            "content_matches_intent": expected_signal_bools["content matches intent"],
        }
    ]


def test_cli_prompt_exits_on_eof(monkeypatch, capsys):
    def _raise_eof(_prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr(builtins, "input", _raise_eof)

    with pytest.raises(SystemExit) as exc:
        cli_client.prompt("Name: ")

    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Bye!" in captured.err


def test_cli_prompt_yes_no_reprompts_on_invalid(monkeypatch, capsys):
    responses = ["maybe", "y"]
    monkeypatch.setattr(builtins, "input", _fake_input_factory(responses))

    result = cli_client.prompt_yes_no("Check?")
    assert result is True

    captured = capsys.readouterr()
    assert "Please answer y/yes or n/no." in captured.out


def test_cli_find_or_create_company_handles_list_failure(monkeypatch, capsys):
    responses = ["Retry Co", *_blank_optional_prompts()]
    monkeypatch.setattr(builtins, "input", _fake_input_factory(responses))

    def _boom(*_, **__):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(cli_client.requests, "get", _boom)

    with pytest.raises(SystemExit):
        cli_client.find_or_create_company()

    captured = capsys.readouterr()
    assert "Couldn't list companies: boom" in captured.err


def test_cli_find_or_create_company_handles_post_http_error(monkeypatch, capsys):
    responses = ["Fresh Co", *_blank_optional_prompts()]
    monkeypatch.setattr(builtins, "input", _fake_input_factory(responses))

    monkeypatch.setattr(
        cli_client.requests,
        "get",
        lambda url, *_, **__: DummyResponse([]),
    )

    def _fail_post(*_, **__):
        raise _http_error("bad payload")

    monkeypatch.setattr(cli_client.requests, "post", _fail_post)

    with pytest.raises(SystemExit):
        cli_client.find_or_create_company()

    captured = capsys.readouterr()
    assert "API said no: bad payload" in captured.err


def test_cli_main_handles_evaluate_http_error(monkeypatch, capsys):
    monkeypatch.setattr(cli_client, "find_or_create_company", lambda: 123)
    monkeypatch.setattr(
        cli_client,
        "collect_signals",
        lambda: {name: False for name in cli_client.SIGNALS},
    )

    def _fail_post(url, *_, **__):
        assert url == f"{cli_client.API}/evaluate"
        raise _http_error("evaluation failed")

    monkeypatch.setattr(cli_client.requests, "post", _fail_post)

    with pytest.raises(SystemExit):
        cli_client.main()

    captured = capsys.readouterr()
    assert "API said no: evaluation failed" in captured.err

