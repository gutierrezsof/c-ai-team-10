"""
=====================================================================
PAGE 3 — "Compare Careers"
=====================================================================
Objective:
    Let the user pick 2-5 careers and directly compare them on:
      1. Median annual wage (grouped bar chart) — REQUIRED
      2. Projected employment growth % (bar chart) — OPTIONAL toggle

    An "Select Occupation Group" dropdown filters which careers are
    available in the compare dropdown, matching the pattern used on
    Page 2 ("Career Opportunity Explorer"). It defaults to
    "All Occupations" so the page can open on Sammie's worked example
    from the home page (market research analyst, data scientist, HR
    specialist), which spans more than one occupation group.

Data source decision
---------------------
Two files were provided: national_careers.csv and state_careers.csv.

    national_careers.csv -> one row PER OCCUPATION (831 unique titles).
        Columns include: national_occ_title, occ_code, employment_2025,
        employment_2035, growth_pct, national_median_wage, education,
        occupation_group, etc.
        -> This already has everything Page 3 needs: wage + growth,
           at the national level, one row per career. No merge needed.

    state_careers.csv -> one row PER STATE PER OCCUPATION (35,224 rows:
        occ_code + state). This is for a *state-level* comparison page
        (e.g. "compare my state to the nation"), not for this page.

Decision: Page 3 uses ONLY national_careers.csv. No merge is required
because a single row per occupation already contains both the wage
metric and the growth metric this page needs to visualize.
=====================================================================
"""

import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd


# ---------------------------------------------------------------
# STEP 1 — Register this file as a page in the multipage app
# ---------------------------------------------------------------
dash.register_page(
    __name__,
    path="/compare-careers",
    name="Compare Careers",
    title="Compare Careers",
    order=3,
)


# ---------------------------------------------------------------
# STEP 2 — Load & lightly clean the data (runs once at import time)
# ---------------------------------------------------------------
DATA_PATH = "data/national_careers.csv"  # adjust path if your app.py lives elsewhere


def load_career_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Clean up whitespace introduced by the raw BLS-style export
    df.columns = [c.strip() for c in df.columns]
    df["national_occ_title"] = df["national_occ_title"].str.strip()
    df["occupation_group"] = df["occupation_group"].str.strip()
    df["education"] = df["education"].str.strip()

    # Drop rows with no wage data (a handful of suppressed BLS values)
    df = df.dropna(subset=["national_median_wage"])

    # Keep only the columns this page actually uses
    cols = [
        "national_occ_title", "occ_code", "occupation_group",
        "national_median_wage", "growth_pct",
        "employment_2025", "employment_2035", "education",
    ]
    return df[cols].reset_index(drop=True)


careers_df = load_career_data()

# Dropdown options built once from the cleaned data
CAREER_OPTIONS = [
    {"label": title, "value": title}
    for title in sorted(careers_df["national_occ_title"].unique())
]

# Occupation group filter options. "All Occupations" is still included
# in the list so users can switch back to seeing everything, but it is
# NOT the default selection (see DEFAULT_OCCUPATION_GROUP below).
OCCUPATION_GROUP_OPTIONS = [{"label": "All Occupations", "value": "All"}] + [
    {"label": group, "value": group}
    for group in sorted(careers_df["occupation_group"].unique())
]

# Default occupation group shown on first page load. Kept at "All" so the
# page can open on Sammie's cross-group example (see DEFAULT_CAREERS below).
# Any other value here must match a string in careers_df["occupation_group"]
# EXACTLY (case + spacing).
DEFAULT_OCCUPATION_GROUP = "All"

# Fall back to "All" if the requested default isn't actually present in
# the data, so the page never loads with an invalid/blank selection.
_group_values = {opt["value"] for opt in OCCUPATION_GROUP_OPTIONS}
if DEFAULT_OCCUPATION_GROUP not in _group_values:
    DEFAULT_OCCUPATION_GROUP = "All"

# Open on Sammie's short list from the home page ("market research analyst,
# data analyst, and HR specialist"). Any title missing from the data is
# dropped; if fewer than two survive, fall back to the first few careers.
DEFAULT_CAREERS = [
    c for c in [
        "Market research analysts and marketing specialists",
        "Data scientists",
        "Human resources specialists",
    ]
    if c in careers_df["national_occ_title"].values
][:5] or [opt["value"] for opt in CAREER_OPTIONS[:3]]


# ---------------------------------------------------------------
# STEP 3 — Layout: occupation group filter + multiselect + toggle + charts
# ---------------------------------------------------------------
layout = html.Div(
    className="page-container",
    children=[

        html.H1("Compare Careers", className="page-title"),
        html.P(
            "Select 2 to 5 careers to compare them side by side. "
            "How do these careers stack up?",
            className="page-subtitle",
        ),

        # --- Control: occupation group filter (narrows career dropdown) --
        html.Div(
            className="controls-row",
            children=[
                html.Label("Select Occupation Group:", className="control-label"),
                dcc.Dropdown(
                    id="occupation-group-filter",
                    options=OCCUPATION_GROUP_OPTIONS,
                    value=DEFAULT_OCCUPATION_GROUP,
                    clearable=False,
                    className="dropdown",
                ),
            ],
        ),

        # --- Control: multiselect dropdown -----------------------------
        html.Div(
            className="controls-row",
            children=[
                html.Label("Select careers to compare (2–5):", className="control-label"),
                dcc.Dropdown(
                    id="career-compare-dropdown",
                    options=CAREER_OPTIONS,
                    value=DEFAULT_CAREERS,
                    multi=True,
                    placeholder="Start typing a career title...",
                    className="dropdown",
                ),
                # NOTE: styles.css has no dedicated warning/error class yet.
                # Using a small inline style here as a placeholder — swap in
                # a real class (e.g. ".warning-text") if/when you add one.
                html.Div(
                    id="career-selection-warning",
                    style={"color": "#d62728", "fontSize": "13px", "marginTop": "6px"},
                ),
            ],
        ),

        # --- Control: which metrics to show -----------------------------
        html.Div(
            className="controls-row",
            children=[
                html.Label("Chart options:", className="control-label"),
                dcc.Checklist(
                    id="metric-toggle",
                    options=[
                        {"label": " Show projected employment growth (%)",
                         "value": "growth"},
                    ],
                    value=["growth"],  # ticked by default; user can uncheck to hide it
                    inline=True,
                ),
            ],
        ),

        # --- Required visualization: grouped bar chart, median wage -----
        html.Div(
            className="chart-card",
            children=[dcc.Graph(id="wage-comparison-chart")],
        ),

        # --- Optional visualization: employment growth -------------------
        html.Div(
            id="growth-chart-card",
            className="chart-card",
            children=[dcc.Graph(id="growth-comparison-chart")],
        ),

        # --- Source note, matching page 1's citation style ---------------
        html.Div(
            [
                "Source: U.S. Bureau of Labor Statistics, Occupational Employment "
                "and Wage Statistics / Employment Projections."
            ],
            className="source-note",
        ),
    ],
)


