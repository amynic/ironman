"""
Ironman 70.3 Comprehensive Data Analysis (2004-2020)
=====================================================
Generates charts and summary statistics across 5 areas:
1. Performance Trends Over Time
2. Country Comparisons
3. Age Group Analysis
4. Race/Course Comparisons
5. Gender Analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os
import numpy as np
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "Half_Ironman_df6.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "analysis_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", palette="colorblind")
plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight", "figure.figsize": (12, 6)})

COLORS = {"M": "#1f77b4", "F": "#e377c2"}


# ── Helpers ─────────────────────────────────────────────────────────────────
def seconds_to_hm(s):
    """Convert seconds to 'Xh Ym' string."""
    h, m = divmod(int(s), 3600)
    m = m // 60
    return f"{h}h {m:02d}m"


def format_time_axis(ax, axis="y"):
    """Format a time axis from seconds to HH:MM."""
    def fmt(x, _):
        h, m = divmod(int(x), 3600)
        return f"{h}:{m:02d}"
    if axis == "y":
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt))
    else:
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt))


def save(fig, name):
    path = os.path.join(OUTPUT_DIR, f"{name}.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Load & Clean ────────────────────────────────────────────────────────────
print("Loading data...")
df = pd.read_csv(DATA_PATH)
print(f"  Raw rows: {len(df):,}")

# Drop exact duplicates
dupes = df.duplicated().sum()
df = df.drop_duplicates()
print(f"  Duplicates removed: {dupes:,}")

# Convert numeric columns
time_cols = ["SwimTime", "Transition1Time", "BikeTime", "Transition2Time", "RunTime", "FinishTime"]
for col in time_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Sanity filters: positive splits, plausible finish time (2.5h - 10h)
MIN_FINISH = 2.5 * 3600  # 9000s
MAX_FINISH = 10 * 3600   # 36000s
split_cols = ["SwimTime", "BikeTime", "RunTime"]

before = len(df)
df = df[
    (df["FinishTime"] >= MIN_FINISH)
    & (df["FinishTime"] <= MAX_FINISH)
    & (df[split_cols] > 0).all(axis=1)
    & (df["Transition1Time"] >= 0)
    & (df["Transition2Time"] >= 0)
    & (df["Gender"].isin(["M", "F"]))
]
print(f"  Rows after filtering: {len(df):,} (removed {before - len(df):,})")

# Sort age groups numerically
df["AgeBand"] = pd.to_numeric(df["AgeBand"], errors="coerce")
df = df.dropna(subset=["AgeBand"])
df["AgeBand"] = df["AgeBand"].astype(int)

# Add derived columns
df["SwimPct"] = df["SwimTime"] / df["FinishTime"] * 100
df["BikePct"] = df["BikeTime"] / df["FinishTime"] * 100
df["RunPct"] = df["RunTime"] / df["FinishTime"] * 100
df["TransitionPct"] = (df["Transition1Time"] + df["Transition2Time"]) / df["FinishTime"] * 100

# Unique events per year
events_per_year = df.groupby("EventYear")["EventLocation"].nunique()

print(f"\n{'='*60}")
print(f"IRONMAN 70.3 Analysis — {len(df):,} records, {df['EventYear'].nunique()} years")
print(f"Years: {df['EventYear'].min()} - {df['EventYear'].max()}")
print(f"Unique races: {df['EventLocation'].nunique()}")
print(f"Countries: {df['Country'].nunique()}")
print(f"{'='*60}\n")


# ════════════════════════════════════════════════════════════════════════════
# 1. PERFORMANCE TRENDS OVER TIME
# ════════════════════════════════════════════════════════════════════════════
print("1. Performance Trends Over Time")

# 1a. Median finish time by year + gender
yearly_gender = df.groupby(["EventYear", "Gender"])["FinishTime"].median().reset_index()
fig, ax = plt.subplots()
for g, color in COLORS.items():
    subset = yearly_gender[yearly_gender["Gender"] == g]
    label = "Male" if g == "M" else "Female"
    ax.plot(subset["EventYear"], subset["FinishTime"], marker="o", color=color, label=label, linewidth=2)
ax.set_title("Median Finish Time by Year & Gender", fontsize=14, fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("Median Finish Time")
format_time_axis(ax, "y")
ax.legend()
# Annotate 2020
ax.axvline(x=2020, color="gray", linestyle="--", alpha=0.5)
ax.annotate("COVID", xy=(2020, ax.get_ylim()[1]), fontsize=9, color="gray", ha="center")
save(fig, "01_finish_time_by_year_gender")

# 1b. Participation growth + event count
yearly_counts = df.groupby("EventYear").size().reset_index(name="Finishers")
fig, ax1 = plt.subplots()
ax1.bar(yearly_counts["EventYear"], yearly_counts["Finishers"], color="#1f77b4", alpha=0.7, label="Finishers")
ax1.set_xlabel("Year")
ax1.set_ylabel("Number of Finishers", color="#1f77b4")
ax1.tick_params(axis="y", labelcolor="#1f77b4")

ax2 = ax1.twinx()
ax2.plot(events_per_year.index, events_per_year.values, color="#ff7f0e", marker="s", linewidth=2, label="Unique Races")
ax2.set_ylabel("Unique Races", color="#ff7f0e")
ax2.tick_params(axis="y", labelcolor="#ff7f0e")

ax1.axvline(x=2020, color="gray", linestyle="--", alpha=0.5)
fig.suptitle("Participation & Race Growth Over Time", fontsize=14, fontweight="bold")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
save(fig, "02_participation_growth")

# 1c. Median split times by year
yearly_splits = df.groupby("EventYear")[["SwimTime", "BikeTime", "RunTime"]].median().reset_index()
fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=False)
for ax, col, title, color in zip(axes, ["SwimTime", "BikeTime", "RunTime"],
                                   ["Swim", "Bike", "Run"],
                                   ["#2ca02c", "#1f77b4", "#d62728"]):
    ax.plot(yearly_splits["EventYear"], yearly_splits[col], marker="o", color=color, linewidth=2)
    ax.set_title(f"Median {title} Time", fontweight="bold")
    ax.set_xlabel("Year")
    format_time_axis(ax, "y")
    ax.axvline(x=2020, color="gray", linestyle="--", alpha=0.3)
fig.suptitle("Median Split Times by Year", fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
save(fig, "03_split_times_by_year")

# 1d. Performance spread by year (percentile bands)
pctls = df.groupby("EventYear")["FinishTime"].quantile([0.25, 0.5, 0.75]).unstack().reset_index()
pctls.columns = ["EventYear", "p25", "p50", "p75"]
fig, ax = plt.subplots()
ax.fill_between(pctls["EventYear"], pctls["p25"], pctls["p75"], alpha=0.3, color="#1f77b4", label="25th-75th percentile")
ax.plot(pctls["EventYear"], pctls["p50"], color="#1f77b4", marker="o", linewidth=2, label="Median")
ax.set_title("Finish Time Distribution by Year", fontsize=14, fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("Finish Time")
format_time_axis(ax, "y")
ax.legend()
ax.axvline(x=2020, color="gray", linestyle="--", alpha=0.5)
save(fig, "04_finish_time_spread_by_year")


# ════════════════════════════════════════════════════════════════════════════
# 2. COUNTRY COMPARISONS
# ════════════════════════════════════════════════════════════════════════════
print("\n2. Country Comparisons")

# 2a. Top 20 countries by participation
country_counts = df["Country"].value_counts().head(20)
fig, ax = plt.subplots(figsize=(12, 7))
country_counts.plot.barh(ax=ax, color="#1f77b4")
ax.invert_yaxis()
ax.set_title("Top 20 Countries by Participation", fontsize=14, fontweight="bold")
ax.set_xlabel("Number of Finishers")
for i, v in enumerate(country_counts):
    ax.text(v + 500, i, f"{v:,}", va="center", fontsize=9)
save(fig, "05_top_countries_participation")

# 2b. Top 20 fastest countries (min 250 finishers)
MIN_COUNTRY = 250
country_perf = df.groupby("Country").agg(
    median_finish=("FinishTime", "median"),
    count=("FinishTime", "size")
).query(f"count >= {MIN_COUNTRY}").sort_values("median_finish")

top20_fast = country_perf.head(20)
fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(range(len(top20_fast)), top20_fast["median_finish"], color="#2ca02c")
ax.set_yticks(range(len(top20_fast)))
ax.set_yticklabels([f"{c} (n={int(top20_fast.loc[c, 'count']):,})" for c in top20_fast.index])
ax.invert_yaxis()
ax.set_title(f"Fastest Countries by Median Finish (min {MIN_COUNTRY} finishers)", fontsize=14, fontweight="bold")
format_time_axis(ax, "x")
ax.set_xlabel("Median Finish Time")
save(fig, "06_fastest_countries")

# 2c. Top countries by discipline (swim/bike/run)
fig, axes = plt.subplots(1, 3, figsize=(18, 7))
for ax, col, title in zip(axes, ["SwimTime", "BikeTime", "RunTime"], ["Swim", "Bike", "Run"]):
    disc = df.groupby("Country").agg(
        median_time=(col, "median"), count=(col, "size")
    ).query(f"count >= {MIN_COUNTRY}").sort_values("median_time").head(15)
    ax.barh(range(len(disc)), disc["median_time"], color="#ff7f0e")
    ax.set_yticks(range(len(disc)))
    ax.set_yticklabels(disc.index)
    ax.invert_yaxis()
    ax.set_title(f"Fastest Countries: {title}", fontweight="bold")
    format_time_axis(ax, "x")
plt.suptitle(f"Fastest Countries by Discipline (min {MIN_COUNTRY} finishers)", fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
save(fig, "07_fastest_countries_by_discipline")


# ════════════════════════════════════════════════════════════════════════════
# 3. AGE GROUP ANALYSIS
# ════════════════════════════════════════════════════════════════════════════
print("\n3. Age Group Analysis")

age_order = sorted(df["AgeGroup"].unique(), key=lambda x: int(x.split("-")[0]) if "-" in x else 999)
# Filter to standard age groups
standard_ages = [ag for ag in age_order if "-" in ag]

# 3a. Median finish time by age group (boxplot)
age_df = df[df["AgeGroup"].isin(standard_ages)].copy()
age_df["AgeGroup"] = pd.Categorical(age_df["AgeGroup"], categories=standard_ages, ordered=True)

fig, ax = plt.subplots(figsize=(14, 6))
sns.boxplot(data=age_df, x="AgeGroup", y="FinishTime", hue="Gender",
            palette=COLORS, showfliers=False, ax=ax)
ax.set_title("Finish Time Distribution by Age Group & Gender", fontsize=14, fontweight="bold")
ax.set_xlabel("Age Group")
ax.set_ylabel("Finish Time")
format_time_axis(ax, "y")
ax.legend(title="Gender", labels=["Male", "Female"])
plt.xticks(rotation=45)
save(fig, "08_finish_time_by_age_group")

# 3b. Participation by age group
age_counts = age_df.groupby(["AgeGroup", "Gender"]).size().reset_index(name="Count")
fig, ax = plt.subplots(figsize=(14, 6))
sns.barplot(data=age_counts, x="AgeGroup", y="Count", hue="Gender", palette=COLORS, ax=ax)
ax.set_title("Participation by Age Group & Gender", fontsize=14, fontweight="bold")
ax.set_xlabel("Age Group")
ax.set_ylabel("Number of Finishers")
ax.legend(title="Gender", labels=["Male", "Female"])
plt.xticks(rotation=45)
save(fig, "09_participation_by_age_group")

# 3c. Peak performance: median finish by age band
peak = df.groupby(["AgeBand", "Gender"])["FinishTime"].median().reset_index()
peak = peak[peak["AgeBand"].between(18, 75)]
fig, ax = plt.subplots()
for g, color in COLORS.items():
    subset = peak[peak["Gender"] == g]
    label = "Male" if g == "M" else "Female"
    ax.plot(subset["AgeBand"], subset["FinishTime"], marker="o", color=color, label=label, linewidth=2)
ax.set_title("Median Finish Time by Age Band", fontsize=14, fontweight="bold")
ax.set_xlabel("Age (lower bound of group)")
ax.set_ylabel("Median Finish Time")
format_time_axis(ax, "y")
ax.legend()
save(fig, "10_peak_performance_age")

# 3d. Split % by age group
split_pct = age_df.groupby("AgeGroup")[["SwimPct", "BikePct", "RunPct", "TransitionPct"]].mean()
fig, ax = plt.subplots(figsize=(14, 6))
split_pct[["SwimPct", "BikePct", "RunPct", "TransitionPct"]].plot.bar(
    stacked=True, ax=ax, color=["#2ca02c", "#1f77b4", "#d62728", "#9467bd"]
)
ax.set_title("Race Time Composition by Age Group", fontsize=14, fontweight="bold")
ax.set_xlabel("Age Group")
ax.set_ylabel("% of Total Finish Time")
ax.legend(["Swim", "Bike", "Run", "Transitions"], bbox_to_anchor=(1.05, 1))
plt.xticks(rotation=45)
save(fig, "11_split_pct_by_age_group")


# ════════════════════════════════════════════════════════════════════════════
# 4. RACE / COURSE COMPARISONS
# ════════════════════════════════════════════════════════════════════════════
print("\n4. Race/Course Comparisons")

MIN_RACE = 100
race_stats = df.groupby("EventLocation").agg(
    median_finish=("FinishTime", "median"),
    count=("FinishTime", "size"),
    years=("EventYear", "nunique")
).query(f"count >= {MIN_RACE}")

# Shorten race names for display
def shorten_name(name):
    return name.replace("IRONMAN 70.3 ", "").replace("IRONMAN ", "")

# 4a. Top 10 fastest courses
fastest = race_stats.sort_values("median_finish").head(10)
fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(range(len(fastest)), fastest["median_finish"], color="#2ca02c")
ax.set_yticks(range(len(fastest)))
ax.set_yticklabels([f"{shorten_name(c)} (n={int(fastest.loc[c, 'count']):,})" for c in fastest.index])
ax.invert_yaxis()
ax.set_title(f"10 Fastest Races by Median Finish (min {MIN_RACE} finishers)", fontsize=14, fontweight="bold")
format_time_axis(ax, "x")
ax.set_xlabel("Median Finish Time")
save(fig, "12_fastest_courses")

# 4b. Top 10 slowest courses
slowest = race_stats.sort_values("median_finish", ascending=False).head(10)
fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(range(len(slowest)), slowest["median_finish"], color="#d62728")
ax.set_yticks(range(len(slowest)))
ax.set_yticklabels([f"{shorten_name(c)} (n={int(slowest.loc[c, 'count']):,})" for c in slowest.index])
ax.invert_yaxis()
ax.set_title(f"10 Slowest Races by Median Finish (min {MIN_RACE} finishers)", fontsize=14, fontweight="bold")
format_time_axis(ax, "x")
ax.set_xlabel("Median Finish Time")
save(fig, "13_slowest_courses")

# 4c. Largest races by total participation
largest = race_stats.sort_values("count", ascending=False).head(15)
fig, ax = plt.subplots(figsize=(12, 7))
ax.barh(range(len(largest)), largest["count"], color="#1f77b4")
ax.set_yticks(range(len(largest)))
ax.set_yticklabels([shorten_name(c) for c in largest.index])
ax.invert_yaxis()
ax.set_title("15 Largest Races by Total Finishers", fontsize=14, fontweight="bold")
ax.set_xlabel("Total Finishers (all years)")
for i, v in enumerate(largest["count"]):
    ax.text(v + 100, i, f"{int(v):,}", va="center", fontsize=9)
save(fig, "14_largest_races")


# ════════════════════════════════════════════════════════════════════════════
# 5. GENDER ANALYSIS
# ════════════════════════════════════════════════════════════════════════════
print("\n5. Gender Analysis")

# 5a. Male vs Female participation over time
gender_year = df.groupby(["EventYear", "Gender"]).size().reset_index(name="Count")
fig, ax = plt.subplots()
for g, color in COLORS.items():
    subset = gender_year[gender_year["Gender"] == g]
    label = "Male" if g == "M" else "Female"
    ax.plot(subset["EventYear"], subset["Count"], marker="o", color=color, label=label, linewidth=2)
ax.set_title("Participation by Gender Over Time", fontsize=14, fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("Number of Finishers")
ax.legend()
ax.axvline(x=2020, color="gray", linestyle="--", alpha=0.5)
save(fig, "15_gender_participation")

# 5b. Female participation % over time
female_pct = gender_year.pivot(index="EventYear", columns="Gender", values="Count")
female_pct["FPct"] = female_pct["F"] / (female_pct["F"] + female_pct["M"]) * 100
fig, ax = plt.subplots()
ax.plot(female_pct.index, female_pct["FPct"], marker="o", color=COLORS["F"], linewidth=2)
ax.set_title("Female Participation % Over Time", fontsize=14, fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("Female %")
ax.set_ylim(0, 50)
ax.axhline(y=female_pct["FPct"].iloc[-1], color="gray", linestyle=":", alpha=0.5)
ax.axvline(x=2020, color="gray", linestyle="--", alpha=0.5)
save(fig, "16_female_participation_pct")

# 5c. Gender performance gap over time
gender_median = df.groupby(["EventYear", "Gender"])["FinishTime"].median().unstack()
gender_median["GapMin"] = (gender_median["F"] - gender_median["M"]) / 60  # gap in minutes
fig, ax = plt.subplots()
ax.bar(gender_median.index, gender_median["GapMin"], color="#9467bd", alpha=0.8)
ax.set_title("Gender Performance Gap Over Time (Female − Male)", fontsize=14, fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("Gap (minutes)")
ax.axvline(x=2020, color="gray", linestyle="--", alpha=0.5)
save(fig, "17_gender_gap")

# 5d. Gender split comparison (% of total time)
gender_splits = df.groupby("Gender")[["SwimPct", "BikePct", "RunPct", "TransitionPct"]].mean()
fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(gender_splits.index))
width = 0.2
labels = ["Swim %", "Bike %", "Run %", "Transition %"]
colors = ["#2ca02c", "#1f77b4", "#d62728", "#9467bd"]
for i, (col, label, color) in enumerate(zip(gender_splits.columns, labels, colors)):
    ax.bar(x + i * width, gender_splits[col], width, label=label, color=color)
ax.set_xticks(x + 1.5 * width)
ax.set_xticklabels(["Male", "Female"])
ax.set_title("Race Time Composition by Gender", fontsize=14, fontweight="bold")
ax.set_ylabel("% of Total Finish Time")
ax.legend()
save(fig, "18_gender_split_comparison")

# 5e. Gender gap by age group
gender_age_gap = df[df["AgeGroup"].isin(standard_ages)].groupby(["AgeGroup", "Gender"])["FinishTime"].median().unstack()
gender_age_gap["GapMin"] = (gender_age_gap["F"] - gender_age_gap["M"]) / 60
gender_age_gap = gender_age_gap.reindex(standard_ages)
fig, ax = plt.subplots(figsize=(14, 6))
ax.bar(range(len(gender_age_gap)), gender_age_gap["GapMin"], color="#9467bd", alpha=0.8)
ax.set_xticks(range(len(gender_age_gap)))
ax.set_xticklabels(gender_age_gap.index, rotation=45)
ax.set_title("Gender Performance Gap by Age Group", fontsize=14, fontweight="bold")
ax.set_xlabel("Age Group")
ax.set_ylabel("Gap (minutes, Female − Male)")
save(fig, "19_gender_gap_by_age")


# ════════════════════════════════════════════════════════════════════════════
# SUMMARY STATISTICS
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)

summary = {
    "Total Records": f"{len(df):,}",
    "Year Range": f"{df['EventYear'].min()}-{df['EventYear'].max()}",
    "Unique Races": str(df["EventLocation"].nunique()),
    "Countries Represented": str(df["Country"].nunique()),
    "Male / Female Split": f"{(df['Gender']=='M').sum():,} / {(df['Gender']=='F').sum():,} ({(df['Gender']=='F').mean()*100:.1f}% F)",
    "Overall Median Finish": seconds_to_hm(df["FinishTime"].median()),
    "Male Median Finish": seconds_to_hm(df[df["Gender"]=="M"]["FinishTime"].median()),
    "Female Median Finish": seconds_to_hm(df[df["Gender"]=="F"]["FinishTime"].median()),
    "Median Swim": seconds_to_hm(df["SwimTime"].median()),
    "Median Bike": seconds_to_hm(df["BikeTime"].median()),
    "Median Run": seconds_to_hm(df["RunTime"].median()),
    "Fastest Finish": seconds_to_hm(df["FinishTime"].min()),
    "Top Country (participation)": df["Country"].value_counts().index[0],
    "Peak Age Group": df[df["AgeGroup"] != "00"].groupby("AgeGroup")["FinishTime"].median().idxmin(),
    "Generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
}

for k, v in summary.items():
    print(f"  {k:30s}: {v}")

# Save summary CSV
summary_df = pd.DataFrame(list(summary.items()), columns=["Metric", "Value"])
summary_path = os.path.join(OUTPUT_DIR, "summary_statistics.csv")
summary_df.to_csv(summary_path, index=False)
print(f"\n  Summary saved: {summary_path}")

print(f"\nAnalysis complete! {len(os.listdir(OUTPUT_DIR))} files saved to {OUTPUT_DIR}")
