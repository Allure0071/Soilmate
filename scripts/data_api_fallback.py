"""Small read-only /api/data server for an older remote Soilmate backend.

Uses only Python's standard library. Run from anywhere with Python 3.9+.
"""

import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
DATABASES = {5: ROOT / "data" / "soil.sqlite", 1: ROOT / "data" / "soil_1km.sqlite"}
TABLE_ORDER = {"points": "row, col", "indicators": "id", "meta": "key"}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/data":
            return self.respond(404, {"detail": "Not Found"})
        args = parse_qs(parsed.query)
        try:
            res = int(args.get("res", ["5"])[0])
            table = args.get("table", ["points"])[0]
            page = int(args.get("page", ["1"])[0])
            page_size = int(args.get("page_size", ["20"])[0])
            if res not in DATABASES or table not in TABLE_ORDER or page < 1 or not 1 <= page_size <= 100:
                raise ValueError("Invalid resolution, table, or page")
            bounds = [args.get(key, [None])[0] for key in ("lon_min", "lon_max", "lat_min", "lat_max")]
            if any(value is not None for value in bounds) and not all(value is not None for value in bounds):
                raise ValueError("All four bounds are required")
            params = [float(value) for value in bounds] if all(value is not None for value in bounds) else []
        except (ValueError, TypeError) as exc:
            return self.respond(400, {"detail": str(exc)})

        where = "WHERE lon BETWEEN ? AND ? AND lat BETWEEN ? AND ?" if table == "points" and params else ""
        if not where:
            params = []
        try:
            with sqlite3.connect(DATABASES[res].as_uri() + "?mode=ro", uri=True) as conn:
                columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
                total = conn.execute(f"SELECT count(*) FROM {table} {where}", params).fetchone()[0]
                rows = conn.execute(
                    f"SELECT * FROM {table} {where} ORDER BY {TABLE_ORDER[table]} LIMIT ? OFFSET ?",
                    params + [page_size, (page - 1) * page_size],
                ).fetchall()
                names = dict(conn.execute("SELECT col_name, cname FROM indicators")) if table == "points" else {}
        except sqlite3.Error as exc:
            return self.respond(500, {"detail": str(exc)})

        self.respond(200, {
            "res": res, "total": total, "page": page, "page_size": page_size,
            "columns": [{"col": col, "cname": names.get(col[2:], col) if col.startswith("v_") else col} for col in columns],
            "rows": rows,
        })

    def respond(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print("Read-only SQLite data API on http://127.0.0.1:18002", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 18002), Handler).serve_forever()
