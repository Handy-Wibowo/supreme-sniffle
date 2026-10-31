"""Local runner for AUTHOR_RUN_PhreshPhish_Temporal.ipynb.

This is a faithful port of notebook cells C0-C6. Only two things differ:

  1. DATA_DIR / OUTPUT_ROOT point at local paths instead of Google Drive
     (the Colab `drive.mount` block is skipped).
  2. Shard counts, seeds and bootstrap replicates can be overridden through
     environment variables, so a smoke test can run before the full job.
     The defaults reproduce the notebook exactly.

Nothing about the protocol is changed: the cutoff, the purge order, the
deduplication, the 18 URL features, the LightGBM parameters, the 0.5
threshold and the domain-cluster bootstrap are as authored.

Environment overrides
  PHRESH_DATA_DIR        dataset dir containing train-*.parquet / test-*.parquet
  PHRESH_OUTPUT_ROOT     where the timestamped output folder is created
  PHRESH_TRAIN_SHARDS    use only the first N train shards (smoke test)
  PHRESH_TEST_SHARDS     use only the first N test shards (smoke test)
  PHRESH_SEEDS           comma separated seeds
  PHRESH_BOOTSTRAP       bootstrap replicate count
"""

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import ipaddress
import json
import os
import platform
import re
import sys
import time
from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import lightgbm as lgb
import tldextract
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
    matthews_corrcoef,
)

# ---------------------------------------------------------------- C0 packages
packages = {
    "numpy": "numpy",
    "pandas": "pandas",
    "pyarrow": "pyarrow",
    "sklearn": "scikit-learn",
    "lightgbm": "lightgbm",
    "tldextract": "tldextract",
}

# ------------------------------------------------------------- C1 configuration
DATA_DIR = Path(os.environ.get(
    "PHRESH_DATA_DIR", r"E:\Kuliah\Tugas Akhir\dataset\PhreshPhish\data"))
OUTPUT_ROOT = Path(os.environ.get(
    "PHRESH_OUTPUT_ROOT",
    r"E:\Kuliah\Tugas Akhir\Experiment\4 - PhreshPhish Temporal Audit\outputs"))

CUTOFF = pd.Timestamp("2025-09-08", tz="UTC")
SEEDS = [int(s) for s in os.environ.get(
    "PHRESH_SEEDS", "13,42,2024,777,31415").split(",")]
PRIMARY_SEED = 13
THRESHOLD = 0.5
BOOTSTRAP_REPLICATES = int(os.environ.get("PHRESH_BOOTSTRAP", "1000"))
MODEL_PARAMS = dict(n_estimators=300, learning_rate=0.05, num_leaves=63,
                    n_jobs=-1, verbosity=-1)

TRAIN_SHARDS = int(os.environ["PHRESH_TRAIN_SHARDS"]) if os.environ.get("PHRESH_TRAIN_SHARDS") else None
TEST_SHARDS = int(os.environ["PHRESH_TEST_SHARDS"]) if os.environ.get("PHRESH_TEST_SHARDS") else None

# A URL that urllib cannot parse cannot receive the 18 URL features, so the row
# cannot be modelled. The notebook's C2 raises on any such row to force a
# documented decision instead of a silent drop. "exclude" records each such row
# in excluded_rows.csv with the reason unparseable_url and in a dedicated
# unparseable_urls.csv with the parser error, and aborts if the count exceeds
# UNPARSEABLE_MAX_SHARE of the partition, so a corpus-wide regression still fails.
UNPARSEABLE_POLICY = os.environ.get("PHRESH_UNPARSEABLE_POLICY", "raise").strip().lower()
UNPARSEABLE_MAX_SHARE = float(os.environ.get("PHRESH_UNPARSEABLE_MAX_SHARE", "0.0001"))
if UNPARSEABLE_POLICY not in {"raise", "exclude"}:
    raise ValueError("PHRESH_UNPARSEABLE_POLICY must be 'raise' or 'exclude'.")

UNPARSEABLE_LOG = []

OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
OUT = OUTPUT_ROOT / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
OUT.mkdir(parents=True, exist_ok=False)