# ---------------------------------------------------------------
# STEP 4 — Callback: occupation group filter updates the career dropdown
# ---------------------------------------------------------------
@callback(
    Output("career-compare-dropdown", "options"),
    Output("career-compare-dropdown", "value"),
    Input("occupation-group-filter", "value"),
    prevent_initial_call=True,   # keep DEFAULT_CAREERS (Sammie's picks) on first load
)
def filter_career_options(selected_group):
    if not selected_group or selected_group == "All":
        filtered_df = careers_df
    else:
        filtered_df = careers_df[careers_df["occupation_group"] == selected_group]

    options = [
        {"label": title, "value": title}
        for title in sorted(filtered_df["national_occ_title"].unique())
    ]

    # Reset selection to the first 2-4 careers available in this group
    # (keeps within the required 2-5 range and avoids stale selections
    # that no longer belong to the chosen group)
    new_value = (
        [opt["value"] for opt in options[:4]]
        if len(options) >= 2
        else [opt["value"] for opt in options]
    )

    return options, new_value


# ---------------------------------------------------------------
# STEP 5 — Callback: validate selection + build the chart(s)
# ---------------------------------------------------------------
@callback(
    Output("wage-comparison-chart", "figure"),
    Output("growth-comparison-chart", "figure"),
    Output("growth-chart-card", "style"),
    Output("career-selection-warning", "children"),
    Input("career-compare-dropdown", "value"),
    Input("metric-toggle", "value"),
)
def update_comparison_charts(selected_careers, metric_toggle):
    selected_careers = selected_careers or []

    # ---- Enforce the 2-5 career rule --------------------------------
    warning = ""
    if len(selected_careers) < 2:
        warning = "Please select at least 2 careers to compare."
    elif len(selected_careers) > 5:
        warning = "Please select 5 or fewer careers. Showing the first 5 selected."
        selected_careers = selected_careers[:5]

    # Not enough data yet -> return empty placeholder figures
    if len(selected_careers) < 2:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            annotations=[{
                "text": "Select 2-5 careers above to see the comparison.",
                "xref": "paper", "yref": "paper",
                "showarrow": False, "font": {"size": 16},
            }],
            xaxis={"visible": False}, yaxis={"visible": False},
        )
        return empty_fig, empty_fig, {"display": "none"}, warning

    # ---- Filter the dataframe to just the selected careers -----------
    filtered = careers_df[careers_df["national_occ_title"].isin(selected_careers)].copy()
    # Preserve the order the user picked them in, for a stable bar order
    filtered["national_occ_title"] = pd.Categorical(
        filtered["national_occ_title"], categories=selected_careers, ordered=True
    )
    filtered = filtered.sort_values("national_occ_title")

    # ---- REQUIRED: grouped bar chart — Median Annual Wage -------------
    wage_fig = go.Figure(
        data=[
            go.Bar(
                x=filtered["national_occ_title"],
                y=filtered["national_median_wage"],
                text=filtered["national_median_wage"].map(lambda v: f"${v:,.0f}"),
                textposition="outside",
                marker_color="#2E86AB",
            )
        ]
    )
    wage_fig.update_layout(
        title="Median Annual Wage by Career",
        xaxis_title="Career",
        yaxis_title="Median Annual Wage (USD)",
        yaxis_tickprefix="$",
        yaxis_tickformat=",",
        template="plotly_white",
        margin=dict(t=60, b=40),
    )

    # ---- OPTIONAL: bar chart — Projected Employment Growth (%) --------
    show_growth = "growth" in (metric_toggle or [])
    growth_fig = go.Figure()
    growth_style = {"display": "none"}

    if show_growth:
        colors = ["#2ca02c" if v >= 0 else "#d62728" for v in filtered["growth_pct"]]
        growth_fig = go.Figure(
            data=[
                go.Bar(
                    x=filtered["national_occ_title"],
                    y=filtered["growth_pct"],
                    text=filtered["growth_pct"].map(lambda v: f"{v:+.1f}%"),
                    textposition="outside",
                    marker_color=colors,
                )
            ]
        )
        growth_fig.update_layout(
            title="Projected Employment Growth (2025–2035)",
            xaxis_title="Career",
            yaxis_title="Projected Growth (%)",
            template="plotly_white",
            margin=dict(t=60, b=40),
        )
        growth_style = {"display": "block"}

    return wage_fig, growth_fig, growth_style, warning