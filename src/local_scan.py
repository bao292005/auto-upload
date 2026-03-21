import os
from typing import List

VALID_EXTS = {".png", ".jpg", ".jpeg"}

def scan_local_images(directory: str, max_files: int | None = None) -> List[str]:
    imgs: List[str] = []
    for root, _, files in os.walk(directory):
        for f in files:
            if os.path.splitext(f)[1].lower() in VALID_EXTS:
                imgs.append(os.path.abspath(os.path.join(root, f)))
    imgs.sort()
    if max_files and max_files > 0:
        imgs = imgs[:max_files]
    return imgs