ENVIRONMENT = {}
for module_name, dist_name in packages.items():
    try:
        ENVIRONMENT[module_name] = importlib.metadata.version(dist_name)
    except importlib.metadata.PackageNotFoundError:
        ENVIRONMENT[module_name] = "unknown"

DESIGN = dict(
    protocol="modified_temporal_url_deduplicated",
    training_corpus="PhreshPhish",
    evaluation_corpus="PhreshPhish",
    label_mapping={"benign": 0, "phish": 1},
    cutoff=str(CUTOFF),
    seeds=SEEDS,
    primary_seed=PRIMARY_SEED,
    threshold=THRESHOLD,
    model=MODEL_PARAMS,
    include_psl_private_domains=False,
    tuning="none",
    test_status="previously inspected in exploratory probes",
    bootstrap_replicates=BOOTSTRAP_REPLICATES,
    environment=ENVIRONMENT,
    python=sys.version,
    platform=platform.platform(),
    cpu=platform.processor(),
    logical_cpus=os.cpu_count(),
    executor="local_runner_port_of_notebook",
    train_shard_limit=TRAIN_SHARDS,
    test_shard_limit=TEST_SHARDS,
    unparseable_url_policy=UNPARSEABLE_POLICY,
    unparseable_url_max_share=UNPARSEABLE_MAX_SHARE,
    unparseable_url_decision=(
        "Rows whose URL urllib cannot parse receive no features and are excluded "
        "with reason unparseable_url, logged in unparseable_urls.csv; the run aborts "
        "if the share exceeds unparseable_url_max_share."),
)
(OUT / "design.json").write_text(json.dumps(DESIGN, indent=2), encoding="utf-8")
print("Output:", OUT)
print("Fits planned:", len(SEEDS), "; no duration estimate copied from another corpus.")
sys.stdout.flush()


# ------------------------------------------------------- C2 auditable loading
def file_sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_partition(root, part, shard_limit=None):
    paths = sorted(Path(root).glob(f"{part}-*.parquet"))
    if not paths:
        raise FileNotFoundError(f"No {part}-*.parquet in {root}")
    if shard_limit:
        paths = paths[:shard_limit]
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
                             bytes=path.stat().st_size,
                             sha256=file_sha256(path)))
    df = pd.concat(frames, ignore_index=True)
    if df[["url", "label", "date"]].isna().any().any():
        raise ValueError(f"{part}: empty URL/label/date. Source audit required.")
    if not df.url.map(lambda u: isinstance(u, str) and bool(u.strip())).all():
        raise ValueError(f"{part}: URL is not valid text.")
    if not set(df.label.unique()).issubset({"benign", "phish"}):
        raise ValueError(f"{part}: unknown label: {df.label.unique()}")
    df["y_phish"] = df.label.map({"benign": 0, "phish": 1}).astype("int8")
    df["date"] = pd.to_datetime(df.date, errors="raise", utc=True)
    if df.date.isna().any():
        raise ValueError(f"{part}: invalid date.")
    df["row_id"] = part + ":" + df.source_file + ":" + df.source_row.astype(str)
    return df, manifest


def parse_url(u):
    u = u.strip()
    p = urlsplit(u if "://" in u else "http://" + u)
    if p.scheme.lower() not in {"http", "https"} or not p.hostname:
        raise ValueError("URL requires a host and a parseable HTTP(S) scheme.")
    _ = p.port  # rejects an invalid port
    host = p.hostname.lower().rstrip(".")
    if any(c.isspace() for c in host):
        raise ValueError("Space inside host.")
    return p, host


def canonical_url(u):
    p, host = parse_url(u)
    # Host and scheme are case insensitive. Path/query are left intact.
    # Fragments are not sent to the server; credentials are kept when present.
    host_netloc = "[" + host + "]" if ":" in host else host
    if p.port is not None:
        host_netloc += ":" + str(p.port)
    auth = p.netloc.rsplit("@", 1)[0] + "@" if "@" in p.netloc else ""
    return urlunsplit((p.scheme.lower(), auth + host_netloc, p.path or "/", p.query, ""))


