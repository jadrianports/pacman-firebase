import sys
import updater


def test_is_active_false_in_dev():
    # pytest runs unfrozen
    assert updater.is_active() is False


def test_check_and_apply_noop_when_not_frozen(monkeypatch):
    called = {"ran": False}
    monkeypatch.setattr(updater, "_run_update", lambda on_status: called.__setitem__("ran", True))
    monkeypatch.setattr(updater, "is_active", lambda: False)
    assert updater.check_and_apply() is False
    assert called["ran"] is False          # never even attempts the update when unfrozen


def test_check_and_apply_swallows_errors(monkeypatch):
    monkeypatch.setattr(updater, "is_active", lambda: True)
    def boom(on_status):
        raise RuntimeError("network down / bad metadata")
    monkeypatch.setattr(updater, "_run_update", boom)
    # must NOT raise — the game has to launch regardless
    assert updater.check_and_apply() is False


def test_check_and_apply_returns_true_when_update_applied(monkeypatch):
    monkeypatch.setattr(updater, "is_active", lambda: True)
    monkeypatch.setattr(updater, "_run_update", lambda on_status: True)
    assert updater.check_and_apply() is True
