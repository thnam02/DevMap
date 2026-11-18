"""Confidence intervals, effect sizes and paired tests for the paper's comparisons, from the result files only.

  python research/v2/paper_stats.py            -> research/v2/results/paper_stats.md

1. Main benchmark (the 650 changes of report-all.md, scored with the report's filter pipeline._confirmed): changes
   with a missed failure per selector (Wilson 95% CI), paired exact McNemar Proviso vs each other selector and vs the
   'traditional' ablation (odds ratio of the discordant pairs with an exact CI).
2. Main benchmark test-time share: paired Wilcoxon signed-rank, median of the paired differences with a bootstrap 95%
   CI (10,000 resamples, seed 0), matched-pairs rank-biserial correlation.
3. SWE-bench agent regressions: the pairing of swe_eval_namerts.summary (both tools ran, regression reproduced);
   detection (McNemar), time share (Wilcoxon, rank-biserial, bootstrap CI); full-suite share of broken tests missed
   with a case-level cluster bootstrap CI.
4. Finish-check pilot: paired check time (replay_report.py's rules: last row per task/arm/rep, status ok).
Published figures are printed beside the computed ones; nothing is adjusted to match."""
from __future__ import annotations

import collections
import json
import math
import os
import statistics
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import pipeline as PL  # noqa: E402

REPOS = ["sqlglot", "sympy", "sqlalchemy", "pygments", "datasette"]
OTHERS = ["testmon", "namerts", "tdad"]
RNG_SEED, BOOT = 0, 10_000


# ------------------------------------------------------------------------------------------------- statistics

def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"),) * 2
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def mcnemar(b, c):
    """Exact two-sided McNemar p (binomial on the discordant pairs) and the conditional odds ratio b/c with an exact
    95% CI from the Clopper-Pearson interval of b/(b+c)."""
    n = b + c
    if n == 0:
        return 1.0, float("nan"), (float("nan"), float("nan"))
    p = stats.binomtest(b, n, 0.5).pvalue
    lo = stats.beta.ppf(0.025, b, c + 1) if b > 0 else 0.0
    hi = stats.beta.ppf(0.975, b + 1, c) if c > 0 else 1.0
    tr = lambda q: q / (1 - q) if q < 1 else float("inf")  # noqa: E731
    return p, (b / c if c else float("inf")), (tr(lo), tr(hi))


def wilcoxon(x, y):
    """Wilcoxon signed-rank on paired x - y (zero differences dropped, as replay_report and the SWE comparison did),
    with the matched-pairs rank-biserial correlation (positive: x larger)."""
    d = np.asarray(x, float) - np.asarray(y, float)
    d = d[d != 0]
    if len(d) == 0:
        return float("nan"), float("nan"), 0
    p = stats.wilcoxon(d).pvalue
    r = stats.rankdata(np.abs(d))
    wp, wm = r[d > 0].sum(), r[d < 0].sum()
    return p, (wp - wm) / (wp + wm), len(d)


def boot_median_diff(x, y, seed=RNG_SEED):
    d = np.asarray(x, float) - np.asarray(y, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(BOOT, len(d)))
    meds = np.median(d[idx], axis=1)
    return float(np.median(d)), (float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5)))


def boot_ratio(num, den, seed=RNG_SEED):
    """Cluster bootstrap (resampling cases) of sum(num)/sum(den)."""
    num, den = np.asarray(num, float), np.asarray(den, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(num), size=(BOOT, len(num)))
    r = num[idx].sum(1) / den[idx].sum(1)
    return float(num.sum() / den.sum()), (float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5)))


def boot_mean_diff(x, y, seed=RNG_SEED):
    d = np.asarray(x, float) - np.asarray(y, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(BOOT, len(d)))
    m = d[idx].mean(1)
    return float(d.mean()), (float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))


def pct(x):
    return f"{100 * x:.1f}%"


def pfmt(p):
    return f"{p:.2g}" if p < 0.001 else f"{p:.3f}"


