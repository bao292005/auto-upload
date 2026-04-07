import pytest


def test_trigger_raises_when_not_windows(monkeypatch):
    from src import ldplayer_macro

    monkeypatch.setattr(ldplayer_macro.platform, "system", lambda: "Linux")

    with pytest.raises(RuntimeError):
        ldplayer_macro.trigger_ldplayer_macro()


def test_focus_window_not_found(monkeypatch):
    from src import ldplayer_macro

    monkeypatch.setattr(ldplayer_macro.platform, "system", lambda: "Windows")

    class FakeWin:
        def exists(self, timeout=None):
            return False

    class FakeDesktop:
        def __init__(self, backend=None):
            pass

        def window(self, title=None, title_re=None):
            return FakeWin()

    monkeypatch.setitem(__import__("sys").modules, "pywinauto", type("M", (), {"Desktop": FakeDesktop}))

    with pytest.raises(ldplayer_macro.LDPlayerWindowNotFound):
        ldplayer_macro.focus_ldplayer_window("LDPlayer")


def test_trigger_retries_then_fails(monkeypatch):
    from src import ldplayer_macro

    monkeypatch.setattr(ldplayer_macro.platform, "system", lambda: "Windows")

    # Make focus succeed but foreground verify fail
    monkeypatch.setattr(ldplayer_macro, "focus_ldplayer_window", lambda title: 123)
    monkeypatch.setattr(ldplayer_macro, "_is_foreground_window", lambda handle, expected_title=None: False)
    monkeypatch.setattr(ldplayer_macro, "send_hotkey_ctrl_f5", lambda: None)

    with pytest.raises(RuntimeError):
        ldplayer_macro.trigger_ldplayer_macro(window_title="LDPlayer", retries=2, focus_backoff_s=0)


def test_trigger_success(monkeypatch):
    from src import ldplayer_macro

    monkeypatch.setattr(ldplayer_macro.platform, "system", lambda: "Windows")

    calls = {"focus": 0, "send": 0}

    def _focus(title):
        calls["focus"] += 1

    def _send():
        calls["send"] += 1

    monkeypatch.setattr(ldplayer_macro, "focus_ldplayer_window", _focus)
    monkeypatch.setattr(ldplayer_macro, "_is_foreground_window", lambda handle, expected_title=None: True)
    monkeypatch.setattr(ldplayer_macro, "send_hotkey_ctrl_f5", _send)

    ldplayer_macro.trigger_ldplayer_macro(window_title="LDPlayer", retries=3, focus_backoff_s=0)

    assert calls["focus"] == 1
    assert calls["send"] == 1