def prepare_temporal(train_raw, test_raw, cutoff):
    ledger = []
    UNPARSEABLE_LOG.clear()

    def record(stage, df):
        ledger.append(dict(stage=stage, rows=len(df),
                           benign=int((df.y_phish == 0).sum()),
                           phish=int((df.y_phish == 1).sum()),
                           min_date=str(df.date.min()), max_date=str(df.date.max())))

    train, test = train_raw.copy(), test_raw.copy()
    record("train_raw", train)
    record("test_raw", test)
    if (test.date < cutoff).any():
        raise ValueError("Test partition has dates before the cutoff; do not move rows automatically.")
    excluded = train.loc[train.date >= cutoff, ["row_id"]].copy()
    excluded["reason"] = "train_at_or_after_cutoff"
    train = train.loc[train.date < cutoff].copy()
    record("train_after_boundary_purge", train)

    for name, df in [("train", train), ("test", test)]:
        keys, bad, bad_rows = [], [], []
        for row in df.itertuples(index=False):
            try:
                keys.append(canonical_url(row.url))
            except (ValueError, UnicodeError) as error:
                keys.append(None)
                bad.append(row.row_id)
                bad_rows.append(dict(row_id=row.row_id, partition=name,
                                     label=row.label, date=str(row.date),
                                     parser_error=f"{type(error).__name__}: {error}",
                                     url=row.url))
        if bad:
            share = len(bad) / max(1, len(df))
            if UNPARSEABLE_POLICY == "raise" or share > UNPARSEABLE_MAX_SHARE:
                raise ValueError(
                    f"{name}: {len(bad)} unparseable URLs "
                    f"({share:.6%} > cap {UNPARSEABLE_MAX_SHARE:.6%}); "
                    f"check row_id {bad[:5]} and document the decision.")
            # Documented exclusion: the row has no usable URL features.
            drop = df.row_id.isin(set(bad))
            ex = df.loc[drop, ["row_id"]].copy()
            ex["reason"] = "unparseable_url"
            excluded = pd.concat([excluded, ex], ignore_index=True)
            UNPARSEABLE_LOG.extend(bad_rows)
            print(f"  excluded {len(bad)} unparseable {name} row(s) "
                  f"({share:.6%}, cap {UNPARSEABLE_MAX_SHARE:.6%}): {bad[:5]}")
            sys.stdout.flush()
            df = df.loc[~drop].copy()
            keys = [k for k in keys if k is not None]
            if name == "train":
                train = df
            else:
                test = df
            record(f"{name}_after_unparseable_purge", df)
        df["url_key"] = keys
        print(f"  canonicalised {name}: {len(df)} rows")
        sys.stdout.flush()

    # Training is not modified based on test labels.
    conflict = train.groupby("url_key").y_phish.nunique().gt(1)
    if conflict.any():
        raise ValueError("Conflicting labels on a training URL; adjudicate before fitting.")
    train = train.sort_values(["date", "row_id"], kind="stable")
    duplicate = train.duplicated("url_key", keep="first")
    ex = train.loc[duplicate, ["row_id"]].copy()
    ex["reason"] = "duplicate_train_url"
    excluded = pd.concat([excluded, ex], ignore_index=True)
    train = train.loc[~duplicate].copy()
    record("train_unique", train)

    repeated = test.url_key.isin(set(train.url_key))
    ex = test.loc[repeated, ["row_id"]].copy()
    ex["reason"] = "test_url_seen_in_train"
    excluded = pd.concat([excluded, ex], ignore_index=True)
    test = test.loc[~repeated].copy()
    record("test_after_seen_url_purge", test)

    conflict = test.groupby("url_key").y_phish.nunique().gt(1)
    if conflict.any():
        raise ValueError("Conflicting labels on a test URL; adjudicate without touching training.")
    test = test.sort_values(["date", "row_id"], kind="stable")
    duplicate = test.duplicated("url_key", keep="first")
    ex = test.loc[duplicate, ["row_id"]].copy()
    ex["reason"] = "duplicate_test_url"
    excluded = pd.concat([excluded, ex], ignore_index=True)
    test = test.loc[~duplicate].copy()
    record("test_unique", test)

    for name, df in [("train", train), ("test", test)]:
        if set(df.y_phish.unique()) != {0, 1}:
            raise ValueError(f"{name}: both classes must remain after filtering.")
    assert train.date.max() < test.date.min(), "Time order is not strict."
    assert set(train.row_id).isdisjoint(test.row_id), "Overlapping rows."
    assert set(train.url_key).isdisjoint(test.url_key), "Overlapping URLs."
    return (train.reset_index(drop=True), test.reset_index(drop=True),
            pd.DataFrame(ledger), excluded)


