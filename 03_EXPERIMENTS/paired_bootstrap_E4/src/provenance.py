"""Hashing, environment capture, manifests, run directories and the run registry.

Everything here is side-effect free until a function is called; importing the
module creates no files.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata as md
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE = EXPERIMENT_DIR.parents[1]
OUTPUT_ROOT = EXPERIMENT_DIR / "outputs"
REGISTRY = EXPERIMENT_DIR / "run_registry.csv"

PACKAGES = [
    "numpy", "pandas", "scikit-learn", "lightgbm", "xgboost", "pyarrow",
    "scipy", "tldextract", "matplotlib", "nbclient", "nbformat", "ipykernel",
]

# Distribution name -> importable module name, for the packages where they differ.
MODULES = {"scikit-learn": "sklearn"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def run_id(prefix: str = "") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{prefix}{stamp}"


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_entry(path: Path, role: str = "") -> dict:
    path = Path(path)
    return {
        "path": str(path),
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def code_manifest() -> dict:
    """Hashes of the code that produced a run (src + notebooks + protocol)."""
    entries = []
    for path in sorted((EXPERIMENT_DIR / "src").glob("*.py")):
        entries.append(file_entry(path, "code"))
    for path in sorted((EXPERIMENT_DIR / "notebooks").glob("*.ipynb")):
        entries.append(file_entry(path, "notebook"))
    protocol = WORKSPACE / "phishing" / "PROTOKOL_EKSPERIMEN_SINTA2_v1.md"
    if protocol.exists():
        entries.append(file_entry(protocol, "protocol"))
    return {"captured_at": utc_now(), "files": entries}


def _pyvenv_includes_system_site() -> bool:
    """Read `include-system-site-packages` from the running venv's pyvenv.cfg."""
    cfg = Path(sys.prefix) / "pyvenv.cfg"
    try:
        for line in cfg.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            if key.strip() == "include-system-site-packages":
                return value.strip().lower() == "true"
    except OSError:
        return False
    return False


def environment_snapshot() -> dict:
    versions = {}
    origins = {}
    for name in PACKAGES:
        try:
            versions[name] = md.version(name)
        except md.PackageNotFoundError:
            versions[name] = "not installed"
            continue
        try:
            mod = importlib.import_module(MODULES.get(name, name))
            origins[name] = getattr(mod, "__file__", "") or ""
        except ImportError:
            origins[name] = "not importable"
    return {
        "captured_at": utc_now(),
        "python": sys.version,
        "python_executable": sys.executable,
        "prefix": sys.prefix,
        # True when the venv inherits the shared interpreter's site-packages, i.e. the
        # pinned freeze is an upper bound rather than an enclosure. Recorded so a
        # silent change in the shared interpreter cannot pass unnoticed.
        "include_system_site_packages": _pyvenv_includes_system_site(),
        "package_origins": origins,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpus": os.cpu_count(),
        "packages": versions,
        "thread_env": {
            k: os.environ.get(k)
            for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
            if os.environ.get(k)
        },
    }


def new_run_dir(prefix: str = "", root: Path | None = None) -> tuple[str, Path]:
    rid = run_id(prefix)
    path = (Path(root) if root else OUTPUT_ROOT) / rid
    path.mkdir(parents=True, exist_ok=False)
    return rid, path


def write_json(path: Path, payload) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def log(path: Path, message: str) -> None:
    """Append a timestamped line to an execution log and echo it."""
    line = f"[{utc_now()}] {message}"
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


class Registry:
    """Append-only CSV of runs. One row per run directory, updated on completion."""

    COLUMNS = [
        "run_id", "experiment", "dataset", "configs", "protocols", "models",
        "seeds", "threads", "started_utc", "finished_utc", "duration_s",
        "status", "n_fits", "output_dir", "log_path", "notes",
    ]

    # Text columns stay object dtype: pandas otherwise infers float64 from a column
    # that is empty in the first rows, and a later timestamp update raises TypeError.
    NUMERIC = ("threads", "duration_s", "n_fits")

    def __init__(self, path: Path = REGISTRY):
        self.path = Path(path)

    def _read(self):
        import pandas as pd

        if not self.path.exists():
            df = pd.DataFrame(columns=self.COLUMNS, dtype="object")
        else:
            df = pd.read_csv(self.path, dtype=str, keep_default_na=False)
        for column in self.NUMERIC:
            df[column] = pd.to_numeric(df[column], errors="coerce")
        return df

    def upsert(self, row: dict) -> None:
        import pandas as pd

        df = self._read()
        row = {k: v for k, v in row.items() if k in self.COLUMNS}
        if "run_id" not in row:
            raise ValueError("upsert requires run_id")
        if (df.run_id == row["run_id"]).any():
            # Only the supplied keys are written; missing ones keep their values
            # (a failure-path update must not erase the start-time metadata).
            for key, value in row.items():
                df.loc[df.run_id == row["run_id"], key] = value
        else:
            row = {c: row.get(c, "") for c in self.COLUMNS}
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(self.path, index=False)


def timed(fn, *args, **kwargs):
    """Run fn and return (result, seconds)."""
    t0 = time.perf_counter()
    out = fn(*args, **kwargs)
    return out, time.perf_counter() - t0
