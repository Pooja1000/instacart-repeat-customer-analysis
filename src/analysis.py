"""
analysis.py — Phase 2: Descriptive analysis, logistic regression, charts.

Reads user_features.parquet and reorder_curve.parquet (produced by Phase 1).
Writes charts to results/figures/ and updates results/results.json.

Usage: python src/analysis.py
"""

import json
import os
import sys
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import yaml
from scipy import stats
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm

import sys

warnings.filterwarnings("ignore", category=FutureWarning)

def flush_print(*args, **kwargs):
    """Print and flush immediately so logs show progress."""
    print(*args, **kwargs, flush=True)

# ── Paths ─────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.yaml")
RESULTS_JSON = os.path.join(PROJECT_ROOT, "results", "results.json")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "results", "figures")
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

os.makedirs(FIGURES_DIR, exist_ok=True)

# ── Load config ───────────────────────────────────────────────
with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)

SEED = cfg["random_seed"]
N_BOOT = cfg["stats"]["bootstrap_iterations"]
CONF_LEVEL = cfg["stats"]["confidence_level"]
MIN_D = cfg["stats"]["min_effect_size"]["cohens_d"]
OR_LO = cfg["stats"]["min_effect_size"]["odds_ratio_lower"]
OR_HI = cfg["stats"]["min_effect_size"]["odds_ratio_upper"]
CV_FOLDS = cfg["stats"]["cross_validation_folds"]
np.random.seed(SEED)

# ── Load data ─────────────────────────────────────────────────
df = pd.read_parquet(os.path.join(DATA_DIR, "user_features.parquet"))
reorder_curve = pd.read_parquet(os.path.join(DATA_DIR, "reorder_curve.parquet"))

# Load existing results
with open(RESULTS_JSON) as f:
    results = json.load(f)

print(f"Loaded {len(df):,} users, {len(reorder_curve)} reorder curve rows.")

# ── Feature lists ─────────────────────────────────────────────
# Features WITHOUT gap features (lead model)
FEATURES_NO_GAP = [
    "first_order_size",
    "avg_basket_size_1_3",
    "reorder_rate_2_3",
    "busiest_days_share_1_3",
    "morning_share_1_3",
    "evening_share_1_3",
    "pct_produce_order1",
    "pct_dairy_order1",
    "pct_snacks_order1",
    "n_departments_order1",
    "n_aisles_order1",
]

# Features WITH gap features (secondary model)
FEATURES_WITH_GAP = FEATURES_NO_GAP + [
    "days_to_second_order",
    "days_to_third_order",
]

FEATURE_LABELS = {
    "first_order_size": "First order size",
    "avg_basket_size_1_3": "Avg basket size (orders 1–3)",
    "reorder_rate_2_3": "Reorder rate (orders 2–3)",
    "days_to_second_order": "Days to 2nd order",
    "days_to_third_order": "Days to 3rd order",
    "busiest_days_share_1_3": "Busiest-days share",
    "morning_share_1_3": "Morning share",
    "evening_share_1_3": "Evening share",
    "pct_produce_order1": "% produce (1st order)",
    "pct_dairy_order1": "% dairy (1st order)",
    "pct_snacks_order1": "% snacks (1st order)",
    "n_departments_order1": "Depts in 1st order",
    "n_aisles_order1": "Aisles in 1st order",
}

PRIMARY_OUTCOME = "is_heavy_p75"


# ══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════

def bootstrap_ci(data, stat_fn=np.mean, n_boot=N_BOOT, seed=SEED, ci=CONF_LEVEL):
    """Bootstrap confidence interval for a statistic (batched vectorisation).

    Processes in batches of 500 to avoid allocating huge arrays when n is large.
    """
    rng = np.random.RandomState(seed)
    data = np.asarray(data, dtype=float)
    data = data[~np.isnan(data)]
    n = len(data)
    batch_size = 500
    boot_stats = []
    for start in range(0, n_boot, batch_size):
        b = min(batch_size, n_boot - start)
        indices = rng.randint(0, n, size=(b, n))
        boot_samples = data[indices]
        if stat_fn is np.mean:
            boot_stats.append(boot_samples.mean(axis=1))
        elif stat_fn is np.median:
            boot_stats.append(np.median(boot_samples, axis=1))
        else:
            boot_stats.append(np.array([stat_fn(row) for row in boot_samples]))
    boot_stats = np.concatenate(boot_stats)
    alpha = (1 - ci) / 2
    lo = np.percentile(boot_stats, alpha * 100)
    hi = np.percentile(boot_stats, (1 - alpha) * 100)
    return stat_fn(data), lo, hi


