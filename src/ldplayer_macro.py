import logging
import platform
import re
import time

logger = logging.getLogger(__name__)


class LDPlayerWindowNotFound(RuntimeError):
    pass


class LDPlayerFocusError(RuntimeError):
    pass


def _require_windows() -> None:
    if platform.system().lower() != "windows":
        raise RuntimeError("LDPlayer macro hotkey trigger is supported on Windows only")


def _force_foreground(hwnd: int) -> None:
    """Best-effort force window to foreground using Win32 APIs."""

    _require_windows()

    import ctypes

    user32 = ctypes.windll.user32

    # 9 = SW_RESTORE
    try:
        user32.ShowWindow(hwnd, 9)
    except Exception:
        pass

    try:
        user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def _get_root_hwnd(hwnd: int) -> int:
    """Return the top-level ancestor (GA_ROOT) for a window handle."""

    _require_windows()

    import ctypes

    user32 = ctypes.windll.user32

    if not hwnd:
        return 0

    # GA_ROOT = 2
    try:
        root = int(user32.GetAncestor(int(hwnd), 2))
        return root or int(hwnd)
    except Exception:
        return int(hwnd)


def _get_foreground_hwnd() -> int:
    _require_windows()

    import ctypes

    user32 = ctypes.windll.user32
    hwnd = int(user32.GetForegroundWindow())
    return _get_root_hwnd(hwnd)


def focus_ldplayer_window(window_title: str) -> int:
    """Bring LDPlayer window to foreground and focus it.

    Returns:
        int: root window handle

    Uses pywinauto to locate a top-level window whose title matches window_title.

    Raises:
        LDPlayerWindowNotFound: if no window is found
        LDPlayerFocusError: if focus cannot be set
    """

    _require_windows()

    try:
        from pywinauto import Desktop  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"pywinauto is required for LDPlayer hotkey triggering: {e}")

    # win32 backend is typically more reliable/faster for top-level window focus than UIA
    desktop = Desktop(backend="win32")

    try:
        # Try exact title first, then fallback to substring match.
        win = desktop.window(title=window_title)
        if not win.exists(timeout=1):
            win = desktop.window(title_re=f".*{re.escape(window_title)}.*")
        if not win.exists(timeout=2):
            raise LDPlayerWindowNotFound(
                f"LDPlayer window not found (title or contains): {window_title}"
            )

        # Best-effort restore/bring front.
        try:
            win.restore()
        except Exception:
            pass

        try:
            win.set_focus()
        except Exception as e:
            raise LDPlayerFocusError(f"Failed to focus LDPlayer window '{window_title}': {e}")

        # Extra best-effort: call Win32 SetForegroundWindow
        try:
            _force_foreground(int(win.handle))
        except Exception:
            pass

        # Give Windows a moment to apply foreground.
        time.sleep(0.1)

        return _get_root_hwnd(int(win.handle))
    except (LDPlayerWindowNotFound, LDPlayerFocusError):
        raise
    except Exception as e:
        raise LDPlayerFocusError(f"Unexpected error focusing LDPlayer window '{window_title}': {e}")


def _get_hwnd_title(hwnd: int) -> str:
    _require_windows()

    import ctypes

    user32 = ctypes.windll.user32
    buf = ctypes.create_unicode_buffer(512)
    try:
        user32.GetWindowTextW(int(hwnd), buf, 512)
        return buf.value or ""
    except Exception:
        return ""


def _is_foreground_window(win_handle: int, expected_title: str | None = None) -> bool:
    """Check if given window is foreground.

    On Windows, foreground handle can be tricky (child vs root windows, focus lock).
    If expected_title is provided, we accept a title match as a fallback to avoid
    false negatives when the handle comparison is unreliable.
    """

    try:
        fg = _get_foreground_hwnd()
        if fg == 0:
            return False

        win_root = _get_root_hwnd(int(win_handle))
        if win_root == fg:
            return True

        if expected_title:
            fg_title = _get_hwnd_title(fg)
            if expected_title in fg_title:
                logger.info(
                    f"Foreground title matched '{expected_title}' (fg='{fg_title}'); proceeding despite handle mismatch"
                )
                return True

        return False
    except Exception:
        return False


def send_hotkey_ctrl_f5() -> None:
    """Send Ctrl+F5 to the active window."""

    _require_windows()

    try:
        from pywinauto.keyboard import send_keys  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"pywinauto is required for LDPlayer hotkey triggering: {e}")

    # pywinauto send_keys syntax: ^ = Ctrl, and function keys use {F5}
    send_keys("^{F5}")


def trigger_ldplayer_macro(
    window_title: str = "LDPlayer",
    retries: int = 3,
    focus_backoff_s: float = 0.2,
) -> None:
    """Focus LDPlayer window and send Ctrl+F5.

    Verifies foreground is LDPlayer, retries focus+send up to `retries`.
    """

    if retries < 1:
        raise ValueError("retries must be >= 1")

    last_err: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Focusing LDPlayer window (title='{window_title}') attempt {attempt}/{retries}")
            handle = focus_ldplayer_window(window_title)

            if not _is_foreground_window(handle, expected_title=window_title):
                raise LDPlayerFocusError(
                    f"LDPlayer window '{window_title}' is not the active foreground window after focus"
                )

            logger.info("Sending hotkey Ctrl+F5 to LDPlayer")
            send_hotkey_ctrl_f5()
            return
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(focus_backoff_s * attempt)

    raise RuntimeError(f"Failed to trigger LDPlayer macro after {retries} attempts: {last_err}")