# ------------------------------------------------------------------------------------------------- 1, 2 main

def main_rows():
    out = []
    for repo in REPOS:
        PL.use(repo)
        trad = PL.merged("ablate-traditional")
        for stage in ("select", "realeval"):
            rows = list(PL.merged(stage).values())
            if stage == "realeval":
                ids = {r["id"] for r in PL.real_set()}
                rows = [r for r in rows if r["id"] in ids]
            rows = [{**r, "selectors": {**r["selectors"], **({"traditional": trad[f"{stage}:{r['id']}"]["proviso"]}
                                                           if f"{stage}:{r['id']}" in trad else {})}} for r in rows]
            for r in PL._confirmed(rows, stage):
                out.append({"repo": repo, "stage": stage, **r})
    return out


def ok(r, k):
    s = r["selectors"].get(k)
    return s is not None and "error" not in s and "missed" in s


def section_main(lines):
    rows = main_rows()
    brk = [r for r in rows if r["truth"]]
    lines += [f"## 1. Main benchmark: changes with a missed failure ({len(rows)} changes, {len(brk)} break tests)", "",
              "| Selector | Changes scored | Breaking changes | With a missed failure | Share of breaking changes "
              "(95% Wilson CI) |", "|---|---|---|---|---|"]
    for k in ["proviso", *OTHERS, "traditional"]:
        have = [r for r in rows if ok(r, k)]
        hb = [r for r in have if r["truth"]]
        m = sum(1 for r in hb if r["selectors"][k]["missed"])
        lo, hi = wilson(m, len(hb))
        lines.append(f"| {k} | {len(have)} | {len(hb)} | {m} | {pct(m / len(hb))} ({pct(lo)}–{pct(hi)}) |")
    tp = [r for r in brk if r["stage"] == "select" and ok(r, "tdad")]
    tm = sum(1 for r in tp if r["selectors"]["tdad"]["missed"])
    tl, th = wilson(tm, len(tp))
    lines += ["", f"TDAD on planted bugs only: {tm} of {len(tp)} breaking changes with a missed failure ({pct(tm / len(tp))}, "
              f"{pct(tl)}–{pct(th)}). TDAD is not run on sympy.",
              "", "Published (report-all.md): Proviso 10, testmon 64, NameRTS 171; traditional 6 (v23_changes.md); TDAD "
              "229 of 236 planted bugs (97%).", "",
              "Paired, on breaking changes both selectors scored (b: only Proviso misses, c: only the other misses):", "",
              "| Proviso vs | Pairs | b | c | McNemar exact p | Odds ratio b/c (95% CI) |", "|---|---|---|---|---|---|"]
    for k in [*OTHERS, "traditional"]:
        pr = [r for r in brk if ok(r, "proviso") and ok(r, k)]
        b = sum(1 for r in pr if r["selectors"]["proviso"]["missed"] and not r["selectors"][k]["missed"])
        c = sum(1 for r in pr if r["selectors"][k]["missed"] and not r["selectors"]["proviso"]["missed"])
        p, orr, (lo, hi) = mcnemar(b, c)
        lines.append(f"| {k} | {len(pr)} | {b} | {c} | {pfmt(p)} | {orr:.3g} ({lo:.3g}–{hi:.3g}) |")
    lines += ["", "## 2. Main benchmark: share of test time (all changes both selectors scored)", "",
              "| Proviso vs | Pairs | Median Proviso / other | Median paired difference, Proviso − other (95% bootstrap CI) | "
              "Mean paired difference (95% bootstrap CI) | Wilcoxon p | Rank-biserial r |", "|---|---|---|---|---|---|---|"]
    for k in [*OTHERS, "traditional"]:
        pr = [r for r in rows if ok(r, "proviso") and ok(r, k) and "time_share" in r["selectors"][k]]
        x = [r["selectors"]["proviso"]["time_share"] for r in pr]
        y = [r["selectors"][k]["time_share"] for r in pr]
        p, rb, n = wilcoxon(x, y)
        md, (lo, hi) = boot_median_diff(x, y)
        mn, (ml, mh) = boot_mean_diff(x, y)
        lines.append(f"| {k} | {len(pr)} | {pct(statistics.median(x))} / {pct(statistics.median(y))} | "
                     f"{100 * md:+.1f} pts ({100 * lo:+.1f} to {100 * hi:+.1f}) | {100 * mn:+.1f} pts "
                     f"({100 * ml:+.1f} to {100 * mh:+.1f}) | {pfmt(p)} | {rb:+.2f} |")
    lines += ["", "Rank-biserial r: −1 = Proviso always cheaper, +1 = always dearer; zero differences left out.", ""]