def cohens_d(group1, group2):
    """Cohen's d effect size."""
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return (np.mean(group1) - np.mean(group2)) / pooled_std


def is_meaningful_d(d):
    """Check if Cohen's d exceeds minimum meaningful threshold."""
    return abs(d) >= MIN_D


def is_meaningful_or(odds_ratio):
    """Check if odds ratio exceeds minimum meaningful threshold."""
    return odds_ratio < OR_LO or odds_ratio > OR_HI


# ══════════════════════════════════════════════════════════════
# 1. OUTCOME DISTRIBUTIONS
# ══════════════════════════════════════════════════════════════
print("\n── 1. Outcome distributions ──")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Total orders distribution
ax = axes[0]
ax.hist(df["total_orders"], bins=50, edgecolor="white", alpha=0.8, color="#4C72B0")
threshold_p75 = df["total_orders"].quantile(0.75)
ax.axvline(threshold_p75, color="#C44E52", linestyle="--", linewidth=2,
           label=f"p75 = {threshold_p75:.0f} orders (heavy-user threshold)")
ax.set_xlabel("Total orders per user")
ax.set_ylabel("Number of users")
ax.set_title("Distribution of total orders per user")
ax.legend(fontsize=9)

# Median gap distribution
ax = axes[1]
ax.hist(df["median_gap_orders_4plus"].dropna(), bins=30, edgecolor="white",
        alpha=0.8, color="#55A868")
ax.axvline(7, color="#C44E52", linestyle="--", linewidth=2,
           label="7 days (fast-cadence threshold)")
ax.set_xlabel("Median days between orders (orders 4+)")
ax.set_ylabel("Number of users")
ax.set_title("Distribution of median inter-order gap")
ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "outcome_distributions.png"), dpi=150,
            bbox_inches="tight")
plt.close()
print("  ✓ outcome_distributions.png")


# ══════════════════════════════════════════════════════════════
# 2. DESCRIPTIVE COMPARISONS: HEAVY vs NON-HEAVY
# ══════════════════════════════════════════════════════════════
print("\n── 2. Heavy vs non-heavy feature comparisons ──")

heavy = df[df[PRIMARY_OUTCOME] == 1]
non_heavy = df[df[PRIMARY_OUTCOME] == 0]
print(f"  Heavy: {len(heavy):,} | Non-heavy: {len(non_heavy):,}")

comparison_results = {}
for feat in FEATURES_WITH_GAP:
    h_data = heavy[feat].dropna().values
    nh_data = non_heavy[feat].dropna().values

    h_mean, h_lo, h_hi = bootstrap_ci(h_data)
    nh_mean, nh_lo, nh_hi = bootstrap_ci(nh_data)
    diff = h_mean - nh_mean
    d = cohens_d(h_data, nh_data)
    meaningful = is_meaningful_d(d)

    comparison_results[feat] = {
        "heavy_mean": round(float(h_mean), 4),
        "heavy_ci": [round(float(h_lo), 4), round(float(h_hi), 4)],
        "non_heavy_mean": round(float(nh_mean), 4),
        "non_heavy_ci": [round(float(nh_lo), 4), round(float(nh_hi), 4)],
        "difference": round(float(diff), 4),
        "cohens_d": round(float(d), 4),
        "practically_meaningful": bool(meaningful),
    }
    flag = "✓" if meaningful else "·"
    print(f"  {flag} {feat}: d={d:.3f}, diff={diff:.3f}")

# Forest-style chart
fig, ax = plt.subplots(figsize=(10, 8))
feats_sorted = sorted(comparison_results.keys(),
                      key=lambda x: abs(comparison_results[x]["cohens_d"]),
                      reverse=True)
y_pos = range(len(feats_sorted))
ds = [comparison_results[f]["cohens_d"] for f in feats_sorted]
colors = ["#C44E52" if abs(d) >= MIN_D else "#CCCCCC" for d in ds]
labels = [FEATURE_LABELS.get(f, f) for f in feats_sorted]

