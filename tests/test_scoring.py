from main import compute_findability, SIGNALS


def _signals_with_true(n: int) -> dict[str, bool]:
    s = {name: False for name in SIGNALS}
    for i, name in enumerate(SIGNALS[:n]):
        s[name] = True
    return s


def test_scoring_zero_true_signals() -> None:
    res = compute_findability(_signals_with_true(0))
    assert res["badge"] == "poor"
    assert res["score"] == 0.0
    assert res["evidence"] == ["No clear signals provided"]


def test_scoring_one_true_signal_has_evidence() -> None:
    res = compute_findability(_signals_with_true(1))
    assert res["badge"] == "poor"  # still below the “mentioned” threshold
    assert 0.0 < res["score"] < 0.2
    assert res["evidence"] == ["+ contact page"]


def test_scoring_two_true_signals() -> None:
    res = compute_findability(_signals_with_true(2))
    assert 0.0 <= res["score"] <= 1.0
    assert res["badge"] in {"fair", "good", "excellent"}


def test_scoring_four_true_signals() -> None:
    res = compute_findability(_signals_with_true(4))
    assert 0.0 <= res["score"] <= 1.0
    assert res["badge"] in {"good", "excellent"}


def test_scoring_six_true_signals() -> None:
    res = compute_findability(_signals_with_true(6))
    assert res["badge"] == "excellent"
    assert res["score"] >= 0.8


