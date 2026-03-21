import uiautomator2 as u2
import time
import random
import logging
import os

logger = logging.getLogger(__name__)

class YouTubeUploader:
    def __init__(self, serial="127.0.0.1:5555"):
        self.serial = serial
        self.d = None  # should be injected/assigned after external connect
        self.titles_cache = []
        self._load_titles()

    def _load_titles(self, titles_path="data/titles.txt"):
        try:
            with open(titles_path, 'r', encoding='utf-8') as f:
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

    def handle_popups(self):
        """Try to close common popups or ads if they appear."""
        if not self.d: return
        try:
            # Common dismissal buttons
            dismiss_texts = ['Not now', 'Dismiss', 'Close', 'Skip', 'Bỏ qua', 'Để sau', 'Đóng']
            for t in dismiss_texts:
                if self.d(textContains=t).exists(timeout=0.5):
                    logger.info(f"Closing popup by clicking: {t}")
                    self.d(textContains=t).click(timeout=1)
        except Exception as e:
            pass

    def upload_short(self, image_path: str, is_dry_run: bool = False, target_seconds: int = 5) -> bool:
        """
        Main UI flow to upload an image as a YouTube Short.
        Returns True if successful, False otherwise.
        """
        if not self.d:
            logger.error("Device not connected. Call connect() first.")
            return False

        try:
            # Transfer the image file to the android device (LDPlayer default download folder)
            filename = os.path.basename(image_path)
            device_tmp_path = f"/sdcard/Download/{filename}"
            logger.info(f"Transferring {image_path} to device at {device_tmp_path}")
            self.d.push(image_path, device_tmp_path)

            # Start YouTube app
            logger.info("Opening YouTube app...")
            # Prefer stable start without monkey for determinism; rely on healthcheck done earlier
            self.d.app_start("com.google.android.youtube")
            try:
                self.d.wait_activity(None, timeout=5)  # best effort settle
            except Exception:
                pass

            self.handle_popups()

            # Click standard Create/Add button (prefer content-desc/resource-id for en-US)
            logger.info("Clicking Create (+) button...")
            # Try common resource-id if available; otherwise content-desc contains "Create"
            create_btn = self.d(descriptionContains="Create")
            if not create_btn.exists(timeout=3):
                # Fallback to Vietnamese if UI language diverges
                create_btn = self.d(descriptionContains="Tạo")
            if create_btn.exists(timeout=5):
                create_btn.click(timeout=2)
            else:
                logger.error("Could not find Create button.")
                return False

            self.handle_popups()

            # Click Create a Short (or "Tạo video ngắn")
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
            # Pick from gallery
            logger.info("Picking image from gallery...")
            # Try multiple selectors commonly seen in YouTube Shorts UI
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
                # Fallback: in Shorts camera, bottom-left thumbnail opens gallery
                try:
                    w, h = self.d.window_size()
                    self.d.click(int(w * 0.15), int(h * 0.85))
                    clicked = True
                except Exception:
                    pass
            if not clicked:
                # Dump UI to help refine selectors on this device
                try:
                    xml = self.d.dump_hierarchy()
                    with open("ui_dump_gallery.xml", "w", encoding="utf-8") as f:
                        f.write(xml)
                    logger.error("Could not find gallery button. Dumped UI to ui_dump_gallery.xml")
                except Exception:
                    logger.error("Could not find gallery button.")
                return False

            # Select the newly pushed image (usually first item in recent)
            time.sleep(1)
            # Just click coord or the first image view
            # Try to tap the first relative image container
            logger.info("Selecting the recent image...")
            first_image = self.d(resourceId="com.android.documentsui:id/icon_thumb")
            if not first_image.exists(timeout=3):
                # Fallback to coordinate tap near top-left of grid
                w, h = self.d.window_size()
                self.d.click(int(w*0.2), int(h*0.3))
            else:
                first_image.click()

            # Click Done/Tiếp
            time.sleep(2)
            logger.info("Clicking Done/Next after selection...")
            done_btn = self.d(text="Next")
            if not done_btn.exists(timeout=1): done_btn = self.d(text="Tiep theo")
            if done_btn.exists(timeout=2): done_btn.click()

            # Click Done/Tiếp
            time.sleep(2)
            logger.info("Clicking Done/Next after selection...")
            done_btn = self.d(text="Done")
            if not done_btn.exists(timeout=1): done_btn = self.d(text="Xong")
            if done_btn.exists(timeout=2): done_btn.click()

            # Add music
            logger.info("Adding trending music...")
            music_btn = self.d(descriptionContains="Add sound")
            if not music_btn.exists(timeout=1): music_btn = self.d(textContains("Add sound"))
            if not music_btn.exists(timeout=1): music_btn = self.d(text("Sound"))
            if music_btn.exists(timeout=2):
                music_btn.click()
                time.sleep(2)
                # Just pick the first trending song
                first_song = self.d(resourceId="com.google.android.youtube:id/music_track_title")
                if not first_song.exists(timeout=2):
                    first_song = self.d(xpath="//android.widget.TextView[contains(@text,'Trending')]/../following-sibling::*[1]//android.widget.TextView[1]")
                if first_song.exists(timeout=5):
                    first_song.click()
                    # Click the arrow to confirm the song
                    confirm_btn = self.d(resourceId="com.google.android.youtube:id/confirm_button")
                    if confirm_btn.exists(timeout=2): confirm_btn.click()

            # Best-effort set duration ~target_seconds on the trim/timeline screen
            try:
                logger.info(f"Setting clip duration to ~{target_seconds}s (best-effort)...")
                # Look for a timeline/slider; try common resource-ids or class names
                timeline = self.d(resourceId="com.google.android.youtube:id/trim_timeline")
                if not timeline.exists(timeout=1):
                    timeline = self.d(className="android.widget.SeekBar")
                if timeline.exists(timeout=2):
                    # Heuristic: drag the right edge handle to approximate length
                    w, h = self.d.window_size()
                    # Drag from ~80% width to ~20% width based on desired seconds (rough heuristic)
                    # Many UIs map 15s full length; scale by target_seconds/15
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

            # Click Next/Tiếp
            next_btn = self.d(text="Next")
            if not next_btn.exists(timeout=1): next_btn = self.d(text="Tiếp")
            if next_btn.exists(timeout=3): next_btn.click()

            # Title input
            caption = self.get_random_title()
            logger.info(f"Adding caption: {caption}")
            caption_input = self.d(resourceId="com.google.android.youtube:id/caption_edit_text")
            if caption_input.exists(timeout=3):
                caption_input.set_text(caption)
            
            if is_dry_run:
                logger.info("DRY RUN: Skipping the final Upload button click.")
                return True
                
            # Click Upload Short
            logger.info("Clicking 'Upload Short'...")
            upload_btn = self.d(textContains="Upload")
            if not upload_btn.exists(timeout=1): upload_btn = self.d(textContains="Tải lên")
            if upload_btn.exists(timeout=2):
                upload_btn.click()
            else:
                logger.error("Could not find Upload button.")
                return False

            # Wait for success toast / notification or element on Library tab. Max 60s.
            logger.info("Waiting for upload to finish (up to 60s)...")
            uploaded_success = self.d(textContains="Uploaded")
            if not uploaded_success.exists(timeout=1): uploaded_success = self.d(textContains="đã tải lên")
            
            # Simple wait simulation, uiautomator2 doesn't easily capture generic toasts reliably,
            # so we look for "Uploaded" or "View" element, or just wait 15-20 seconds.
            success = False
            for _ in range(30): # 30 * 2 = 60s max
                if uploaded_success.exists(timeout=2):
                    success = True
                    break
                time.sleep(2)

            if success:
                logger.info("Upload Successful!")
                # Cleanup device file
                self.d.shell(f'rm "{device_tmp_path}"')
                return True
            else:
                logger.warning("Did not detect Upload success indicator within timeout.")
                # We return False if uncertain.
                return False

        except Exception as e:
            logger.error(f"Error during UI automation: {e}")
            return False