ax.barh(y_pos, ds, color=colors, edgecolor="white", height=0.7)
ax.set_yticks(y_pos)
ax.set_yticklabels(labels)
ax.set_xlabel("Cohen's d (heavy − non-heavy)")
ax.set_title("Feature differences: heavy vs non-heavy users\n"
             f"(red = |d| ≥ {MIN_D}, grey = below threshold)")
ax.axvline(0, color="black", linewidth=0.5)
ax.axvline(MIN_D, color="#C44E52", linewidth=0.5, linestyle=":")
ax.axvline(-MIN_D, color="#C44E52", linewidth=0.5, linestyle=":")
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "heavy_vs_nonheavy_features.png"),
            dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ heavy_vs_nonheavy_features.png")


# ══════════════════════════════════════════════════════════════
# 3. LOGISTIC REGRESSION (two versions)
# ══════════════════════════════════════════════════════════════
print("\n── 3. Logistic regression ──")

def run_logistic(df_in, features, label, results_dict):
    """Fit logistic regression, compute cross-validated AUC, return results."""
    sub = df_in[features + [PRIMARY_OUTCOME]].dropna()
    X = sub[features].values
    y = sub[PRIMARY_OUTCOME].values

    # Standardise
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # VIF check
    vif_data = []
    for i, feat in enumerate(features):
        vif_val = variance_inflation_factor(X_scaled, i)
        vif_data.append({"feature": feat, "vif": round(float(vif_val), 2)})
    print(f"\n  [{label}] VIF check:")
    for v in vif_data:
        flag = "⚠" if v["vif"] > 5 else " "
        print(f"    {flag} {v['feature']}: {v['vif']}")

    # Fit model
    X_const = sm.add_constant(X_scaled)
    model = sm.Logit(y, X_const).fit(disp=0)

    # Odds ratios with CIs
    odds_ratios = {}
    params = model.params[1:]  # skip intercept
    conf = model.conf_int()[1:]
    pvals = model.pvalues[1:]
    for i, feat in enumerate(features):
        or_val = float(np.exp(params[i]))
        or_lo = float(np.exp(conf[i][0]))
        or_hi = float(np.exp(conf[i][1]))
        p = float(pvals[i])
        meaningful = is_meaningful_or(or_val)
        odds_ratios[feat] = {
            "odds_ratio": round(or_val, 4),
            "ci_lower": round(or_lo, 4),
            "ci_upper": round(or_hi, 4),
            "p_value": round(p, 6),
            "practically_meaningful": bool(meaningful),
        }

    # Cross-validated AUC
    from sklearn.linear_model import LogisticRegression
    lr_sk = LogisticRegression(max_iter=1000, random_state=SEED)
    cv_scores = cross_val_score(lr_sk, X_scaled, y, cv=CV_FOLDS,
                                scoring="roc_auc")
    cv_auc_mean = float(cv_scores.mean())
    cv_auc_std = float(cv_scores.std())

    print(f"  [{label}] Cross-validated AUC: {cv_auc_mean:.3f} ± {cv_auc_std:.3f}")
    print(f"  [{label}] Pseudo R²: {model.prsquared:.3f}")

    # Sort odds ratios for printing
    sorted_or = sorted(odds_ratios.items(),
                       key=lambda x: abs(np.log(x[1]["odds_ratio"])),
                       reverse=True)
    print(f"  [{label}] Top odds ratios:")
    for feat, vals in sorted_or[:5]:
        flag = "✓" if vals["practically_meaningful"] else "·"
        print(f"    {flag} {feat}: OR={vals['odds_ratio']:.3f} "
              f"[{vals['ci_lower']:.3f}, {vals['ci_upper']:.3f}]")

    results_dict[label] = {
        "odds_ratios": odds_ratios,
        "cv_auc_mean": round(cv_auc_mean, 4),
        "cv_auc_std": round(cv_auc_std, 4),
        "pseudo_r_squared": round(float(model.prsquared), 4),
        "n_obs": int(len(sub)),
        "vif": vif_data,
    }

    return odds_ratios, features


regression_results = {}

# Model A: WITHOUT gap features (lead model)
or_no_gap, feat_no_gap = run_logistic(
    df, FEATURES_NO_GAP, "without_gap_features", regression_results
)

