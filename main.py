import argparse
import logging
import os
import sys

from src.drive_sync import download_and_filter
from src.db_manager import DBManager
from src.android_auto import YouTubeUploader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auto_upload.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Auto Upload Shorts qua LDPlayer MVP")
    parser.add_argument(
        "--drive-url", 
        type=str, 
        required=True, 
        help="Shareable link of the Google Drive folder containing images"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Run without clicking the upload button on YouTube"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger.info("Starting Auto Upload Shorts CLI")
    if args.dry_run:
        logger.info("Mode: DRY-RUN (Will not tap final Upload button)")

    temp_dir = "./temp"
    
    # Init DB
    db = DBManager()
    
    # Init UI Automator
    uploader = YouTubeUploader(serial="localhost:5555")
    try:
        uploader.connect()
    except Exception as e:
        logger.error("Could not connect to LDPlayer device. Stop.")
        sys.exit(1)
        
    # Phase 1: Download & Filter
    valid_images = download_and_filter(args.drive_url, temp_dir)
    
    if not valid_images:
        logger.info("No valid images found or failed to download. Exiting.")
        sys.exit(0)
        
    # Phase 2: Iterate & Upload
    success_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    
    for img_path in valid_images:
        img_hash = db.get_file_hash(img_path)
        
        if not img_hash:
            logger.warning(f"Could not hash {img_path}, skipping.")
            failed_count += 1
            continue
            
        if db.is_uploaded(img_hash):
            logger.info(f"Skipping already uploaded image (hash: {img_hash[:8]}...): {os.path.basename(img_path)}")
            skipped_count += 1
            
            # GC: delete file since already uploaded
            try:
                os.remove(img_path)
            except Exception:
                pass
            continue
            
        logger.info(f"Processing new image: {os.path.basename(img_path)}")
        
        # Upload
        upload_success = uploader.upload_short(img_path, is_dry_run=args.dry_run)
        
        if upload_success:
            if not args.dry_run:
                # Mark it done
                db.mark_success(img_hash)
            success_count += 1
            # Garbage collection: drop the local file upon success
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
