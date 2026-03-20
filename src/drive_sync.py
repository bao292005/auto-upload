import os
import gdown
import logging
from typing import List

logger = logging.getLogger(__name__)

def download_and_filter(drive_url: str, temp_dir: str) -> List[str]:
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
        res = gdown.download_folder(url=drive_url, output=temp_dir, quiet=False, use_cookies=False)
        if not res:
            logger.error("Failed to download folder from Google Drive.")
            return []
            
        valid_extensions = {'.png', '.jpg', '.jpeg'}
        valid_images = []
        
        for file in res:
            ext = os.path.splitext(file)[1].lower()
            if ext in valid_extensions:
                valid_images.append(os.path.abspath(file))
            else:
                logger.info(f"Removing invalid file: {file}")
                # Remove non-image files downloaded inside temp directory structure
                try:
                    if os.path.isfile(file):
                        os.remove(file)
                except Exception as e:
                    logger.warning(f"Could not delete garbage file {file}: {e}")
                    
        logger.info(f"Successfully downloaded {len(valid_images)} valid images from Google Drive.")
        return valid_images
        
    except Exception as e:
        logger.error(f"Error during drive sync: {e}")
        return []
