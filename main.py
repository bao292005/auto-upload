import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv

# Ensure stdout/stderr can print Unicode paths/filenames on Windows consoles
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Also nudge Python runtime to prefer UTF-8 for subprocesses/IO
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from src.drive_sync import download_and_filter
from src.db_manager import DBManager
from src.android_auto import YouTubeUploader
from src.device import connect_device

class _Utf8ConsoleHandler(logging.StreamHandler):
    """Console handler that never crashes on Unicode on Windows.

    Some Windows consoles (and some Anaconda setups) default to legacy encodings
    like cp1252, which can raise UnicodeEncodeError when writing Vietnamese paths.
    This handler always encodes to UTF-8 and writes bytes directly.
    """

    def emit(self, record):  # type: ignore[override]
        try:
            import os

            msg = self.format(record)
            data = (msg + self.terminator).encode("utf-8", errors="replace")

            stream = self.stream
            try:
                fd = stream.fileno()
                os.write(fd, data)
            except Exception:
                # Fallback: try buffer
                if hasattr(stream, "buffer"):
                    stream.buffer.write(data)
                    stream.flush()
                else:
                    # Last resort: decode to str and write
                    stream.write(data.decode("utf-8", errors="replace"))
                    stream.flush()
        except Exception:
            self.handleError(record)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("auto_upload.log", encoding="utf-8"),
        _Utf8ConsoleHandler(sys.stdout),
    ],
    force=True,
)
logger = logging.getLogger(__name__)


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    v = value.strip().lower()
    if v in {"true", "1", "yes", "y"}:
        return True
    if v in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _parse_pos_int(value: Optional[str], default: int) -> int:
    if value is None or value.strip() == "":
        return default
    try:
        n = int(value)
    except Exception as e:
        raise ValueError(f"Invalid int value: {value}") from e
    if n <= 0:
        raise ValueError(f"Expected positive int, got: {value}")
    return n


def main() -> None:
    # Load .env without overriding existing OS env vars
    load_dotenv(override=False)

    logger.info("Starting Auto Upload Shorts (env-only mode)")
    logger.info("Loading configuration from ENV/.env")

    drive_url = os.getenv("DRIVE_URL")
    local_dir = os.getenv("LOCAL_DIR")

    adb_serial = os.getenv("ADB_SERIAL")
    if not adb_serial:
        logger.error("Missing ADB_SERIAL env var")
        sys.exit(1)

    try:
        max_files = _parse_pos_int(os.getenv("MAX_FILES"), default=5)
        target_seconds = _parse_pos_int(os.getenv("TARGET_SECONDS"), default=5)
        dry_run = _parse_bool(os.getenv("DRY_RUN"), default=False)
        ld_macro_timeout = _parse_pos_int(os.getenv("LD_MACRO_TIMEOUT"), default=180)
        ld_macro_settle_seconds = _parse_pos_int(os.getenv("LD_MACRO_SETTLE_SECONDS"), default=8)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    upload_backend = (os.getenv("UPLOAD_BACKEND") or "ld-macro").strip().lower()
    if upload_backend not in {"uiauto", "ld-macro"}:
        logger.error("UPLOAD_BACKEND must be one of: uiauto, ld-macro")
        sys.exit(1)

    ld_window_title = os.getenv("LD_WINDOW_TITLE") or "LDPlayer"

    if not drive_url and not local_dir:
        logger.error("Please provide DRIVE_URL or LOCAL_DIR")
        sys.exit(1)

    if upload_backend == "ld-macro" and dry_run:
        logger.error("DRY_RUN is not supported when UPLOAD_BACKEND=ld-macro")
        sys.exit(1)

    # Preflight: ensure LDPlayer window is available for macro backend
    if upload_backend == "ld-macro":
        try:
            from src.ldplayer_macro import focus_ldplayer_window

            focus_ldplayer_window(ld_window_title)
        except Exception as e:
            logger.error(f"LDPlayer window is not ready/focusable (title='{ld_window_title}'): {e}")
            logger.error("Please open LDPlayer (and keep its window visible) before running.")
            sys.exit(1)

    # Init DB
    db = DBManager()

    # Connect device
    try:
        d = connect_device(adb_serial)
    except Exception as e:
        logger.error(f"Could not connect to Android device/emulator: {e}")
        sys.exit(1)

    uploader = YouTubeUploader(serial=adb_serial)
    uploader.d = d

    # Phase 1: Collect images
    temp_dir = "./temp"
    valid_images: list[str] = []

    if local_dir:
        try:
            from src.local_scan import scan_local_images

            valid_images = scan_local_images(local_dir, max_files=max_files)
            logger.info(f"Loaded {len(valid_images)} images from local dir: {local_dir}")
        except Exception as e:
            logger.error(f"Failed to scan local dir {local_dir}: {e}")
            sys.exit(1)
    else:
        valid_images = download_and_filter(drive_url, temp_dir, max_files=max_files)  # type: ignore[arg-type]

    if not valid_images:
        logger.info("No valid images found. Exiting.")
        sys.exit(0)

    # Phase 2: Iterate & Upload
    success_count = 0
    skipped_count = 0
    failed_count = 0

    for img_path in valid_images:
        img_hash = db.get_file_hash(img_path)

        if not img_hash:
            logger.warning(f"Could not hash {img_path}, skipping.")
            failed_count += 1
            continue

        if db.is_uploaded(img_hash):
            logger.info(
                f"Skipping already uploaded image (hash: {img_hash[:8]}...): {os.path.basename(img_path)}"
            )
            skipped_count += 1
            try:
                os.remove(img_path)
            except Exception:
                pass
            continue

        logger.info(f"Processing new image: {os.path.basename(img_path)}")

        if upload_backend == "ld-macro":
            upload_success = uploader.upload_short_via_ldplayer_macro(
                img_path,
                window_title=ld_window_title,
                macro_timeout_s=ld_macro_timeout,
                macro_settle_s=ld_macro_settle_seconds,
            )
        else:
            upload_success = uploader.upload_short(
                img_path,
                is_dry_run=dry_run,
                target_seconds=target_seconds,
            )

        if upload_success:
            if not dry_run:
                db.mark_success(img_hash)
            success_count += 1
            try:
                os.remove(img_path)
                logger.info(f"Cleaned up local file: {os.path.basename(img_path)}")
            except Exception as e:
                logger.warning(f"Failed to delete {img_path}: {e}")
        else:
            logger.error(f"Failed to upload {os.path.basename(img_path)}")
            failed_count += 1

    logger.info("====================================")
    logger.info("Auto Upload Process Completed")
    logger.info(f"Total processed: {len(valid_images)}")
    logger.info(f"Success: {success_count}, Skipped (duplicate): {skipped_count}, Failed: {failed_count}")
    logger.info("====================================")


if __name__ == "__main__":
    main()
