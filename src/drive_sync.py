import os
import gdown
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def download_and_filter(drive_url: str, temp_dir: str, max_files: Optional[int] = None) -> List[str]:
    """
    Downloads file from a Google Drive folder URL to temp_dir,
    and returns a list of absolute paths to valid images (png, jpg, jpeg).
    Deletes non-image files.
    """
    os.makedirs(temp_dir, exist_ok=True)
    
    logger.info(f"Downloading from Google Drive folder: {drive_url}")
    try:
        # Download folder
        # gdown.download_folder requires the sharing link of a folder
        # Some gdown versions error if folder has >50 files. Try with remaining_ok=True if available.
        try:
            res = gdown.download_folder(url=drive_url, output=temp_dir, quiet=False, use_cookies=False, remaining_ok=True)  # type: ignore
        except TypeError:
            # Fallback for older gdown without remaining_ok
            res = gdown.download_folder(url=drive_url, output=temp_dir, quiet=False, use_cookies=False)
        if not res:
            logger.error("Failed to download folder from Google Drive (possibly >50 files). Consider splitting into subfolders ≤50 items or update gdown.")
            return []
            
        valid_extensions = {'.png', '.jpg', '.jpeg'}
        valid_images = []

        # Some gdown versions may return nested structure; traverse output dir for images
        if isinstance(res, list) and res:
            candidates = res
        else:
            candidates = []
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    candidates.append(os.path.join(root, f))

        for file in candidates:
            ext = os.path.splitext(file)[1].lower()
            if ext in valid_extensions:
                valid_images.append(os.path.abspath(file))
            else:
                logger.info(f"Removing invalid file: {file}")
                try:
                    if os.path.isfile(file):
                        os.remove(file)
                except Exception as e:
                    logger.warning(f"Could not delete garbage file {file}: {e}")

        # Deterministic sort then apply optional limit
        valid_images.sort()
        if max_files is not None and max_files > 0:
            valid_images = valid_images[:max_files]
        logger.info(f"Successfully prepared {len(valid_images)} valid images from Google Drive (max_files={max_files}).")
        return valid_images
        
    except Exception as e:
        logger.error(f"Error during drive sync: {e}")
        return []
