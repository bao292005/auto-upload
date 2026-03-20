import os
import pytest
from src.db_manager import DBManager

def test_db_manager_init(tmp_path):
    db_path = tmp_path / "test_history.sqlite"
    db = DBManager(str(db_path))
    assert os.path.exists(db_path)
    db.close()

def test_hash_file(tmp_path):
    test_file = tmp_path / "test.png"
    test_file.write_bytes(b"hello world")
    
    file_hash = DBManager.get_file_hash(str(test_file))
    assert file_hash == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

def test_upload_tracking(tmp_path):
    db_path = tmp_path / "test_history.sqlite"
    db = DBManager(str(db_path))
    
    test_hash = "fakehash123"
    assert not db.is_uploaded(test_hash)
    
    db.mark_success(test_hash)
    assert db.is_uploaded(test_hash)
    
    db.close()
