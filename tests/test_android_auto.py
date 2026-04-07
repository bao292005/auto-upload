import importlib
import sys
import types


def _load_android_auto(monkeypatch):
    fake_u2 = types.SimpleNamespace(connect=lambda serial: None)
    monkeypatch.setitem(sys.modules, "uiautomator2", fake_u2)
    import src.android_auto as android_auto

    return importlib.reload(android_auto)


def test_extract_title_from_image_filename_normalizes(monkeypatch):
    android_auto = _load_android_auto(monkeypatch)
    uploader = android_auto.YouTubeUploader()

    title = uploader.extract_title_from_image_filename(
        "C:/tmp/001_nhan_sắc-Hoa_hậu_Đại_dương_Việt_Nam_2025.jpg"
    )

    assert title == "nhan sắc Hoa hậu Đại dương Việt Nam 2025"


def test_extract_title_from_image_filename_fallback(monkeypatch):
    android_auto = _load_android_auto(monkeypatch)
    uploader = android_auto.YouTubeUploader()

    title = uploader.extract_title_from_image_filename("C:/tmp/001__---.jpg")

    assert title == "YouTube Short!"


def test_extract_title_from_image_filename_repairs_mojibake(monkeypatch):
    android_auto = _load_android_auto(monkeypatch)
    uploader = android_auto.YouTubeUploader()

    title = uploader.extract_title_from_image_filename(
        "C:/tmp/4_khung_giß╗¥_v├áng_trong_ng├áy.jpg"
    )

    assert "ß" not in title
    assert "├" not in title
    assert "╗" not in title


def test_click_upload_button_uses_upload_bottom_button_selector(monkeypatch):
    android_auto = _load_android_auto(monkeypatch)
    uploader = android_auto.YouTubeUploader()

    clicked = {"value": False}

    class FakeSelector:
        def __init__(self, exists_value=False):
            self._exists_value = exists_value

        def exists(self, timeout=0):
            return self._exists_value

        def click(self, timeout=0):
            clicked["value"] = True

    class FakeDevice:
        def __call__(self, **kwargs):
            if kwargs.get("resourceId") == "com.google.android.youtube:id/upload_bottom_button":
                return FakeSelector(True)
            return FakeSelector(False)

        def dump_hierarchy(self):
            return "<hierarchy/>"

    uploader.d = FakeDevice()

    ok = uploader.click_upload_button(timeout_s=1)

    assert ok is True
    assert clicked["value"] is True


def test_wait_for_caption_input_uses_fallback_edit_text(monkeypatch):
    android_auto = _load_android_auto(monkeypatch)
    uploader = android_auto.YouTubeUploader()

    class FakeSelector:
        def __init__(self, exists_value=False):
            self._exists_value = exists_value

        def exists(self, timeout=0):
            return self._exists_value

    class FakeDevice:
        def __call__(self, **kwargs):
            if kwargs.get("className") == "android.widget.EditText" and len(kwargs) == 1:
                return FakeSelector(True)
            return FakeSelector(False)

        def dump_hierarchy(self):
            return "<hierarchy/>"

    uploader.d = FakeDevice()

    found = uploader.wait_for_caption_input(timeout_s=1)

    assert found is not None


def test_upload_short_via_ldplayer_macro_happy_path(monkeypatch):
    android_auto = _load_android_auto(monkeypatch)
    uploader = android_auto.YouTubeUploader()

    calls = []

    class FakeCaptionInput:
        def click(self):
            calls.append("caption_click")

    class FakeDevice:
        def __init__(self):
            self.shell_calls = []

        def shell(self, cmd):
            self.shell_calls.append(cmd)

    uploader.d = FakeDevice()

    monkeypatch.setattr(
        uploader,
        "extract_title_from_image_filename",
        lambda image_path: calls.append("extract") or "derived title",
    )
    monkeypatch.setattr(
        uploader,
        "prepare_device_clipboard",
        lambda title: calls.append("clipboard") or True,
    )
    monkeypatch.setattr(
        uploader,
        "get_drafts_count",
        lambda: calls.append("drafts") or 1,
    )
    monkeypatch.setattr(
        uploader,
        "push_image_to_device",
        lambda image_path, device_path: calls.append("push"),
    )
    monkeypatch.setattr(
        uploader,
        "open_youtube_and_settle",
        lambda: calls.append("open") or True,
    )
    monkeypatch.setattr(
        android_auto,
        "trigger_ldplayer_macro",
        lambda window_title, retries: calls.append("trigger"),
    )
    monkeypatch.setattr(
        uploader,
        "wait_for_macro_settle",
        lambda settle_s=8: calls.append("settle"),
    )
    monkeypatch.setattr(
        uploader,
        "wait_for_caption_input",
        lambda timeout_s=30: calls.append("wait_caption") or FakeCaptionInput(),
    )
    monkeypatch.setattr(
        uploader,
        "paste_from_clipboard_via_adb",
        lambda: calls.append("paste") or True,
    )
    monkeypatch.setattr(
        uploader,
        "click_upload_button",
        lambda timeout_s=20: calls.append("click_upload") or True,
    )
    monkeypatch.setattr(
        uploader,
        "wait_for_upload_success",
        lambda timeout_s: calls.append("wait_success") or True,
    )

    ok = uploader.upload_short_via_ldplayer_macro("C:/tmp/001_test.jpg")

    assert ok is True
    assert calls == [
        "extract",
        "drafts",
        "push",
        "open",
        "trigger",
        "settle",
        "wait_caption",
        "caption_click",
        "clipboard",
        "paste",
        "click_upload",
        "wait_success",
    ]