# ------------------------------------------------------------------------------------------------- 3 SWE-bench

def section_swe(lines):
    sys.path.insert(0, HERE)
    import swe_eval as E
    out = os.path.join(HERE, "results", "swe")
    prov = {}
    for line in open(os.path.join(out, "eval-v2.3.jsonl")):
        r = json.loads(line)
        if r.get("format") == E.EVAL_FORMAT and "error" not in r:
            prov[(r["instance"], r["case"])] = r
    nr = {}
    for line in open(os.path.join(out, "eval_namerts.jsonl")):
        r = json.loads(line)
        nr[(r["instance"], r["case"])] = r
    both = [(prov[k], nr[k]) for k in nr if "error" not in nr[k] and k in prov and prov[k].get("reproduced")]
    undet = lambda r: bool(r["missed"]) and len(r["missed"]) >= len(r["reproduced"])  # noqa: E731
    n = len(both)
    dp, dn = sum(1 for p, _ in both if not undet(p)), sum(1 for _, q in both if not undet(q))
    b = sum(1 for p, q in both if undet(p) and not undet(q))
    c = sum(1 for p, q in both if undet(q) and not undet(p))
    pm, orr, _ = mcnemar(b, c)
    x = [p["time_share"] for p, _ in both]
    y = [q["time_share"] for _, q in both]
    pw, rb, nz = wilcoxon(x, y)
    md, (lo, hi) = boot_median_diff(x, y)
    cheaper = sum(1 for a, bb in zip(x, y) if a < bb)
    dearer = sum(1 for a, bb in zip(x, y) if a > bb)
    all_rep = [r for r in prov.values() if r.get("reproduced")]
    det_all = sum(1 for r in all_rep if not undet(r))
    l1, h1 = wilson(dp, n)
    l2, h2 = wilson(dn, n)
    l3, h3 = wilson(det_all, len(all_rep))
    lines += ["## 3. SWE-bench agent regressions", "",
              f"All reproduced regressions (Proviso alone): {det_all} of {len(all_rep)} detected "
              f"({pct(det_all / len(all_rep))}; 95% Wilson CI {pct(l3)}–{pct(h3)}). Published: 342 of 342.", "",
              f"Paired with NameRTS ({n} regressions where both ran; published 221):", "",
              f"- Detected: Proviso {dp} ({pct(l1)}–{pct(h1)}), NameRTS {dn} ({pct(l2)}–{pct(h2)}); discordant b = {b} "
              f"(only Proviso undetected), c = {c}; McNemar exact p = {pfmt(pm)}. Published: 221 vs 215, p = 0.031.",
              f"- Time share: median {pct(statistics.median(x))} vs {pct(statistics.median(y))} (published 39.2% vs "
              f"60.2%); median paired difference {100 * md:+.1f} pts (95% bootstrap CI {100 * lo:+.1f} to "
              f"{100 * hi:+.1f}); Wilcoxon p = {pfmt(pw)} on {nz} non-zero pairs (published 1.1e-7); rank-biserial r = "
              f"{rb:+.2f}; Proviso cheaper in {cheaper}, dearer in {dearer} (published 147 / 71).", ""]
    fs = [json.loads(l) for l in open(os.path.join(out, "fullsuite-v2.3.jsonl"))]
    fs = [r for r in fs if r.get("truth")]
    tot = [len(r["truth"]) for r in fs]
    pm_ = [len(r["proviso_missed"]) for r in fs]
    ran = [r for r in fs if r.get("namerts_missed") is not None and r.get("namerts_files") is not None]
    nm_ = [len(r["namerts_missed"]) for r in ran]
    ntot = [len(r["truth"]) for r in ran]
    s1, (a1, z1) = boot_ratio(pm_, tot)
    s2, (a2, z2) = boot_ratio(nm_, ntot)
    lines += [f"Full-suite ground truth (held-out, no sympy; {len(fs)} cases with broken tests, {sum(tot):,} broken "
              f"tests; NameRTS ran on {len(ran)}):", "",
              f"- Broken tests missed: Proviso {sum(pm_):,} = {pct(s1)} (95% case-bootstrap CI {pct(a1)}–{pct(z1)}); "
              f"NameRTS {sum(nm_):,} of {sum(ntot):,} = {pct(s2)} ({pct(a2)}–{pct(z2)}). Published: 1,717 (1.5%) vs "
              f"58,408 (50.3%) of 116,103.",
              "- The CIs are wide because the broken tests cluster in a few cases (one xarray patch breaks ~11,700).", ""]