# ---------------------------------------------------------------- C3 data audit
print("\n[C3] loading partitions ...")
sys.stdout.flush()
t0 = time.perf_counter()
tr_raw, tr_manifest = load_partition(DATA_DIR, "train", TRAIN_SHARDS)
te_raw, te_manifest = load_partition(DATA_DIR, "test", TEST_SHARDS)
print(f"  loaded train={len(tr_raw)} test={len(te_raw)} in {time.perf_counter()-t0:.1f}s")
(OUT / "input_manifest.json").write_text(
    json.dumps(tr_manifest + te_manifest, indent=2), encoding="utf-8")

print("[C3] purging the seam and duplicate URLs ...")
sys.stdout.flush()
train, test, ledger, excluded = prepare_temporal(tr_raw, te_raw, CUTOFF)
ledger.to_csv(OUT / "row_ledger.csv", index=False)
excluded.to_csv(OUT / "excluded_rows.csv", index=False)
if UNPARSEABLE_LOG:
    pd.DataFrame(UNPARSEABLE_LOG).to_csv(OUT / "unparseable_urls.csv", index=False)
print(ledger.to_string(index=False))
print(f"Unparseable rows excluded: {len(UNPARSEABLE_LOG)} "
      f"(policy={UNPARSEABLE_POLICY}, cap={UNPARSEABLE_MAX_SHARE:.6%} per partition).")
print("Sizes after cleaning are new results; do not copy raw sizes into the results table.")
del tr_raw, te_raw
sys.stdout.flush()


# ------------------------------------------------------- C4 deterministic features
print("\n[C4] extracting deterministic URL features ...")
sys.stdout.flush()

EXT = tldextract.TLDExtract(suffix_list_urls=(), include_psl_private_domains=False)
SPEC = re.compile(r"[^A-Za-z0-9]")


@lru_cache(maxsize=None)
def host_parts(host):
    try:
        ipaddress.ip_address(host)
        return host, "", "", True
    except ValueError:
        e = EXT(host)
        reg = e.domain + "." + e.suffix if e.suffix else (e.domain or host)
        return reg, e.subdomain or "", e.suffix or "", False


def url_features(u):
    u = u.strip()
    p, host = parse_url(u)
    reg, sub, suffix, is_ip = host_parts(host)
    length = len(u) or 1
    letters = sum(c.isalpha() for c in u)
    digits = sum(c.isdigit() for c in u)
    obfuscated = len(re.findall(r"%[0-9A-Fa-f]{2}", u))
    special = len(SPEC.findall(u))
    return {"URLLength": length, "DomainLength": len(reg), "TLDLength": len(suffix),
            "NoOfSubDomain": len([s for s in sub.split(".") if s]),
            "NoOfObfuscatedChar": obfuscated, "ObfuscationRatio": obfuscated / length,
            "NoOfLettersInURL": letters, "LetterRatioInURL": letters / length,
            "NoOfDegitsInURL": digits, "DegitRatioInURL": digits / length,
            "NoOfEqualsInURL": u.count("="), "NoOfQMarkInURL": u.count("?"),
            "NoOfAmpersandInURL": u.count("&"), "NoOfOtherSpecialCharsInURL": special,
            "SpacialCharRatioInURL": special / length, "IsHTTPS": int(p.scheme.lower() == "https"),
            "HasObfuscation": int(obfuscated > 0), "IsDomainIP": int(is_ip)}


def domain_for(u):
    _, host = parse_url(u)
    return host_parts(host)[0]


