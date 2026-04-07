import uiautomator2 as u2
import time
import random
import logging
import os
import re
import unicodedata

from src.ldplayer_macro import trigger_ldplayer_macro

logger = logging.getLogger(__name__)


class YouTubeUploader:
    def __init__(self, serial="127.0.0.1:5555"):
        self.serial = serial
        self.d = None  # should be injected/assigned after external connect
        self.titles_cache = []
        self._load_titles()

    def _load_titles(self, titles_path="data/titles.txt"):
        try:
            with open(titles_path, "r", encoding="utf-8") as f:
                self.titles_cache = [t.strip() for t in f.readlines() if t.strip()]
        except Exception as e:
            logger.warning(f"Could not load titles from {titles_path}: {e}")

    def connect(self):
        """Connect to device"""
        try:
            logger.info(f"Connecting to Android device/emulator at {self.serial}...")
            self.d = u2.connect(self.serial)
            logger.info("Connected successfully.")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    def get_random_title(self) -> str:
        """Returns a random title from the cache. Returns default if empty."""
        if self.titles_cache:
            return random.choice(self.titles_cache)
        return "YouTube Short!"

    def _repair_mojibake(self, text: str) -> str:
        """Best-effort fix for UTF-8 text decoded with legacy encodings."""
        markers = ["Ã", "Ð", "Ñ", "Ä", "á»", "áº", "á»¥", "â", "�", "ß", "├", "╗"]
        if not any(m in text for m in markers):
            return text

        candidates = [text]
        for source_enc in ("latin1", "cp1252"):
            try:
                candidates.append(text.encode(source_enc).decode("utf-8"))
            except Exception:
                pass

        replacements = {
            "ß╗çu": "ệu",
            "ß╗¥": "ấy",
            "ß╗ì": "ọ",
            "ß║┐": "ế",
            "ß║ú": "ả",
            "ß║Ñ": "ấ",
            "├á": "á",
            "├Á": "Á",
            "├â": "à",
            "├Â": "À",
            "├®": "ê",
            "├Ê": "Ê",
            "├ó": "í",
            "├Ó": "Í",
            "├Á": "Á",
            "├í": "ó",
            "├Í": "Ó",
            "├ú": "ú",
            "├Ú": "Ú",
        }

        def _apply_known_replacements(s: str) -> str:
            out = s
            for bad, good in sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True):
                out = out.replace(bad, good)
            return out

        candidates.append(_apply_known_replacements(text))

        def _score(s: str) -> tuple[int, int]:
            bad = s.count("�") + s.count("Ã") + s.count("Ð") + s.count("Ñ") + s.count("Ä")
            bad += s.count("ß") + s.count("├") + s.count("╗")
            good = sum(ch.isalpha() for ch in s)
            return (bad, -good)

        return min(candidates, key=_score)

    def extract_title_from_image_filename(self, image_path: str) -> str:
        """Build a clean title from image filename (without extension)."""
        name = os.path.basename(image_path)
        stem, _ = os.path.splitext(name)

        title = self._repair_mojibake(stem)
        title = unicodedata.normalize("NFKC", title)
        title = re.sub(r"^[\s\d._-]+", "", title)
        title = re.sub(r"[_\-.]+", " ", title)
        title = re.sub(r"[\r\n\t]+", " ", title)
        title = re.sub(r"\s+", " ", title).strip()

        if len(title) > 100:
            title = title[:100].rstrip()

        if not title:
            return "YouTube Short!"

        return title

    def prepare_device_clipboard(self, title: str) -> bool:
        """Set Android clipboard text for later paste."""
        if not self.d:
            return False

        try:
            set_clipboard = getattr(self.d, "set_clipboard", None)
            if callable(set_clipboard):
                set_clipboard(title)
                return True
        except Exception:
            pass

        escaped = title.replace("\\", "\\\\").replace('"', '\\"')
        escaped = escaped.replace("'", "'\"'\"'")

        cmds = [
            f"am broadcast -a clipper.set -e text '{escaped}'",
            f"cmd clipboard set text \"{escaped}\"",
        ]

        for cmd in cmds:
            try:
                self.d.shell(cmd)
                return True
            except Exception:
                continue

        return False

    def _dump_ui_debug(self, dump_path: str) -> None:
        if not self.d:
            return
        try:
            xml = self.d.dump_hierarchy()
            with open(dump_path, "w", encoding="utf-8") as f:
                f.write(xml)
            logger.warning(f"Dumped UI to {dump_path} for debugging")
        except Exception:
            pass

    def wait_for_caption_input(self, timeout_s: int = 30):
        """Wait until YouTube caption/title input appears; return element or None."""
        if not self.d:
            return None

        end = time.time() + timeout_s
        while time.time() < end:
            candidates = [
                self.d(resourceId="com.google.android.youtube:id/caption_edit_text"),
                self.d(resourceId="com.google.android.youtube:id/title_edit_text"),
                self.d(resourceId="com.google.android.youtube:id/description_edit_text"),
                self.d(className="android.widget.EditText", textContains="Tiêu đề"),
                self.d(className="android.widget.EditText", textContains="Tieu de"),
                self.d(className="android.widget.EditText", textContains="Mô tả"),
                self.d(className="android.widget.EditText", textContains="Mo ta"),
                self.d(className="android.widget.EditText", textContains="Title"),
                self.d(className="android.widget.EditText", textContains="Description"),
                self.d(className="android.widget.EditText"),
            ]

            for el in candidates:
                try:
                    if el.exists(timeout=0.2):
                        return el
                except Exception:
                    pass
            time.sleep(1)

        self._dump_ui_debug("ui_dump_caption_not_found.xml")
        return None

    def paste_from_clipboard_via_adb(self) -> bool:
        """Paste current clipboard into focused input using Android keyevent."""
        if not self.d:
            return False

        try:
            self.d.shell("input keyevent 279")
            return True
        except Exception:
            return False

    def wait_for_macro_settle(self, settle_s: int = 8) -> None:
        """Wait for LDPlayer macro to finish its scripted steps."""
        if settle_s <= 0:
            return
        logger.info(f"Waiting {settle_s}s for macro to finish before pasting title...")
        time.sleep(settle_s)

    def click_upload_button(self, timeout_s: int = 20) -> bool:
        """Tap Upload/Publish button on YouTube share screen."""
        if not self.d:
            return False

        end = time.time() + timeout_s
        while time.time() < end:
            candidates = [
                self.d(resourceId="com.google.android.youtube:id/upload_bottom_button"),
                self.d(resourceId="com.google.android.youtube:id/upload_bottom_button_container"),
                self.d(resourceId="com.google.android.youtube:id/upload_button"),
                self.d(resourceId="com.google.android.youtube:id/publish_button"),
                self.d(text="Tải video Shorts lên"),
                self.d(textContains="Shorts"),
                self.d(text="Upload"),
                self.d(text="Tải lên"),
                self.d(text="Publish"),
                self.d(text="Đăng"),
                self.d(textContains="Upload"),
                self.d(textContains="Tải lên"),
                self.d(textContains="Publish"),
                self.d(textContains="Đăng"),
                self.d(descriptionContains="Upload"),
                self.d(descriptionContains="Tải lên"),
                self.d(descriptionContains="Publish"),
                self.d(descriptionContains="Đăng"),
            ]

            for el in candidates:
                try:
                    if el.exists(timeout=0.3):
                        el.click(timeout=1)
                        return True
                except Exception:
                    pass

            time.sleep(1)

        self._dump_ui_debug("ui_dump_upload_button_not_found.xml")
        return False

    def handle_popups(self):
        """Try to close common popups or ads if they appear."""
        if not self.d:
            return
        try:
            dismiss_texts = ["Not now", "Dismiss", "Close", "Skip", "Bỏ qua", "Để sau", "Đóng"]
            for t in dismiss_texts:
                if self.d(textContains=t).exists(timeout=0.5):
                    logger.info(f"Closing popup by clicking: {t}")
                    self.d(textContains=t).click(timeout=1)
        except Exception:
            pass

    def open_youtube_and_settle(self) -> bool:
        if not self.d:
            logger.error("Device not connected. Call connect() first.")
            return False

        try:
            logger.info("Opening YouTube app...")
            self.d.app_start("com.google.android.youtube")
            try:
                self.d.wait_activity(None, timeout=5)  # best effort settle
            except Exception:
                pass

            self.handle_popups()
            return True
        except Exception as e:
            logger.error(f"Failed to open YouTube: {e}")
            return False

    def push_image_to_device(self, image_path: str, device_path: str) -> None:
        if not self.d:
            raise RuntimeError("Device not connected")

        # Ensure clean path
        try:
            self.d.shell(f'rm "{device_path}"')
        except Exception:
            pass

        logger.info(f"Transferring {image_path} to device at {device_path}")
        self.d.push(image_path, device_path)

        # Best-effort: verify the file exists and nudge MediaStore so picker can see it
        try:
            ls = self.d.shell(f'ls -l "{device_path}"')
            logger.info(f"Device file check: {ls}")
        except Exception:
            pass

        try:
            # Some ROMs only show new files in picker after a media scan
            self.d.shell(
                'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE '
                f'-d file://{device_path}'
            )
        except Exception:
            pass

    def _tap_bottom_nav_you(self) -> bool:
        """Best-effort: open the You/Library tab from YouTube bottom nav."""
        if not self.d:
            return False

        candidates = [
            # Newer YouTube bottom nav
            self.d(descriptionContains="You"),
            self.d(descriptionContains="Bạn"),
            self.d(text="You"),
            self.d(text="Bạn"),
            # Older YouTube bottom nav
            self.d(descriptionContains="Library"),
            self.d(descriptionContains="Thư viện"),
            self.d(text="Library"),
            self.d(text="Thư viện"),
        ]

        for el in candidates:
            try:
                if el.exists(timeout=1):
                    el.click(timeout=1)
                    time.sleep(1)
                    return True
            except Exception:
                pass

        return False

    def _navigate_to_drafts(self) -> bool:
        """Best-effort navigation to YouTube Drafts screen."""
        if not self.d:
            return False

        if not self._tap_bottom_nav_you():
            return False

        # Enter "Your videos" (varies across locales/versions)
        your_videos_candidates = [
            self.d(textContains="Your videos"),
            self.d(textContains="Video của bạn"),
            self.d(textContains="Video của Bạn"),
            self.d(descriptionContains="Your videos"),
            self.d(descriptionContains="Video của bạn"),
        ]
        for el in your_videos_candidates:
            try:
                if el.exists(timeout=1):
                    el.click(timeout=1)
                    time.sleep(1)
                    break
            except Exception:
                pass

        # Select Drafts tab/section
        drafts_candidates = [
            self.d(textContains="Draft"),
            self.d(textContains="Bản nháp"),
            self.d(textContains="Nháp"),
            self.d(descriptionContains="Draft"),
            self.d(descriptionContains="Bản nháp"),
            self.d(descriptionContains="Nháp"),
        ]
        for el in drafts_candidates:
            try:
                if el.exists(timeout=1):
                    el.click(timeout=1)
                    time.sleep(1)
                    return True
            except Exception:
                pass

        return False

    def _count_visible_draft_labels(self) -> int | None:
        """Return a best-effort count of draft labels on the current screen."""
        if not self.d:
            return None

        try:
            # xpath() returns UI objects; .all() gives list
            nodes = self.d.xpath(
                "//*[contains(@text, 'Draft') or contains(@text, 'Bản nháp') or contains(@text, 'Nháp')]"
            ).all()
            if not nodes:
                return 0
            return len(nodes)
        except Exception:
            return None

    def get_drafts_count(self) -> int | None:
        """Navigate to Drafts and count visible draft labels (best-effort)."""
        if not self.d:
            return None

        if not self._navigate_to_drafts():
            return None

        return self._count_visible_draft_labels()

    def wait_for_upload_success(self, timeout_s: int) -> bool:
        if not self.d:
            return False

        logger.info(f"Waiting for upload to finish (up to {timeout_s}s)...")

        # Try multiple likely success indicators (text-based; best-effort)
        indicators = [
            # Published/uploaded flows
            self.d(textContains="Uploaded"),
            self.d(textContains="Video uploaded"),
            self.d(textContains="Upload complete"),
            self.d(textContains="View"),
            self.d(textContains="đã tải lên"),
            self.d(textContains="Đã tải lên"),
            self.d(textContains="Đã đăng"),
            self.d(textContains="Đã xuất bản"),
            # Draft flows (sometimes toast/snackbar; may or may not appear in hierarchy)
            self.d(textContains="Draft"),
            self.d(textContains="Bản nháp"),
            self.d(textContains="Nháp"),
            self.d(textContains="saved"),
            self.d(textContains="Đã lưu"),
        ]

        end = time.time() + timeout_s
        while time.time() < end:
            for el in indicators:
                try:
                    if el.exists(timeout=0.2):
                        return True
                except Exception:
                    pass
            time.sleep(2)

        # On timeout: dump hierarchy for debugging
        self._dump_ui_debug("ui_dump_upload_timeout.xml")

        return False

    def upload_short_via_ldplayer_macro(
        self,
        image_path: str,
        window_title: str = "LDPlayer",
        macro_timeout_s: int = 180,
        macro_settle_s: int = 8,
    ) -> bool:
        """Upload using LDPlayer macro triggered by Ctrl+F5.

        Handoff:
        - uiautomator2 opens YouTube to a stable state
        - image is pushed to /sdcard/Download/auto_upload_latest.jpg
        - LDPlayer macro starts at Create (+) and selects the most recent image

        Success criteria:
        - Prefer explicit "uploaded/published" indicators.
        - If those aren't detected, fall back to a Drafts-count check.
        """

        if not self.d:
            logger.error("Device not connected. Call connect() first.")
            return False

        device_path = "/sdcard/Download/auto_upload_latest.jpg"

        try:
            title = self.extract_title_from_image_filename(image_path)
            logger.info(f"Derived title from filename: {title}")

            # Baseline Drafts count before starting (best-effort)
            before_drafts = self.get_drafts_count()
            if before_drafts is not None:
                logger.info(f"Drafts baseline count: {before_drafts}")

            self.push_image_to_device(image_path, device_path)

            if not self.open_youtube_and_settle():
                return False

            logger.info("Triggering LDPlayer macro (Ctrl+F5)...")
            trigger_ldplayer_macro(window_title=window_title, retries=3)
            self.wait_for_macro_settle(settle_s=macro_settle_s)

            caption_input = self.wait_for_caption_input(timeout_s=30)
            if not caption_input:
                logger.error("Caption input not found after macro trigger.")
                return False

            try:
                caption_input.click()
            except Exception:
                pass

            if not self.prepare_device_clipboard(title):
                logger.error("Failed to prepare device clipboard for title paste.")
                return False

            if not self.paste_from_clipboard_via_adb():
                logger.error("Failed to paste title from clipboard via ADB.")
                return False

            if not self.click_upload_button(timeout_s=20):
                logger.error("Could not find Upload button after title paste.")
                return False

            success = self.wait_for_upload_success(timeout_s=macro_timeout_s)
            if success:
                logger.info("Upload Successful!")
                try:
                    self.d.shell(f'rm "{device_path}"')
                except Exception:
                    pass
                return True

            # Fallback: Drafts check
            logger.info("No explicit success indicator detected; verifying via Drafts list...")
            after_drafts = self.get_drafts_count()
            if before_drafts is not None and after_drafts is not None:
                logger.info(f"Drafts count: before={before_drafts}, after={after_drafts}")
                if after_drafts > before_drafts:
                    logger.info("Detected new Draft; treating as success.")
                    try:
                        self.d.shell(f'rm "{device_path}"')
                    except Exception:
                        pass
                    return True

            logger.warning("Did not detect Upload success indicator within timeout.")
            return False
        except Exception as e:
            logger.error(f"Error during macro upload: {e}")
            return False

    def upload_short(self, image_path: str, is_dry_run: bool = False, target_seconds: int = 5) -> bool:
        """Existing full uiautomator2 flow (legacy backend)."""

        if not self.d:
            logger.error("Device not connected. Call connect() first.")
            return False

        try:
            filename = os.path.basename(image_path)
            device_tmp_path = f"/sdcard/Download/{filename}"
            logger.info(f"Transferring {image_path} to device at {device_tmp_path}")
            self.d.push(image_path, device_tmp_path)

            if not self.open_youtube_and_settle():
                return False

            logger.info("Clicking Create (+) button...")
            create_btn = self.d(descriptionContains="Create")
            if not create_btn.exists(timeout=3):
                create_btn = self.d(descriptionContains="Tạo")
            if create_btn.exists(timeout=5):
                create_btn.click(timeout=2)
            else:
                logger.error("Could not find Create button.")
                return False

            self.handle_popups()

            logger.info("Clicking 'Create a Short'...")
            short_btn = self.d(textContains="Short")
            if short_btn.exists(timeout=3):
                short_btn.click()
            else:
                short_btn = self.d(descriptionContains="Short")
                if short_btn.exists(timeout=2):
                    short_btn.click()
                else:
                    logger.error("Could not find 'Create a Short' button.")
                    return False

            time.sleep(2)
            logger.info("Picking image from gallery...")
            candidates = [
                self.d(resourceId="com.google.android.youtube:id/gallery_button"),
                self.d(resourceId="com.google.android.youtube:id/shorts_gallery_button"),
                self.d(descriptionContains="Gallery"),
                self.d(textContains="Gallery"),
                self.d(descriptionContains="Import"),
                self.d(textContains="Import"),
            ]
            clicked = False
            for el in candidates:
                if el.exists(timeout=2):
                    el.click()
                    clicked = True
                    break
            if not clicked:
                try:
                    w, h = self.d.window_size()
                    self.d.click(int(w * 0.15), int(h * 0.85))
                    clicked = True
                except Exception:
                    pass
            if not clicked:
                try:
                    xml = self.d.dump_hierarchy()
                    with open("ui_dump_gallery.xml", "w", encoding="utf-8") as f:
                        f.write(xml)
                    logger.error("Could not find gallery button. Dumped UI to ui_dump_gallery.xml")
                except Exception:
                    logger.error("Could not find gallery button.")
                return False

            time.sleep(1)
            logger.info("Selecting the recent image...")
            first_image = self.d(resourceId="com.android.documentsui:id/icon_thumb")
            if not first_image.exists(timeout=3):
                w, h = self.d.window_size()
                self.d.click(int(w * 0.2), int(h * 0.3))
            else:
                first_image.click()

            time.sleep(2)
            logger.info("Clicking Done/Next after selection...")
            done_btn = self.d(text="Next")
            if not done_btn.exists(timeout=1):
                done_btn = self.d(text="Tiep theo")
            if done_btn.exists(timeout=2):
                done_btn.click()

            time.sleep(2)
            logger.info("Clicking Done/Next after selection...")
            done_btn = self.d(text="Done")
            if not done_btn.exists(timeout=1):
                done_btn = self.d(text="Xong")
            if done_btn.exists(timeout=2):
                done_btn.click()

            logger.info("Adding trending music...")
            music_btn = self.d(descriptionContains="Add sound")
            if not music_btn.exists(timeout=1):
                music_btn = self.d(textContains("Add sound"))
            if not music_btn.exists(timeout=1):
                music_btn = self.d(text("Sound"))
            if music_btn.exists(timeout=2):
                music_btn.click()
                time.sleep(2)
                first_song = self.d(resourceId="com.google.android.youtube:id/music_track_title")
                if not first_song.exists(timeout=2):
                    first_song = self.d(
                        xpath="//android.widget.TextView[contains(@text,'Trending')]/../following-sibling::*[1]//android.widget.TextView[1]"
                    )
                if first_song.exists(timeout=5):
                    first_song.click()
                    confirm_btn = self.d(resourceId="com.google.android.youtube:id/confirm_button")
                    if confirm_btn.exists(timeout=2):
                        confirm_btn.click()

            try:
                logger.info(f"Setting clip duration to ~{target_seconds}s (best-effort)...")
                timeline = self.d(resourceId="com.google.android.youtube:id/trim_timeline")
                if not timeline.exists(timeout=1):
                    timeline = self.d(className="android.widget.SeekBar")
                if timeline.exists(timeout=2):
                    w, h = self.d.window_size()
                    full = 0.8
                    frac = max(0.1, min(1.0, target_seconds / 15.0))
                    start_x = int(w * (0.2 + full * frac))
                    end_x = int(w * 0.2)
                    y = int(h * 0.6)
                    self.d.drag(start_x, y, end_x, y, 0.2)
                else:
                    logger.info("No timeline/slider found; skipping duration adjustment.")
            except Exception as e:
                logger.warning(f"Duration adjust skipped due to error: {e}")

            next_btn = self.d(text="Next")
            if not next_btn.exists(timeout=1):
                next_btn = self.d(text="Tiếp")
            if next_btn.exists(timeout=3):
                next_btn.click()

            caption = self.get_random_title()
            logger.info(f"Adding caption: {caption}")
            caption_input = self.d(resourceId="com.google.android.youtube:id/caption_edit_text")
            if caption_input.exists(timeout=3):
                caption_input.set_text(caption)

            if is_dry_run:
                logger.info("DRY RUN: Skipping the final Upload button click.")
                return True

            logger.info("Clicking 'Upload Short'...")
            upload_btn = self.d(textContains="Upload")
            if not upload_btn.exists(timeout=1):
                upload_btn = self.d(textContains="Tải lên")
            if upload_btn.exists(timeout=2):
                upload_btn.click()
            else:
                logger.error("Could not find Upload button.")
                return False

            success = self.wait_for_upload_success(timeout_s=60)
            if success:
                logger.info("Upload Successful!")
                self.d.shell(f'rm "{device_tmp_path}"')
                return True

            logger.warning("Did not detect Upload success indicator within timeout.")
            return False

        except Exception as e:
            logger.error(f"Error during UI automation: {e}")
            return False
