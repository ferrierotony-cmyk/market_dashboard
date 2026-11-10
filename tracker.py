"""Allocation log: a local SQLite database that syncs to an external tracking spreadsheet.

Every baseline and regime shift is written to data/allocations.db (SQLite) and
output/allocation_log.csv, then pushed to a Google Sheet when one is configured. Rows are marked
synced only after the sheet accepts them, so a failed sync is retried and never duplicates rows.

Google Sheet setup (optional):
  1. Create a Google Cloud service account and download its JSON key. Keep that file private.
  2. Share your spreadsheet with the service account's email address, as an editor.
  3. Set environment variables (never put them in code or commit them):
       GOOGLE_SERVICE_ACCOUNT_JSON   path to the key file
       GOOGLE_SHEET_ID               the long id in the sheet's URL
       GOOGLE_SHEET_TAB              tab name (default "Allocations"; created if missing)
  4. pip install gspread

Commands:
  python tracker.py check     # test the database and the sheet connection
  python tracker.py log       # log the current target mix from the latest alert state
  python tracker.py show      # last 15 rows
  python tracker.py sync      # push unsynced rows to the sheet
"""
import argparse
import csv
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import allocator as al

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "allocations.db"
CSV_PATH = ROOT / "output" / "allocation_log.csv"
SHEET_HEADER = (["time_utc", "event", "regime_nodes"] + [f"w_{a}" for a in al.ASSETS]
                + [f"chg_{a}" for a in al.ASSETS] + ["note"])


class SheetSink:
    """Append rows to one worksheet of a Google Sheet through gspread."""

    def __init__(self, worksheet):
        self.ws = worksheet

    @classmethod
    def from_env(cls, env=os.environ, gspread_module=None):
        path, sheet_id = env.get("GOOGLE_SERVICE_ACCOUNT_JSON"), env.get("GOOGLE_SHEET_ID")
        if not (path and sheet_id):
            return None
        if gspread_module is None:
            import gspread as gspread_module
        book = gspread_module.service_account(filename=path).open_by_key(sheet_id)
        tab = env.get("GOOGLE_SHEET_TAB", "Allocations")
        try:
            ws = book.worksheet(tab)
        except Exception:
            ws = book.add_worksheet(title=tab, rows=1000, cols=len(SHEET_HEADER))
        return cls(ws)

    def append(self, rows: list[list]) -> None:
        if not self.ws.row_values(1):
            self.ws.append_rows([SHEET_HEADER], value_input_option="RAW")
        self.ws.append_rows(rows, value_input_option="USER_ENTERED")


