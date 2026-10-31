"""Run two independent reviewers on the v10 candidate with distinct model IDs.

Reviewer A: gpt-6-luna   (Kenari)
Reviewer B: glm-5-3      (Kenari)

Both receive byte-identical packets and run in separate calls with no shared state.
Writes 06_self_qa/dual_review/<model>_review.md, <model>_raw.json, and VERDICTS.json
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from pathlib import Path

BASE = "https://kenari.id/v1/chat/completions"
KEY = os.environ.get("KENARI_API_KEY", "")
HERE = Path(r"E:\Kuliah\Tugas Akhir\phishing\revision_v10_p1\06_self_qa\dual_review")
TEXT = (HERE / "MANUSCRIPT_TEXT.txt").read_text(encoding="utf8")

MODELS = ["gpt-6-luna", "glm-5-3-flash"]

SYSTEM = (
    "You are an independent, adversarial peer reviewer for an Indonesian journal in the "
    "SINTA-2 class (national accreditation rank 2). You have NOT seen any earlier review of "
    "this manuscript and you must judge only the text supplied. Your job is to find what would "
    "cause rejection, not to encourage the authors. A rubber-stamp review is a failed review. "
    "Never invent facts that are not in the text; if something cannot be verified from the "
    "manuscript alone, write UNVERIFIABLE."
)

INSTRUCTIONS = """Review the manuscript below and return a structured verdict.

CONTEXT YOU MAY USE
- This is the P1 revision of an empirical/technical paper on phishing-URL detection generalisation.
- It compares two corpora (PhiUSIIL, PhreshPhish) across: random vs domain-disjoint splitting,
  feature-group ablation, within-corpus temporal evaluation, frozen one-direction zero-shot
  transfer, validation-selected operating thresholds, and a descriptive error taxonomy.
- The paper explicitly does not propose a new model and does not claim state of the art.
- The manuscript is in Indonesian; the title, abstract and keywords are bilingual.

READING NOTES FOR THIS EXTRACTION (apply to both reviewers equally)
- The manuscript file contains two embedded raster figures: Figure 1 (research pipeline diagram,
  860x820) and Figure 2 (two metric panels). Their captions appear inline; the images themselves are
  not reproduced in this plain-text extraction. Do not score their absence as a missing figure.
- Tables are rendered as pipe-separated rows, with the header row first. Before concluding that a
  number is unsupported, check every table's column headers and the paragraph that introduces it.
- Paragraph identifiers [Pnnn] are stable anchors into the document body; tables are [TABLE n].

EVALUATE EXACTLY THESE CRITERIA. For each, start the line with the criterion id, then PASS or BLOCK,
then 2-4 sentences of justification, then "Evidence:" with a paragraph id ([Pnnn]) or a short quote.

C1 Claim-evidence consistency. Is every quantitative claim traceable to a table or figure in the
   text? Do any two numbers contradict each other? Are denominators, units and rounding coherent?
C2 Boundary discipline. Check that the text does NOT claim: a new model or state of the art;
   a causal mechanism for benchmark saturation; blind, prospective or untouched evaluation;
   proof of leakage; universal generalisation from two corpora; deployment readiness or a
   production FPR guarantee. Quote any sentence that crosses a boundary.
C3 Preserved corrections. Verify these specific statements are present and correct:
   (a) source polarity legitimate=1 / phishing=0 for PhiUSIIL, and the analysis mapping
   legitimate=0 / phishing=1; (b) legacy E3 metrics are not used as phishing-positive metrics;
   (c) bootstrap RNG seed 42 is distinguished from model seed 13; (d) the platform-cluster
   interval is absent and cluster uncertainty is labelled unverified; (e) the 37.1% platform
   share is descriptive only; (f) 85 is described as selected reported fits, not all fits;
   (g) A0/A1 producer provenance is stated as unknown; (h) A2 is a contract, not a claim of
   value equality with stored columns; (i) strict no-overlap scoring is a sensitivity analysis.
C4 Literature use. Is each citation attached to a sentence it can actually support, or are any
   decorative? Are comparative claims bounded? Name any obviously missing near-neighbour topic
   that a reviewer would demand, but do not invent specific papers unless you are certain they exist.
C5 Novelty framing. Is the contribution stated as an integrated, evidence-bounded evaluation
   chain rather than model superiority? Is the claim defensible against the nearest cited work?
C6 Internal consistency and presentation. Table and figure numbering, cross-references, reference
   list completeness, terminology consistency, Indonesian/English abstract agreement, and whether
   any section is missing what a SINTA-2 reviewer expects (method detail, limitations, ethics,
   availability statement).
C7 Rejection risk. Give the five highest-risk issues in priority order. For each: severity
   (High/Medium/Low), what is wrong, where it is ([Pnnn]), and the smallest concrete fix.

END WITH EXACTLY ONE LINE:
OVERALL: APPROVE
or
OVERALL: BLOCK

Choose BLOCK if any of C1-C6 is BLOCK, or if any High-severity issue in C7 would plausibly cause
rejection without further revision.

MANUSCRIPT TEXT FOLLOWS.
=====================================================================

"""


def call(model: str, packet: str) -> dict:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": packet},
        ],
        "temperature": 0.2,
        "max_tokens": 8000,
    }
    req = urllib.request.Request(
        BASE,
        data=json.dumps(body).encode("utf8"),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf8", "ignore")[:800]
        raise RuntimeError(f"HTTP {e.code}: {detail}") from e


def main() -> int:
    packet = INSTRUCTIONS + TEXT
    verdicts = {}
    for model in MODELS:
        slug = model.replace(".", "-")
        out_md = HERE / f"{slug}_review.md"
        out_raw = HERE / f"{slug}_raw.json"
        print(f"--- calling {model} ...")
        t0 = time.time()
        try:
            raw = call(model, packet)
        except Exception as e:
            print(f"{model} ERROR: {type(e).__name__}: {e}")
            verdicts[model] = {"status": "ERROR", "error": f"{type(e).__name__}: {e}"}
            continue
        elapsed = round(time.time() - t0, 1)
        try:
            content = raw["choices"][0]["message"]["content"]
        except Exception:
            content = json.dumps(raw)[:2000]
            verdicts[model] = {"status": "BAD_RESPONSE"}
        usage = raw.get("usage", {})
        out_raw.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf8")
        out_md.write_text(content, encoding="utf8")
        m = re.search(r"OVERALL:\s*(APPROVE|BLOCK)", content, re.I)
        blocks = re.findall(r"^(C[1-7])\s*:?\s*(PASS|BLOCK)", content, re.I | re.M)
        verdicts[model] = {
            "status": "OK",
            "elapsed_s": elapsed,
            "usage": usage,
            "overall": m.group(1).upper() if m else "UNPARSED",
            "criteria": {c.upper(): v.upper() for c, v in blocks},
            "chars": len(content),
        }
        print(f"    {verdicts[model]}")

    (HERE / "VERDICTS.json").write_text(json.dumps(verdicts, indent=2), encoding="utf8")

    ok = all(v.get("status") == "OK" and v.get("overall") in ("APPROVE", "BLOCK") for v in verdicts.values())
    gate = "PASS" if ok and all(v["overall"] == "APPROVE" for v in verdicts.values()) else "BLOCK"
    print("\nGATE:", gate)
    print(json.dumps(verdicts, indent=2))
    return 0 if gate == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())