# -*- coding: utf-8 -*-
"""
Verification script for CL1 SQLite-based secure storage.
Tests encryption, anti-tamper, and multi-instance isolation.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from module.statistics.cl1_database import Cl1Database
from module.logger import logger

def test_secure_storage():
    logger.hr("Starting CL1 Secure Storage Verification")
    
    # 1. Setup temporary DB
    test_db_path = Path("cl1_test.db")
    if test_db_path.exists():
        test_db_path.unlink()
    
    db = Cl1Database(db_path=test_db_path)
    instance1 = "test_instance_1"
    instance2 = "test_instance_2"
    month = "2026-02"
    
    # 2. Test Write and Read (Instance 1)
    logger.info("Testing Instance 1 data...")
    db.increment_battle_count(instance1)
    db.add_akashi_ap_entry(instance1, amount=120, base=60, count=2, source='akashi')
    
    stats1 = db.get_stats(instance1, month)
    assert stats1['battle_count'] == 1
    assert stats1['akashi_ap'] == 120
    assert len(stats1['akashi_ap_entries']) == 1
    logger.info("✓ Instance 1 Write/Read Passed")
    
    # 3. Test Multi-instance Isolation (Instance 2)
    logger.info("Testing Instance 2 isolation...")
    db.increment_battle_count(instance2)
    stats2 = db.get_stats(instance2, month)
    stats1_again = db.get_stats(instance1, month)
    
    assert stats2['battle_count'] == 1
    assert stats2['akashi_ap'] == 0 # Instance 2 should NOT have instance 1's AP
    assert stats1_again['battle_count'] == 1 # Instance 1 should remain same
    logger.info("✓ Multi-instance Isolation Passed")
    
    # 4. Test Encryption & Anti-tamper
    logger.info("Testing Anti-tamper...")
    # Read the DB file, find the blob and flip a bit
    import sqlite3
    with sqlite3.connect(test_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT encrypted_blob FROM cl1_data WHERE instance = ? AND month = ?", (instance1, month))
        blob = bytearray(cursor.fetchone()[0])
        # Tamper with the ciphertext or tag (offset 32 is start of ciphertext)
        blob[35] = blob[35] ^ 0xFF 
        
        cursor.execute("UPDATE cl1_data SET encrypted_blob = ? WHERE instance = ? AND month = ?", (bytes(blob), instance1, month))
        conn.commit()
    
    # Try to read back
    tampered_stats = db.get_stats(instance1, month)
    # db.get_stats returns empty data on decryption failure
    assert tampered_stats['battle_count'] == 0
    logger.info("✓ Anti-tamper Detection Passed (Decryption failed as expected)")
    
    # Give some time for OS to release handles and collect garbage
    import gc
    gc.collect()
    
    # Cleanup
    try:
        if test_db_path.exists():
            test_db_path.unlink()
    except Exception as e:
        logger.warning(f"Could not delete test DB: {e}. This is common on Windows and can be ignored if tests passed.")
    
    logger.hr("Verification Complete: ALL TESTS PASSED")

if __name__ == "__main__":
    try:
        test_secure_storage()
    except Exception as e:
        logger.exception(f"Verification FAILED: {e}")
        sys.exit(1)