# Model B: WITH gap features
or_with_gap, feat_with_gap = run_logistic(
    df, FEATURES_WITH_GAP, "with_gap_features", regression_results
)


# ── Odds-ratio chart (lead model: without gaps) ──────────────
def plot_odds_ratios(odds_ratios, features, title, filename):
    """Forest-style odds-ratio chart."""
    fig, ax = plt.subplots(figsize=(10, 7))
    sorted_feats = sorted(features,
                          key=lambda f: abs(np.log(odds_ratios[f]["odds_ratio"])),
                          reverse=True)
    y_pos = range(len(sorted_feats))
    ors = [odds_ratios[f]["odds_ratio"] for f in sorted_feats]
    ci_lo = [odds_ratios[f]["ci_lower"] for f in sorted_feats]
    ci_hi = [odds_ratios[f]["ci_upper"] for f in sorted_feats]
    errors = [[o - l for o, l in zip(ors, ci_lo)],
              [h - o for o, h in zip(ors, ci_hi)]]
    labels = [FEATURE_LABELS.get(f, f) for f in sorted_feats]
    colors = ["#C44E52" if is_meaningful_or(o) else "#CCCCCC" for o in ors]

    ax.errorbar(ors, y_pos, xerr=errors, fmt="o", color="black",
                ecolor="gray", capsize=3, markersize=5)
    for i, (o, c) in enumerate(zip(ors, colors)):
        ax.plot(o, i, "o", color=c, markersize=8, zorder=5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.axvline(1.0, color="black", linewidth=0.5)
    ax.axvline(OR_LO, color="#C44E52", linewidth=0.5, linestyle=":")
    ax.axvline(OR_HI, color="#C44E52", linewidth=0.5, linestyle=":")
    ax.set_xlabel("Odds ratio (standardised, 95% CI)")
    ax.set_title(title)
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, filename), dpi=150,
                bbox_inches="tight")
    plt.close()


plot_odds_ratios(or_no_gap, feat_no_gap,
                 "Odds ratios for heavy-user status\n(without gap features — lead model)",
                 "odds_ratios_no_gap.png")
print("  ✓ odds_ratios_no_gap.png")

plot_odds_ratios(or_with_gap, feat_with_gap,
                 "Odds ratios for heavy-user status\n(with gap features — secondary model)",
                 "odds_ratios_with_gap.png")
print("  ✓ odds_ratios_with_gap.png")


# ══════════════════════════════════════════════════════════════
# 4. HEAVY / FAST-CADENCE OVERLAP
# ══════════════════════════════════════════════════════════════
print("\n── 4. Heavy × Fast-cadence overlap ──")

overlap = {
    "both": int(((df["is_heavy_p75"] == 1) & (df["is_fast_cadence"] == 1)).sum()),
    "heavy_only": int(((df["is_heavy_p75"] == 1) & (df["is_fast_cadence"] == 0)).sum()),
    "fast_only": int(((df["is_heavy_p75"] == 0) & (df["is_fast_cadence"] == 1)).sum()),
    "neither": int(((df["is_heavy_p75"] == 0) & (df["is_fast_cadence"] == 0)).sum()),
}
overlap["pct_overlap_among_heavy"] = round(
    overlap["both"] / (overlap["both"] + overlap["heavy_only"]) * 100, 1
)
overlap["pct_overlap_among_fast"] = round(
    overlap["both"] / (overlap["both"] + overlap["fast_only"]) * 100, 1
)
print(f"  Both: {overlap['both']:,}")
print(f"  Heavy only: {overlap['heavy_only']:,}")
print(f"  Fast only: {overlap['fast_only']:,}")
print(f"  Neither: {overlap['neither']:,}")
print(f"  % of heavy users who are also fast-cadence: {overlap['pct_overlap_among_heavy']}%")
print(f"  % of fast-cadence users who are also heavy: {overlap['pct_overlap_among_fast']}%")


# ══════════════════════════════════════════════════════════════
# 5. SENSITIVITY CHECKS
# ══════════════════════════════════════════════════════════════
print("\n── 5. Sensitivity checks ──")