t0 = time.perf_counter()
Xtrain = pd.DataFrame([url_features(u) for u in train.url], dtype="float32")
train_extract_s = time.perf_counter() - t0
print(f"  train features {Xtrain.shape} in {train_extract_s:.1f}s")
sys.stdout.flush()
t0 = time.perf_counter()
Xtest = pd.DataFrame([url_features(u) for u in test.url], dtype="float32")
test_extract_s = time.perf_counter() - t0
print(f"  test features {Xtest.shape} in {test_extract_s:.1f}s")

assert list(Xtrain.columns) == list(Xtest.columns)
assert "TLDLegitimateProb" not in Xtrain
assert np.isfinite(Xtrain.to_numpy()).all() and np.isfinite(Xtest.to_numpy()).all()

train["domain"] = train.url.map(domain_for)
test["domain"] = test.url.map(domain_for)
test["domain_seen"] = test.domain.isin(set(train.domain))

for part, df in [("train", train), ("test", test)]:
    export = df[["row_id", "date", "y_phish", "domain"]].copy()
    export["url_sha256"] = df.url_key.map(lambda u: hashlib.sha256(u.encode()).hexdigest())
    if part == "test":
        export["domain_seen"] = df.domain_seen
    export.to_csv(OUT / f"split_{part}.csv.gz", index=False)

exposure = test.groupby("y_phish").domain_seen.agg(["size", "sum", "mean"]).reset_index()
exposure.to_csv(OUT / "actual_test_domain_exposure.csv", index=False)
(OUT / "feature_schema.json").write_text(json.dumps(dict(
    names=list(Xtrain.columns), count=len(Xtrain.columns),
    source="deterministic URL-only; no target encoding",
    semantics="New extractor; not asserted identical to PhiUSIIL precomputed columns",
    train_extract_s=train_extract_s, test_extract_s=test_extract_s), indent=2), encoding="utf-8")
print("Features:", len(Xtrain.columns))
print(exposure.to_string(index=False))
print("Exposure above uses training domains, not corpus-wide domain frequency.")
sys.stdout.flush()


# ------------------------------------------------------------- C5 fitting per seed
print("\n[C5] fitting per seed ...")
sys.stdout.flush()


def metrics(y, prob):
    y = np.asarray(y)
    prob = np.asarray(prob)
    if not len(y):
        return {"n": 0}
    pred = (prob >= THRESHOLD).astype("int8")
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    both = len(np.unique(y)) == 2
    return dict(n=len(y), n_benign=int(tn + fp), n_phish=int(tp + fn),
                tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp),
                prevalence=float(y.mean()), f1_phish=f1_score(y, pred, zero_division=0),
                precision_phish=precision_score(y, pred, zero_division=0),
                recall_phish=recall_score(y, pred, zero_division=0),
                fpr_benign=float(fp / (tn + fp)) if tn + fp else np.nan,
                miss_phish=float(fn / (tp + fn)) if tp + fn else np.nan,
                roc_auc=roc_auc_score(y, prob) if both else np.nan,
                average_precision=average_precision_score(y, prob) if both else np.nan,
                mcc=matthews_corrcoef(y, pred) if both else np.nan)


results = []
for seed in SEEDS:
    model = lgb.LGBMClassifier(**MODEL_PARAMS, random_state=seed)
    t0 = time.perf_counter()
    model.fit(Xtrain, train.y_phish)
    fit_s = time.perf_counter() - t0
    phish_column = int(np.flatnonzero(model.classes_ == 1)[0])
    t0 = time.perf_counter()
    prob = model.predict_proba(Xtest)[:, phish_column]
    prediction_s = time.perf_counter() - t0
    prediction_ms_per_row = prediction_s / len(test) * 1000
    model.booster_.save_model(str(OUT / f"model_seed_{seed}.txt"))
    predfile = test[["row_id", "date", "y_phish", "domain", "domain_seen"]].copy()
    predfile["p_phish"] = prob
    predfile.to_csv(OUT / f"predictions_seed_{seed}.csv.gz", index=False)
    for stratum, mask in [("all", np.ones(len(test), dtype=bool)),
                          ("seen_domain", test.domain_seen.to_numpy()),
                          ("unseen_domain", ~test.domain_seen.to_numpy())]:
        r = dict(seed=seed, stratum=stratum,
                 **metrics(test.y_phish.to_numpy()[mask], prob[mask]))
        # Time is for the whole batch, not attributed to a subset.
        if stratum == "all":
            r.update(fit_s=fit_s, batch_predict_s=prediction_s,
                     amortized_predict_ms_per_row=prediction_ms_per_row)
        results.append(r)
    pd.DataFrame(results).to_csv(OUT / "results_per_seed.csv", index=False)
    (OUT / f"model_params_seed_{seed}.json").write_text(
        json.dumps(model.get_params(), indent=2, default=str), encoding="utf-8")
    print("Finished seed", seed, "fit_s=", round(fit_s, 2))
    sys.stdout.flush()

