# Open the F1 database in DuckDB's browser SQL editor (read-only).
# Run: python python\sql_ui.py   then open http://localhost:4213
from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "f1_db.duckdb"

# In-memory main DB so the UI can store its own notebooks; the F1 file is attached read-only.
# (Opening the F1 file itself with read_only=True breaks the UI: it can't create its "_duckdb_ui" catalog.)
con = duckdb.connect()
con.execute(f"ATTACH '{DB_PATH.as_posix()}' AS f1 (READ_ONLY)")
con.execute("USE f1")
con.execute("CALL start_ui()")
input("SQL UI running at http://localhost:4213 - press Enter to stop ")