def test_upload_short_via_ldplayer_macro_fails_when_clipboard_prepare_fails(monkeypatch):
    android_auto = _load_android_auto(monkeypatch)
    uploader = android_auto.YouTubeUploader()

    calls = []

    class FakeCaptionInput:
        def click(self):
            return None

    class FakeDevice:
        def shell(self, cmd):
            return None

    uploader.d = FakeDevice()

    monkeypatch.setattr(
        uploader,
        "extract_title_from_image_filename",
        lambda image_path: "derived title",
    )
    monkeypatch.setattr(uploader, "get_drafts_count", lambda: None)
    monkeypatch.setattr(uploader, "push_image_to_device", lambda image_path, device_path: None)
    monkeypatch.setattr(uploader, "open_youtube_and_settle", lambda: True)
    monkeypatch.setattr(
        android_auto,
        "trigger_ldplayer_macro",
        lambda window_title, retries: calls.append("trigger"),
    )
    monkeypatch.setattr(uploader, "wait_for_macro_settle", lambda settle_s=8: None)
    monkeypatch.setattr(uploader, "wait_for_caption_input", lambda timeout_s=30: FakeCaptionInput())
    monkeypatch.setattr(
        uploader,
        "prepare_device_clipboard",
        lambda title: calls.append("clipboard") or False,
    )

    ok = uploader.upload_short_via_ldplayer_macro("C:/tmp/001_test.jpg")

    assert ok is False
    assert calls == ["trigger", "clipboard"]


def test_upload_short_via_ldplayer_macro_fails_when_upload_button_not_found(monkeypatch):
    android_auto = _load_android_auto(monkeypatch)
    uploader = android_auto.YouTubeUploader()

    class FakeCaptionInput:
        def click(self):
            return None

    class FakeDevice:
        def shell(self, cmd):
            return None

    uploader.d = FakeDevice()

    monkeypatch.setattr(uploader, "extract_title_from_image_filename", lambda image_path: "title")
    monkeypatch.setattr(uploader, "prepare_device_clipboard", lambda title: True)
    monkeypatch.setattr(uploader, "get_drafts_count", lambda: None)
    monkeypatch.setattr(uploader, "push_image_to_device", lambda image_path, device_path: None)
    monkeypatch.setattr(uploader, "open_youtube_and_settle", lambda: True)
    monkeypatch.setattr(android_auto, "trigger_ldplayer_macro", lambda window_title, retries: None)
    monkeypatch.setattr(uploader, "wait_for_macro_settle", lambda settle_s=8: None)
    monkeypatch.setattr(uploader, "wait_for_caption_input", lambda timeout_s=30: FakeCaptionInput())
    monkeypatch.setattr(uploader, "paste_from_clipboard_via_adb", lambda: True)
    monkeypatch.setattr(uploader, "click_upload_button", lambda timeout_s=20: False)

    ok = uploader.upload_short_via_ldplayer_macro("C:/tmp/001_test.jpg")

    assert ok is False


def test_upload_short_via_ldplayer_macro_fails_when_caption_not_found(monkeypatch):
    android_auto = _load_android_auto(monkeypatch)
    uploader = android_auto.YouTubeUploader()

    calls = []

    class FakeDevice:
        def shell(self, cmd):
            return None

    uploader.d = FakeDevice()

    monkeypatch.setattr(uploader, "extract_title_from_image_filename", lambda image_path: "title")
    monkeypatch.setattr(uploader, "prepare_device_clipboard", lambda title: True)
    monkeypatch.setattr(uploader, "get_drafts_count", lambda: None)
    monkeypatch.setattr(uploader, "push_image_to_device", lambda image_path, device_path: None)
    monkeypatch.setattr(uploader, "open_youtube_and_settle", lambda: True)
    monkeypatch.setattr(
        android_auto,
        "trigger_ldplayer_macro",
        lambda window_title, retries: calls.append("trigger"),
    )
    monkeypatch.setattr(uploader, "wait_for_macro_settle", lambda settle_s=8: None)
    monkeypatch.setattr(uploader, "wait_for_caption_input", lambda timeout_s=30: None)
    monkeypatch.setattr(
        uploader,
        "paste_from_clipboard_via_adb",
        lambda: calls.append("paste") or True,
    )

    ok = uploader.upload_short_via_ldplayer_macro("C:/tmp/001_test.jpg")

    assert ok is False
    assert calls == ["trigger"]
