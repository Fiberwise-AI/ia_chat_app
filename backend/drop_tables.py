"""Drop V003 and V004 tables to allow re-running migrations."""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nexusql import DatabaseManager

# Use SQLite database
db_url = 'sqlite:///ia_chat_app.db'

print(f"Connecting to: {db_url}")
db = DatabaseManager(db_url)
db.connect()

try:
    print("Dropping document_collections table...")
    db.execute("DROP TABLE IF EXISTS document_collections")

    print("Dropping documents table...")
    db.execute("DROP TABLE IF EXISTS documents")

    print("Tables dropped successfully!")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.disconnect()
    print("Done!")
