"""
pages/page2.py — Explore Career + Location (Sofia)

Answers: "What does this career look like, and where are the best opportunities?"
Career dropdown -> KPI profile and a U.S. choropleth that toggles between
median wage and employment, with state abbreviations labeled on the map.

Data: national_careers.csv (one row per occupation), state_careers.csv (one row
per occupation per state, OEWS). BLS suppresses low-reliability estimates, so
missing values are flagged and left blank rather than filled in.

AI assistance: Used Claude to scaffold the layout/callback structure and the
missing-data handling for the choropleth, then condensed it. Reviewed and
adjusted the color scale, hover text, and footnote wording by hand.

CHANGE LOG (this revision):
  - Removed the "Projected Employment: 2025 vs. 2035" bar chart and its
    callback. The choropleth is now the only chart on the page and runs
    full width (charts-two-col -> charts-one-col).
  - Added state abbreviation labels directly on the choropleth (e.g. "VA"
    drawn on top of Virginia), via a text-only Scattergeo trace layered
    over the choropleth. Plotly auto-places these at each state's
    centroid when locationmode="USA-states" is used, so no external
    centroid lookup table is needed.
"""

import os
import dash
from dash import dcc, html, callback, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Data ------------------------------------------------------------------
# The CSVs may live next to this file, in the project root, or in data/.
_DIRS = [os.path.dirname(os.path.abspath(__file__)),
         os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
         os.getcwd(), os.path.join(os.getcwd(), "data")]


def _read(filename, **strip):
    for d in _DIRS:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            df = pd.read_csv(path)
            for col in strip:
                df[col] = df[col].astype(str).str.strip()
            return df
    raise FileNotFoundError(f"Couldn't find {filename}. Looked in: {_DIRS}")


national_df = _read("national_careers.csv", national_occ_title=1, occ_code=1)
state_df = _read("state_careers.csv", occ_code=1, state=1)

# Flag suppressed estimates so the UI can say "Not reported" instead of faking 0.
national_df["wage_reported"] = national_df["national_median_wage"].notna()
state_df["wage_reported"] = state_df["state_median_wage"].notna()
state_df["employment_reported"] = state_df["state_employment"].notna()

CAREER_OPTIONS = [{"label": t, "value": c} for c, t in
                  national_df.sort_values("national_occ_title")[
                      ["occ_code", "national_occ_title"]].drop_duplicates().values]
# Open on Sammie's worked example from the home page; fall back to the largest
# occupation if that title isn't in the data so the page never opens empty.
_sammie_occ = national_df.loc[
    national_df["national_occ_title"] == "Market research analysts and marketing specialists",
    "occ_code",
]
DEFAULT_OCC = (_sammie_occ.iloc[0] if not _sammie_occ.empty
               else national_df.nlargest(1, "employment_2025")["occ_code"].iloc[0])

# metric key -> (value column, reported flag, legend label, card title, money?)
METRICS = {
    "wage": ("state_median_wage", "wage_reported", "Median Annual Wage",
             "Median Annual Wage by State", True),
    "employment": ("state_employment", "employment_reported", "People Employed",
                   "Number Employed by State", False),
}

dash.register_page(__name__, path="/explore", name="Explore Career + Location", order=4)


# --- Helpers ---------------------------------------------------------------
def _fmt(val, kind="int"):
    if val is None or val != val:            # None or NaN
        return "Not reported"
    if kind == "money":
        return f"${val:,.0f}"
    if kind == "pct":
        return f"{'▲' if val >= 0 else '▼'} {val:+.1f}%"
    return f"{val:,.0f}"


def _kpi(label, value, note=None, accent=False):
    return html.Div(
        [html.Div(label, className="kpi-label"), html.Div(value, className="kpi-value")]
        + ([html.Div(note, className="kpi-note")] if note else []),
        className="kpi-card accent-amber" if accent else "kpi-card")


def _blank(message):
    fig = go.Figure()
    fig.update_layout(annotations=[{"text": message, "showarrow": False,
                                    "font": {"size": 14, "color": "#6b7280"}}])
    return fig.update_xaxes(visible=False).update_yaxes(visible=False)


def _lookup(occ_code):
    """Return the national row for occ_code, or None if missing/unselected."""
    if not occ_code:
        return None
    row = national_df.loc[national_df["occ_code"] == occ_code]
    return None if row.empty else row.iloc[0]


def _control(label, component):
    return html.Div([html.Label(label, className="control-label"), component],
                    className="control-block")


def _chart_card(title, graph, extra=None):
    return html.Div([html.Div(title, className="chart-card-title"), graph] +
                    ([extra] if extra is not None else []), className="chart-card")


