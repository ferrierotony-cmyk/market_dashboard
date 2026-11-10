"""Pre-registration lock. Fixes a design's spec before it is tested, and refuses to run if it changed.

  python prereg.py lock prereg_v2.json     # write prereg_v2.lock (sha256 + UTC time). Refuses to overwrite.
  python prereg.py verify prereg_v2.json   # exit 0 only if the spec still matches its lock

The hash covers the spec's canonical JSON, so reformatting does not matter but any change of
content does. This does not stop someone from deleting the lock; it makes silent edits visible.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def spec_hash(path: Path) -> str:
    canonical = json.dumps(json.loads(Path(path).read_text(encoding="utf-8")), sort_keys=True,
                           separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def lock_path(path: Path) -> Path:
    return Path(path).with_suffix(".lock")


def lock(path: Path) -> dict:
    lp = lock_path(path)
    if lp.exists():
        raise FileExistsError(f"{lp.name} already exists; a locked design is never re-locked")
    rec = {"spec": Path(path).name, "sha256": spec_hash(path), "locked_utc": datetime.now(timezone.utc).isoformat()}
    lp.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


def verify(path: Path) -> dict:
    """Returns the lock record; raises if the lock is missing or the spec has changed."""
    lp = lock_path(path)
    if not lp.exists():
        raise RuntimeError(f"{lp.name} not found: lock the spec before testing it")
    rec = json.loads(lp.read_text(encoding="utf-8"))
    if rec["sha256"] != spec_hash(path):
        raise RuntimeError(f"{Path(path).name} has changed since it was locked at {rec['locked_utc']}")
    return rec


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) != 2 or argv[0] not in ("lock", "verify"):
        print(__doc__)
        return 2
    cmd, path = argv[0], Path(argv[1])
    try:
        rec = lock(path) if cmd == "lock" else verify(path)
    except Exception as e:
        print(f"FAILED: {e}")
        return 1
    print(f"{cmd} ok: {rec['spec']} sha256={rec['sha256'][:16]}... locked {rec['locked_utc']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