sensitivity_results = {}
for pctl_col, pctl_name in [("is_heavy_p70", "top_30pct"),
                             ("is_heavy_p80", "top_20pct")]:
    sub = df[FEATURES_NO_GAP + [pctl_col]].dropna()
    X = sub[FEATURES_NO_GAP].values
    y = sub[pctl_col].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_const = sm.add_constant(X_scaled)
    model = sm.Logit(y, X_const).fit(disp=0)

    from sklearn.linear_model import LogisticRegression
    lr_sk = LogisticRegression(max_iter=1000, random_state=SEED)
    cv_scores = cross_val_score(lr_sk, X_scaled, y, cv=CV_FOLDS,
                                scoring="roc_auc")

    sens_or = {}
    params = model.params[1:]
    conf = model.conf_int()[1:]
    for i, feat in enumerate(FEATURES_NO_GAP):
        sens_or[feat] = {
            "odds_ratio": round(float(np.exp(params[i])), 4),
            "ci_lower": round(float(np.exp(conf[i][0])), 4),
            "ci_upper": round(float(np.exp(conf[i][1])), 4),
        }

    sensitivity_results[pctl_name] = {
        "odds_ratios": sens_or,
        "cv_auc_mean": round(float(cv_scores.mean()), 4),
        "n_heavy": int(y.sum()),
        "n_total": int(len(y)),
    }
    print(f"  {pctl_name}: AUC={cv_scores.mean():.3f}, n_heavy={int(y.sum()):,}")

# Sensitivity chart: compare ORs across thresholds
fig, ax = plt.subplots(figsize=(12, 7))
feats = sorted(FEATURES_NO_GAP,
               key=lambda f: abs(np.log(or_no_gap[f]["odds_ratio"])),
               reverse=True)
y_positions = np.arange(len(feats))
width = 0.25

for i, (label, data, color) in enumerate([
    ("Top 25% (primary)", {f: or_no_gap[f] for f in feats}, "#4C72B0"),
    ("Top 30%", {f: sensitivity_results["top_30pct"]["odds_ratios"][f] for f in feats}, "#55A868"),
    ("Top 20%", {f: sensitivity_results["top_20pct"]["odds_ratios"][f] for f in feats}, "#C44E52"),
]):
    ors = [data[f]["odds_ratio"] for f in feats]
    ci_lo = [data[f]["ci_lower"] for f in feats]
    ci_hi = [data[f]["ci_upper"] for f in feats]
    errors = [[o - l for o, l in zip(ors, ci_lo)],
              [h - o for o, h in zip(ors, ci_hi)]]
    offset = (i - 1) * width
    ax.errorbar(ors, y_positions + offset, xerr=errors, fmt="o",
                color=color, ecolor=color, capsize=2, markersize=5,
                alpha=0.8, label=label)

ax.set_yticks(y_positions)
ax.set_yticklabels([FEATURE_LABELS.get(f, f) for f in feats])
ax.axvline(1.0, color="black", linewidth=0.5)
ax.set_xlabel("Odds ratio (standardised, 95% CI)")
ax.set_title("Sensitivity check: odds ratios across heavy-user thresholds")
ax.legend(loc="best", fontsize=9)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "sensitivity_check.png"), dpi=150,
            bbox_inches="tight")
plt.close()
print("  ✓ sensitivity_check.png")


# ══════════════════════════════════════════════════════════════
# 6. LIFECYCLE SEGMENTS
# ══════════════════════════════════════════════════════════════
print("\n── 6. Lifecycle segments ──")

segment_summary = {}
for seg in df["lifecycle_segment"].unique():
    seg_df = df[df["lifecycle_segment"] == seg]
    n = len(seg_df)
    segment_summary[seg] = {
        "n_users": n,
        "pct_of_total": round(n / len(df) * 100, 1),
        "avg_total_orders": round(float(seg_df["total_orders"].mean()), 1),
        "median_total_orders": float(seg_df["total_orders"].median()),
        "avg_median_gap": round(float(seg_df["median_gap_orders_4plus"].mean()), 1),
        "pct_heavy": round(float(seg_df["is_heavy_p75"].mean() * 100), 1),
        "pct_fast_cadence": round(float(seg_df["is_fast_cadence"].mean() * 100), 1),
        "avg_first_order_size": round(float(seg_df["first_order_size"].mean()), 1),
        "avg_reorder_rate": round(float(seg_df["reorder_rate_2_3"].mean()), 3),
    }
    print(f"  {seg}: n={n:,} ({segment_summary[seg]['pct_of_total']}%), "
          f"heavy={segment_summary[seg]['pct_heavy']}%, "
          f"avg_orders={segment_summary[seg]['avg_total_orders']}")