# --- Layout ----------------------------------------------------------------
def layout():
    return html.Div(className="page-container", children=[
        html.Div("Explore Career + Location", className="page-title"),
        html.Div("Pick a career to see its national profile and where in the "
                 "U.S. it pays best and employs the most people.",
                 className="page-subtitle"),
        html.Div(className="controls-row", children=[
            _control("Career", dcc.Dropdown(
                id="p2-career-dropdown", options=CAREER_OPTIONS, value=DEFAULT_OCC,
                clearable=False, placeholder="Search for a career...")),
            _control("Map Shows", dcc.RadioItems(
                id="p2-map-metric",
                options=[{"label": m[2], "value": k} for k, m in METRICS.items()],
                value="wage", className="dash-radio-toggle", inline=True)),
        ]),
        html.Div(id="p2-error-banner"),
        html.Div(id="p2-kpi-row", className="kpi-row"),
        # NOTE: the employment bar chart card that used to sit here (inside a
        # two-column "charts-two-col" row) has been removed. The choropleth
        # is now the only chart on the page and runs full width.
        html.Div(className="charts-one-col", children=[
            _chart_card(html.Span(id="p2-map-title"),
                        dcc.Graph(id="p2-choropleth", config={"displayModeBar": False}),
                        html.Div(id="p2-map-footnote", className="footnote")),
        ]),
    ])


# --- Callbacks -------------------------------------------------------------
@callback(Output("p2-error-banner", "children"), Output("p2-kpi-row", "children"),
          Input("p2-career-dropdown", "value"))
def update_profile(occ_code):
    row = _lookup(occ_code)
    if row is None:
        msg = "Choose a career from the dropdown to see its profile." if not occ_code \
            else f"No profile data found for occupation code {occ_code}."
        return html.Div(msg, className="error-banner"), []

    wage = row["national_median_wage"] if row["wage_reported"] else None
    return None, [
        _kpi("Median Annual Wage", _fmt(wage, "money"), "National, 2025"),
        _kpi("Projected Growth", _fmt(row["growth_pct"], "pct"), "2025 → 2035", accent=True),
        _kpi("Annual Openings", _fmt(row["annual_openings"]), "Per year, avg."),
        _kpi("Employed (2025)", _fmt(row["employment_2025"]), "Nationwide"),
        _kpi("Typical Education", row["education"], row["occupation_group"]),
    ]


# NOTE: update_employment_chart() and the "p2-employment-chart" Graph have
# been removed along with the bar chart itself. If you ever want the 2025
# vs. 2035 comparison back, the KPI row still surfaces "Employed (2025)",
# and national_df has employment_2035 available to re-add it later.


@callback(Output("p2-choropleth", "figure"), Output("p2-map-title", "children"),
          Output("p2-map-footnote", "children"),
          Input("p2-career-dropdown", "value"), Input("p2-map-metric", "value"))
def update_choropleth(occ_code, metric):
    col, flag, label, title, is_money = METRICS[metric]
    states = state_df.loc[state_df["occ_code"] == occ_code].copy() if occ_code else state_df.iloc[:0]
    if states.empty:
        msg = "Select a career to see where it's strongest." if not occ_code \
            else "No state-level data available for this career."
        return _blank(msg), title, ""

    states["hover_value"] = states[col].map(lambda v: _fmt(v, "money" if is_money else "int"))

    fig = px.choropleth(
        states, locations="state", locationmode="USA-states", color=col, scope="usa",
        color_continuous_scale="Viridis",  # colorblind-safe, perceptually uniform
        hover_name="state_name", custom_data=["hover_value"])
    fig.update_traces(hovertemplate=f"<b>%{{hovertext}}</b><br>{label}: %{{customdata[0]}}<extra></extra>")

    # NEW: overlay state abbreviations (e.g. "VA") directly on the map.
    # A text-only Scattergeo trace sharing the same locationmode lets Plotly
    # auto-place each label at its state's centroid — no separate lookup
    # table of lat/lon centroids is needed. hoverinfo is turned off here so
    # hovering still shows the choropleth's tooltip, not this label trace.
    fig.add_trace(go.Scattergeo(
        locations=states["state"],
        locationmode="USA-states",
        text=states["state"],
        mode="text",
        textfont=dict(size=9, color="#1f2937"),
        hoverinfo="skip",
        showlegend=False,
    ))

    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), coloraxis_colorbar_title=None,
                      height=340, geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="white"))

    n_missing = int((~states[flag]).sum())
    footnote = (f"{n_missing} state(s) have no reliable estimate for this career and are "
                "shown blank (BLS suppresses low-count data).") if n_missing else ""
    return fig, title, footnote