# ------------------------------------------------------------------------------------------------- 4 finish check

def section_gate(lines):
    lines += ["## 4. Finish-check pilot (20 replay cases, check time per run)", "",
              "| Model | Pairs | Total check time Proviso / full | Median Proviso / full | Median paired difference "
              "(95% bootstrap CI) | Wilcoxon p | Rank-biserial r | Published |", "|---|---|---|---|---|---|---|---|"]
    pub = {"results-gate": "Sonnet 2046 vs 3087 s, p = 0.07", "results-gate-haiku": "Haiku 1407 vs 3144 s, p = 0.001"}
    for d, model in (("results-gate", "Sonnet"), ("results-gate-haiku", "Haiku")):
        rows = {}
        for line in open(os.path.join(ROOT, "research", "agent", d, "results.jsonl")):
            if line.strip():
                r = json.loads(line)
                rows[(r.get("task"), str(r.get("arm")), str(r.get("rep")))] = r
        per = collections.defaultdict(dict)
        for (task, arm, rep), r in rows.items():
            if r.get("status") == "ok":
                per[(task, rep)][arm] = r.get("proviso_gate_secs") or 0.0
        pr = [(v["gate-proviso"], v["gate-full"]) for v in per.values() if "gate-proviso" in v and "gate-full" in v]
        x, y = [a for a, _ in pr], [b for _, b in pr]
        p, rb, n = wilcoxon(x, y)
        md, (lo, hi) = boot_median_diff(x, y)
        lines.append(f"| {model} | {len(pr)} | {sum(x):.0f} / {sum(y):.0f} s | {statistics.median(x):.0f} / "
                     f"{statistics.median(y):.0f} s | {md:+.0f} s ({lo:+.0f} to {hi:+.0f}) | {pfmt(p)} | {rb:+.2f} | "
                     f"{pub[d]} |")
    lines += ["", "With 20 pairs the CIs are wide; the pilot supports 'cheaper on Haiku', not a precise saving.", ""]


def main():
    lines = ["# Paper statistics: confidence intervals and effect sizes", "",
             "Generated by research/v2/paper_stats.py from the result files (no tests run). Wilson intervals for "
             "proportions; exact McNemar on discordant pairs; Wilcoxon signed-rank with zero differences dropped; "
             f"bootstrap {BOOT:,} resamples, seed {RNG_SEED}.", ""]
    section_main(lines)
    section_swe(lines)
    section_gate(lines)
    text = "\n".join(lines)
    open(os.path.join(HERE, "results", "paper_stats.md"), "w").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