class AllocationLog:
    def __init__(self, db_path: Path = DB_PATH, csv_path: Path = CSV_PATH, sheet: "SheetSink | None" = None):
        self.db_path, self.csv_path, self.sheet = Path(db_path), Path(csv_path), sheet
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT, time_utc TEXT NOT NULL, event TEXT NOT NULL,
                regime_nodes TEXT NOT NULL, weights TEXT NOT NULL, changes TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '', synced INTEGER NOT NULL DEFAULT 0)""")

    def _conn(self):
        return sqlite3.connect(self.db_path, timeout=30)

    def record(self, event: str, targets: dict, previous: dict | None = None, nodes=(), note: str = "",
               sync: bool = False, now: datetime | None = None) -> int:
        """Write one allocation row. Returns its id. Optionally pushes unsynced rows to the sheet."""
        now = now or datetime.now(timezone.utc)
        changes = {a: round(targets[a] - (previous or {}).get(a, targets[a]), 4) for a in al.ASSETS}
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO allocations (time_utc, event, regime_nodes, weights, changes, note) VALUES (?,?,?,?,?,?)",
                (now.isoformat(timespec="seconds"), event, ",".join(nodes), json.dumps(targets), json.dumps(changes), note))
            row_id = cur.lastrowid
        self._append_csv(self._row_values(self.row(row_id)))
        if sync and self.sheet is not None:
            try:
                self.sync_sheet()
            except Exception as e:                      # the local log is the record; the sheet catches up later
                print(f"  sheet sync failed (will retry): {type(e).__name__}: {str(e)[:80]}")
        return row_id

    def row(self, row_id: int) -> dict:
        with self._conn() as c:
            r = c.execute("SELECT id,time_utc,event,regime_nodes,weights,changes,note,synced FROM allocations WHERE id=?",
                          (row_id,)).fetchone()
        return self._as_dict(r)

    @staticmethod
    def _as_dict(r) -> dict:
        return {"id": r[0], "time_utc": r[1], "event": r[2], "regime_nodes": r[3], "weights": json.loads(r[4]),
                "changes": json.loads(r[5]), "note": r[6], "synced": bool(r[7])}

    @staticmethod
    def _row_values(d: dict) -> list:
        return ([d["time_utc"], d["event"], d["regime_nodes"]] + [d["weights"][a] for a in al.ASSETS]
                + [d["changes"][a] for a in al.ASSETS] + [d["note"]])

    def _append_csv(self, values: list) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.csv_path.exists()
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(SHEET_HEADER)
            w.writerow(values)

    def recent(self, n: int = 15) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT id,time_utc,event,regime_nodes,weights,changes,note,synced FROM allocations "
                             "ORDER BY id DESC LIMIT ?", (n,)).fetchall()
        return [self._as_dict(r) for r in rows][::-1]

    def unsynced(self) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT id,time_utc,event,regime_nodes,weights,changes,note,synced FROM allocations "
                             "WHERE synced=0 ORDER BY id").fetchall()
        return [self._as_dict(r) for r in rows]

    def sync_sheet(self) -> int:
        """Push unsynced rows. Marks them synced only after the sheet accepts the whole batch."""
        if self.sheet is None:
            raise RuntimeError("no sheet configured (see the setup notes at the top of tracker.py)")
        pending = self.unsynced()
        if not pending:
            return 0
        self.sheet.append([self._row_values(d) for d in pending])
        with self._conn() as c:
            c.executemany("UPDATE allocations SET synced=1 WHERE id=?", [(d["id"],) for d in pending])
        return len(pending)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["check", "log", "show", "sync"])
    args = ap.parse_args(argv)

    try:
        sheet = SheetSink.from_env()
        sheet_msg = "connected" if sheet else "not configured (set GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_SHEET_ID)"
    except Exception as e:
        sheet, sheet_msg = None, f"connection failed: {type(e).__name__}: {str(e)[:80]}"
    log = AllocationLog(sheet=sheet)

    if args.command == "check":
        print(f"Database: {log.db_path} ({len(log.recent(10**6))} rows, {len(log.unsynced())} unsynced)")
        print(f"Spreadsheet: {sheet_msg}")
    elif args.command == "show":
        for d in log.recent():
            w = " ".join(f"{a[:3]} {d['weights'][a]*100:.1f}" for a in al.ASSETS)
            print(f"#{d['id']:<3} {d['time_utc']}  {d['event']:<9} {w}  nodes: {d['regime_nodes'] or 'none'}"
                  f"  {'synced' if d['synced'] else 'local only'}")
    elif args.command == "sync":
        print(f"Synced {log.sync_sheet()} row(s) to the sheet.")
    else:
        import alerts
        import regime
        cfg = alerts.load_rules()
        state = alerts.load_state()
        nodes = regime.triggered_nodes(state, cfg["rules"])
        target = regime.target_weights(nodes, cfg["rules"], regime.regime_cfg(cfg)["max_dev"])
        last = state.get("regime:last", {}).get("target")
        targets = {a: round(float(target[a]), 4) for a in al.ASSETS}
        rid = log.record("snapshot", targets, last, nodes, note="manual snapshot", sync=True)
        print(f"Logged row #{rid}: " + ", ".join(f"{a} {targets[a]*100:.1f}%" for a in al.ASSETS))


if __name__ == "__main__":
    main()