# Segment summary chart
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
segments_ordered = ["small-and-slow", "small-and-fast", "big-and-slow", "big-and-fast"]
seg_colors = ["#C44E52", "#DD8452", "#55A868", "#4C72B0"]

# Segment sizes
ax = axes[0]
sizes = [segment_summary[s]["n_users"] for s in segments_ordered]
ax.bar(range(4), sizes, color=seg_colors, edgecolor="white")
ax.set_xticks(range(4))
ax.set_xticklabels([s.replace("-", "\n") for s in segments_ordered], fontsize=9)
ax.set_ylabel("Number of users")
ax.set_title("Segment sizes")
for i, v in enumerate(sizes):
    ax.text(i, v + 500, f"{v:,}", ha="center", fontsize=8)

# Heavy-user rate by segment
ax = axes[1]
pcts = [segment_summary[s]["pct_heavy"] for s in segments_ordered]
ax.bar(range(4), pcts, color=seg_colors, edgecolor="white")
ax.set_xticks(range(4))
ax.set_xticklabels([s.replace("-", "\n") for s in segments_ordered], fontsize=9)
ax.set_ylabel("% heavy users")
ax.set_title("Heavy-user rate by segment")
for i, v in enumerate(pcts):
    ax.text(i, v + 0.5, f"{v}%", ha="center", fontsize=8)

# Avg total orders by segment
ax = axes[2]
avg_ords = [segment_summary[s]["avg_total_orders"] for s in segments_ordered]
ax.bar(range(4), avg_ords, color=seg_colors, edgecolor="white")
ax.set_xticks(range(4))
ax.set_xticklabels([s.replace("-", "\n") for s in segments_ordered], fontsize=9)
ax.set_ylabel("Avg total orders")
ax.set_title("Average total orders by segment")
for i, v in enumerate(avg_ords):
    ax.text(i, v + 0.3, f"{v:.1f}", ha="center", fontsize=8)

plt.suptitle("Lifecycle segments (defined from orders 1–3 only)", fontsize=13)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "lifecycle_segments.png"), dpi=150,
            bbox_inches="tight")
plt.close()
print("  ✓ lifecycle_segments.png")


# ══════════════════════════════════════════════════════════════
# 7. REORDER-RATE CURVE
# ══════════════════════════════════════════════════════════════
print("\n── 7. Reorder-rate curve ──")

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(reorder_curve["order_number"], reorder_curve["reorder_rate"],
        marker="o", color="#4C72B0", linewidth=2, markersize=6)
for _, row in reorder_curve.iterrows():
    ax.annotate(f"{row['reorder_rate']:.1%}",
                (row["order_number"], row["reorder_rate"]),
                textcoords="offset points", xytext=(0, 10),
                fontsize=8, ha="center")

n_cohort = int(reorder_curve["n_users"].iloc[0])
ax.set_xlabel("Order number")
ax.set_ylabel("Reorder rate (share of items that are reorders)")
ax.set_title(f"Reorder rate by order number\n"
             f"(constant cohort: {n_cohort:,} users with ≥10 prior orders)")
ax.set_xticks(range(1, 11))
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.set_ylim(-0.02, 0.75)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "reorder_rate_curve.png"), dpi=150,
            bbox_inches="tight")
plt.close()
print("  ✓ reorder_rate_curve.png")


# ══════════════════════════════════════════════════════════════
# 8. UPDATE RESULTS.JSON
# ══════════════════════════════════════════════════════════════
print("\n── 8. Updating results.json ──")

results["phase2_analysis"] = {
    "feature_comparisons": comparison_results,
    "logistic_regression": regression_results,
    "heavy_fast_overlap": overlap,
    "sensitivity": sensitivity_results,
    "lifecycle_segments": segment_summary,
    "reorder_curve": {
        str(int(row["order_number"])): round(float(row["reorder_rate"]), 4)
        for _, row in reorder_curve.iterrows()
    },
    "reorder_curve_cohort_size": n_cohort,
}

with open(RESULTS_JSON, "w") as f:
    json.dump(results, f, indent=2)
print(f"  ✓ {RESULTS_JSON}")

print("\n✅ Phase 2 analysis complete.")