R = pd.DataFrame(results)
summary = R.groupby("stratum")[["f1_phish", "precision_phish", "recall_phish",
                                "fpr_benign", "miss_phish", "roc_auc",
                                "average_precision", "mcc"]].agg(
    ["mean", "std", "min", "max"])
summary.to_csv(OUT / "seed_variation.csv")
print(summary.to_string())
print("Between-seed SD is not cross-period uncertainty. Do not call it a temporal CI.")
sys.stdout.flush()


# ------------------------------------------------------- C6 domain cluster bootstrap
print("\n[C6] domain-cluster bootstrap on the primary seed ...")
sys.stdout.flush()


def rates_from_confusion(c):
    tn, fp, fn, tp = map(float, c)

    def div(a, b):
        return a / b if b else np.nan

    return {"f1_phish": div(2 * tp, 2 * tp + fp + fn), "precision_phish": div(tp, tp + fp),
            "recall_phish": div(tp, tp + fn), "fpr_benign": div(fp, fp + tn)}


def cluster_bootstrap(frame, reps, seed):
    y = frame.y_phish.to_numpy()
    pred = (frame.p_phish.to_numpy() >= THRESHOLD).astype(int)
    c = pd.DataFrame({"domain": frame.domain.to_numpy(),
                      "tn": ((y == 0) & (pred == 0)).astype(int),
                      "fp": ((y == 0) & (pred == 1)).astype(int),
                      "fn": ((y == 1) & (pred == 0)).astype(int),
                      "tp": ((y == 1) & (pred == 1)).astype(int)})
    counts = c.groupby("domain")[["tn", "fp", "fn", "tp"]].sum().to_numpy()
    if len(counts) < 2:
        raise ValueError("Too few domains for a cluster bootstrap.")
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(reps):
        idx = rng.integers(0, len(counts), size=len(counts))
        samples.append(rates_from_confusion(counts[idx].sum(axis=0)))
    B = pd.DataFrame(samples)
    point = rates_from_confusion(counts.sum(axis=0))
    return pd.DataFrame([dict(metric=k, estimate=v, lower95=B[k].quantile(.025),
                              upper95=B[k].quantile(.975),
                              valid_replicates=int(B[k].notna().sum()))
                         for k, v in point.items()])


primary = pd.read_csv(OUT / f"predictions_seed_{PRIMARY_SEED}.csv.gz")
ci = cluster_bootstrap(primary, BOOTSTRAP_REPLICATES, PRIMARY_SEED)
ci.to_csv(OUT / "cluster_bootstrap_primary_seed.csv", index=False)
primary["month"] = pd.to_datetime(primary.date, utc=True).dt.strftime("%Y-%m")
monthly = []
for month, frame in primary.groupby("month"):
    monthly.append(dict(month=month, seed=PRIMARY_SEED, **metrics(frame.y_phish, frame.p_phish)))
pd.DataFrame(monthly).to_csv(OUT / "monthly_descriptive_primary_seed.csv", index=False)

files = [dict(file=p.name, sha256=file_sha256(p), bytes=p.stat().st_size)
         for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "output_manifest.json"]
(OUT / "output_manifest.json").write_text(json.dumps(files, indent=2), encoding="utf-8")

print(ci.to_string(index=False))
print("CI is a domain resampling on one test period and one fixed model; "
      "it is not a guarantee of temporal generalisation.")
print("Done. Review row_ledger.csv, results_per_seed.csv, "
      "cluster_bootstrap_primary_seed.csv, actual_test_domain_exposure.csv, "
      "design.json, feature_schema.json and both manifests.")
