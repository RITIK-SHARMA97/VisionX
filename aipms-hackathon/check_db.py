#!/usr/bin/env python
"""Check database status and schema."""
import sqlite3
import os

db_path = 'aipms.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"✓ Database exists. Tables ({len(tables)}):")
    for t in tables:
        print(f"  - {t[0]}")
    conn.close()
else:
    print("✗ Database not found - needs to be created")
