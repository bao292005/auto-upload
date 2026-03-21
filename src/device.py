import logging
import subprocess
import time
from typing import Optional

import uiautomator2 as u2

logger = logging.getLogger(__name__)


def _autodiscover_single() -> Optional[str]:
    """Return the single ADB device serial if exactly one device is connected; otherwise None."""
    try:
        proc = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=False)
        lines = proc.stdout.splitlines()
        # Skip header line "List of devices attached"
        entries = [l for l in lines[1:] if "\tdevice" in l]
        serials = [e.split("\t")[0].strip() for e in entries if e.strip()]
        if len(serials) == 1:
            return serials[0]
        return None
    except Exception as e:
        logger.warning(f"ADB autodiscovery failed: {e}")
        return None


def connect_device(serial: Optional[str] = None, retries: int = 3, backoff: float = 2.0):
    """
    Connect to an Android device/emulator using uiautomator2.
    - If `serial` is None, attempt autodiscovery when exactly one device is present.
    - Perform healthcheck after connect.
    - Retry with exponential backoff.

    Returns: u2.Device
    Raises: last exception on failure
    """
    eff_serial = serial or _autodiscover_single()
    if not eff_serial:
        raise RuntimeError(
            "No ADB device selected or multiple devices present. Provide --adb-serial or set ADB_SERIAL."
        )

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Connecting to Android device/emulator at {eff_serial} (attempt {attempt}/{retries})…")
            d = u2.connect(eff_serial)
            # Ensure atx-agent is ready and basic services are healthy (if available)
            try:
                if hasattr(d, "healthcheck"):
                    d.healthcheck()
                    logger.info("Device healthcheck OK.")
                else:
                    # Fallback: access a lightweight property to validate JSON-RPC
                    _ = d.info
                    logger.warning("uiautomator2.healthcheck() not available; proceeded after info() ping.")
            except Exception as ping_err:
                logger.warning(f"Healthcheck/info ping failed: {ping_err}")
                raise
            return d
        except Exception as e:
            last_err = e
            logger.warning(f"Connect/healthcheck failed: {e}")
            if attempt < retries:
                time.sleep(backoff * attempt)
    # Out of retries
    raise last_err if last_err else RuntimeError("Unknown error connecting to device")
