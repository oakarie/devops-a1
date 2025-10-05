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


