"""Loading, the inherited cleaning protocol, and the fit/validation split.

The cleaning steps are Experiment 4's, applied in the same order, so that the
test partition this experiment evaluates on is row-for-row the one Experiment 4
already published. The only addition is splitting the surviving training period
at ``VAL_START``.

Order (do not reorder without re-deriving the test set):

 1. drop training rows dated at or after CUTOFF (seam purge)
 2. canonicalise URLs; exclude unparseable rows under a logged cap
 3. sort training by (date, row_id), drop duplicate canonical URLs keeping first
 4. drop test rows whose canonical URL occurred in training (train->test leak)
 5. sort test by (date, row_id), drop duplicate canonical URLs keeping first
 6. split training into fit (< VAL_START) and validation (>= VAL_START)
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from .config import CUTOFF, LABEL_MAP, UNPARSEABLE_MAX_SHARE, UNPARSEABLE_POLICY, VAL_START
from .features import canonical_url


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_partition(root: Path, part: str):
    """Read url/label/date from every shard of one partition; return rows + manifest."""
    paths = sorted(Path(root).glob(f"{part}-*.parquet"))
    if not paths:
        raise FileNotFoundError(f"No {part}-*.parquet in {root}")
    frames, manifest = [], []
    for path in paths:
        schema = pq.read_schema(path)
        needed = {"url", "label", "date"}
        if not needed.issubset(set(schema.names)):
            raise ValueError(f"Different schema: {path.name}; needed {needed}")
        frame = pq.read_table(path, columns=["url", "label", "date"]).to_pandas()
        frame["source_file"] = path.name
        frame["source_row"] = np.arange(len(frame))
        frames.append(frame)
        manifest.append(dict(file=path.name, rows=len(frame),
                             bytes=path.stat().st_size, sha256=file_sha256(path)))
    df = pd.concat(frames, ignore_index=True)
    if df[["url", "label", "date"]].isna().any().any():
        raise ValueError(f"{part}: empty URL/label/date. Source audit required.")
    if not df.url.map(lambda u: isinstance(u, str) and bool(u.strip())).all():
        raise ValueError(f"{part}: URL is not valid text.")
    unknown = set(df.label.unique()) - set(LABEL_MAP)
    if unknown:
        raise ValueError(f"{part}: unknown label(s) {sorted(unknown)}")
    df["y_phish"] = df.label.map(LABEL_MAP).astype("int8")
    df["date"] = pd.to_datetime(df.date, errors="raise", utc=True)
    if df.date.isna().any():
        raise ValueError(f"{part}: invalid date.")
    df["row_id"] = part + ":" + df.source_file + ":" + df.source_row.astype(str)
    return df, manifest


def prepare(train_raw: pd.DataFrame, test_raw: pd.DataFrame):
    """Apply the inherited protocol; return fit, validation, test, ledger, excluded."""
    ledger, excluded, unparseable = [], [], []

    def record(stage, df):
        ledger.append(dict(stage=stage, rows=len(df),
                           benign=int((df.y_phish == 0).sum()),
                           phish=int((df.y_phish == 1).sum()),
                           min_date=str(df.date.min()), max_date=str(df.date.max())))

    train, test = train_raw.copy(), test_raw.copy()
    record("train_raw", train)
    record("test_raw", test)

    if (test.date < CUTOFF).any():
        raise ValueError("Test partition has dates before the cutoff; do not move rows automatically.")
    ex = train.loc[train.date >= CUTOFF, ["row_id"]].copy()
    ex["reason"] = "train_at_or_after_cutoff"
    excluded.append(ex)
    train = train.loc[train.date < CUTOFF].copy()
    record("train_after_boundary_purge", train)

    for name in ("train", "test"):
        df = train if name == "train" else test
        keys, bad = [], []
        for row in df.itertuples(index=False):
            try:
                keys.append(canonical_url(row.url))
            except (ValueError, UnicodeError) as error:
                keys.append(None)
                bad.append(dict(row_id=row.row_id, partition=name, label=row.label,
                                date=str(row.date),
                                parser_error=f"{type(error).__name__}: {error}",
                                url=row.url))
        if bad:
            share = len(bad) / max(1, len(df))
            if UNPARSEABLE_POLICY == "raise" or share > UNPARSEABLE_MAX_SHARE:
                raise ValueError(
                    f"{name}: {len(bad)} unparseable URLs ({share:.6%} > cap "
                    f"{UNPARSEABLE_MAX_SHARE:.6%}); check {[b['row_id'] for b in bad[:5]]}.")
            drop = df.row_id.isin({b["row_id"] for b in bad})
            ex = df.loc[drop, ["row_id"]].copy()
            ex["reason"] = "unparseable_url"
            excluded.append(ex)
            unparseable.extend(bad)
            df = df.loc[~drop].copy()
            keys = [k for k in keys if k is not None]
            record(f"{name}_after_unparseable_purge", df)
        df["url_key"] = keys
        if name == "train":
            train = df
        else:
            test = df

    if train.groupby("url_key").y_phish.nunique().gt(1).any():
        raise ValueError("Conflicting labels on a training URL; adjudicate before fitting.")
    train = train.sort_values(["date", "row_id"], kind="stable")
    dup = train.duplicated("url_key", keep="first")
    ex = train.loc[dup, ["row_id"]].copy()
    ex["reason"] = "duplicate_train_url"
    excluded.append(ex)
    train = train.loc[~dup].copy()
    record("train_unique", train)

    repeated = test.url_key.isin(set(train.url_key))
    ex = test.loc[repeated, ["row_id"]].copy()
    ex["reason"] = "test_url_seen_in_train"
    excluded.append(ex)
    test = test.loc[~repeated].copy()
    record("test_after_seen_url_purge", test)

    if test.groupby("url_key").y_phish.nunique().gt(1).any():
        raise ValueError("Conflicting labels on a test URL; adjudicate without touching training.")
    test = test.sort_values(["date", "row_id"], kind="stable")
    dup = test.duplicated("url_key", keep="first")
    ex = test.loc[dup, ["row_id"]].copy()
    ex["reason"] = "duplicate_test_url"
    excluded.append(ex)
    test = test.loc[~dup].copy()
    record("test_unique", test)

    is_val = train.date >= VAL_START
    fit = train.loc[~is_val].copy()
    val = train.loc[is_val].copy()
    record("fit", fit)
    record("validation", val)

    for name, df in (("fit", fit), ("validation", val), ("test", test)):
        if set(df.y_phish.unique()) != {0, 1}:
            raise ValueError(f"{name}: both classes must remain after filtering.")
    assert fit.date.max() < VAL_START, "Fit block crosses into validation."
    assert val.date.min() >= VAL_START and val.date.max() < CUTOFF, "Validation block misplaced."
    assert test.date.min() >= CUTOFF, "Test starts before the cutoff."
    assert fit.date.max() < test.date.min(), "Fit is not strictly earlier than test."
    assert val.date.max() < test.date.min(), "Validation is not strictly earlier than test."
    assert set(fit.url_key).isdisjoint(val.url_key), "A URL appears in both fit and validation."
    assert set(fit.url_key).isdisjoint(test.url_key), "A URL appears in both fit and test."
    assert set(val.url_key).isdisjoint(test.url_key), "A URL appears in both validation and test."
    assert set(fit.row_id).isdisjoint(val.row_id), "Fit and validation share rows."

    return (fit.reset_index(drop=True), val.reset_index(drop=True),
            test.reset_index(drop=True), pd.DataFrame(ledger),
            pd.concat(excluded, ignore_index=True), pd.DataFrame(unparseable))
