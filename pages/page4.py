"""
=====================================================================
Explore Career + Location
=====================================================================

Question:
What does this career look like, and where are the best opportunities?

Data:
- national_careers.csv: one row per occupation
- state_careers.csv: one row per occupation per state (OEWS)

BLS suppresses low-reliability estimates, so missing values are flagged
and left blank rather than filled in.

Expectation:
U.S. choropleth that toggles between median wage and employment, with
state abbreviations labeled on the map.

AI Assistance:
- Used Claude to scaffold the layout and callback structure.
- Reviewed and adjusted the color scale, hover text, and footnote wording by hand.
- Used Claude to help debug merge conflicts and error messages.
=====================================================================
"""

# Import packages
import os

import dash
from dash import dcc, html, callback, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ---------------------------------------------------------------------
# Load and Read Data
# ---------------------------------------------------------------------

_DIRS = [
    os.path.dirname(os.path.abspath(__file__)),
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    os.getcwd(),
    os.path.join(os.getcwd(), "data"),
]


def _read(filename, **strip):
    for d in _DIRS:
        path = os.path.join(d, filename)

        if os.path.exists(path):
            df = pd.read_csv(path)

            for col in strip:
                df[col] = df[col].astype(str).str.strip()

            return df

    raise FileNotFoundError(
        f"Couldn't find {filename}. Looked in: {_DIRS}"
    )


# ---------------------------------------------------------------------
# Data Cleaning
# ---------------------------------------------------------------------

national_df = _read(
    "national_careers.csv",
    national_occ_title=1,
    occ_code=1,
)

state_df = _read(
    "state_careers.csv",
    occ_code=1,
    state=1,
)


# Flag suppressed estimates so the UI can display "Not reported"
# rather than incorrectly treating missing values as zero.
national_df["wage_reported"] = national_df[
    "national_median_wage"
].notna()

state_df["wage_reported"] = state_df[
    "state_median_wage"
].notna()

state_df["employment_reported"] = state_df[
    "state_employment"
].notna()


# ---------------------------------------------------------------------
# Career Dropdown Options
# ---------------------------------------------------------------------

CAREER_OPTIONS = [
    {"label": title, "value": code}
    for code, title in (
        national_df
        .sort_values("national_occ_title")[
            ["occ_code", "national_occ_title"]
        ]
        .drop_duplicates()
        .values
    )
]


# Default to Data Scientists
DEFAULT_OCC = "15-2051"


# ---------------------------------------------------------------------
# Map Metrics
# ---------------------------------------------------------------------

# metric key:
# (
#     value column,
#     reported flag,
#     legend label,
#     card title,
#     money?
# )

METRICS = {
    "wage": (
        "state_median_wage",
        "wage_reported",
        "Median Annual Wage",
        "Median Annual Wage by State",
        True,
    ),
    "employment": (
        "state_employment",
        "employment_reported",
        "People Employed",
        "Number Employed by State",
        False,
    ),
}


# ---------------------------------------------------------------------
# Register Dash Page
# ---------------------------------------------------------------------

dash.register_page(
    __name__,
    path="/explore",
    name="Explore Career + Location",
)


# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------

def _fmt(val, kind="int"):
    """
    Format a raw value as money, percentage, plain number,
    or "Not reported" if missing.
    """

    if val is None or val != val:
        return "Not reported"

    if kind == "money":
        return f"${val:,.0f}"

    if kind == "pct":
        return f"{'▲' if val >= 0 else '▼'} {val:+.1f}%"

    return f"{val:,.0f}"


def _kpi(label, value, note=None, accent=False):
    """
    Build a KPI card with a label, value, and optional note.
    """

    return html.Div(
        [
            html.Div(label, className="kpi-label"),
            html.Div(value, className="kpi-value"),
        ]
        + (
            [html.Div(note, className="kpi-note")]
            if note
            else []
        ),
        className=(
            "kpi-card accent-amber"
            if accent
            else "kpi-card"
        ),
    )


def _blank(message):
    """
    Build an empty placeholder chart with a centered message.
    """

    fig = go.Figure()

    fig.update_layout(
        annotations=[
            {
                "text": message,
                "showarrow": False,
                "font": {
                    "size": 14,
                    "color": "#6b7280",
                },
            }
        ]
    )

    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)

    return fig


def _lookup(occ_code):
    """
    Return the national data row for an occupation code.
    """

    if not occ_code:
        return None

    row = national_df.loc[
        national_df["occ_code"] == occ_code
    ]

    if row.empty:
        return None

    return row.iloc[0]


def _control(label, component):
    """
    Wrap an input control in a consistent layout block.
    """

    return html.Div(
        [
            html.Label(
                label,
                className="control-label",
            ),
            component,
        ],
        className="control-block",
    )


def _chart_card(title, graph, extra=None):
    """
    Wrap a chart inside a titled card.
    """

    children = [
        html.Div(
            title,
            className="chart-card-title",
        ),
        graph,
    ]

    if extra is not None:
        children.append(extra)

    return html.Div(
        children,
        className="chart-card",
    )


# ---------------------------------------------------------------------
# Page Layout
# ---------------------------------------------------------------------

def layout():
    return html.Div(
        className="page-container",
        children=[
            html.Div(
                "Explore Career + Location",
                className="page-title",
            ),

            html.Div(
                (
                    "Pick a career to see its national profile and "
                    "where in the U.S. it pays best and employs the "
                    "most people."
                ),
                className="page-subtitle",
            ),

            html.Div(
                className="controls-row",
                children=[
                    _control(
                        "Career",
                        dcc.Dropdown(
                            id="p2-career-dropdown",
                            options=CAREER_OPTIONS,
                            value=DEFAULT_OCC,
                            clearable=False,
                            placeholder="Search for a career...",
                        ),
                    ),

                    _control(
                        "Map Shows",
                        dcc.RadioItems(
                            id="p2-map-metric",
                            options=[
                                {
                                    "label": metric_data[2],
                                    "value": metric_key,
                                }
                                for metric_key, metric_data
                                in METRICS.items()
                            ],
                            value="wage",
                            className="dash-radio-toggle",
                            inline=True,
                        ),
                    ),
                ],
            ),

            html.Div(
                id="p2-error-banner"
            ),

            html.Div(
                id="p2-kpi-row",
                className="kpi-row",
            ),

            html.Div(
                className="charts-one-col",
                children=[
                    _chart_card(
                        html.Span(
                            id="p2-map-title"
                        ),
                        dcc.Graph(
                            id="p2-choropleth",
                            config={
                                "displayModeBar": False
                            },
                        ),
                        html.Div(
                            id="p2-map-footnote",
                            className="footnote",
                        ),
                    )
                ],
            ),
        ],
    )


# ---------------------------------------------------------------------
# Callback: Update National Career Profile
# ---------------------------------------------------------------------

@callback(
    Output(
        "p2-error-banner",
        "children",
    ),
    Output(
        "p2-kpi-row",
        "children",
    ),
    Input(
        "p2-career-dropdown",
        "value",
    ),
)
def update_profile(occ_code):

    row = _lookup(occ_code)

    if row is None:
        if not occ_code:
            msg = (
                "Choose a career from the dropdown "
                "to see its profile."
            )
        else:
            msg = (
                f"No profile data found for "
                f"occupation code {occ_code}."
            )

        return (
            html.Div(
                msg,
                className="error-banner",
            ),
            [],
        )

    wage = (
        row["national_median_wage"]
        if row["wage_reported"]
        else None
    )

    return None, [
        _kpi(
            "Median Annual Wage",
            _fmt(wage, "money"),
            "National, 2025",
        ),

        _kpi(
            "Projected Growth",
            _fmt(
                row["growth_pct"],
                "pct",
            ),
            "2025 → 2035",
            accent=True,
        ),

        _kpi(
            "Annual Openings",
            _fmt(
                row["annual_openings"]
            ),
            "Per year, avg.",
        ),

        _kpi(
            "Employed (2025)",
            _fmt(
                row["employment_2025"]
            ),
            "Nationwide",
        ),

        _kpi(
            "Typical Education",
            row["education"],
            row["occupation_group"],
        ),
    ]


# ---------------------------------------------------------------------
# Callback: Update State Choropleth
# ---------------------------------------------------------------------

@callback(
    Output(
        "p2-choropleth",
        "figure",
    ),
    Output(
        "p2-map-title",
        "children",
    ),
    Output(
        "p2-map-footnote",
        "children",
    ),
    Input(
        "p2-career-dropdown",
        "value",
    ),
    Input(
        "p2-map-metric",
        "value",
    ),
)
def update_choropleth(occ_code, metric):

    col, flag, label, title, is_money = METRICS[metric]

    if occ_code:
        states = state_df.loc[
            state_df["occ_code"] == occ_code
        ].copy()
    else:
        states = state_df.iloc[:0].copy()

    if states.empty:
        if not occ_code:
            msg = (
                "Select a career to see where "
                "it's strongest."
            )
        else:
            msg = (
                "No state-level data available "
                "for this career."
            )

        return (
            _blank(msg),
            title,
            "",
        )

    # Create formatted hover values.
    states["hover_value"] = states[col].map(
        lambda value: _fmt(
            value,
            "money" if is_money else "int",
        )
    )

    # Create U.S. choropleth.
    fig = px.choropleth(
        states,
        locations="state",
        locationmode="USA-states",
        color=col,
        scope="usa",
        color_continuous_scale="Viridis",
        hover_name="state_name",
        custom_data=[
            "hover_value"
        ],
    )

    fig.update_traces(
        hovertemplate=(
            f"<b>%{{hovertext}}</b><br>"
            f"{label}: %{{customdata[0]}}"
            "<extra></extra>"
        )
    )

    # Overlay state abbreviations directly onto the map.
    fig.add_trace(
        go.Scattergeo(
            locations=states["state"],
            locationmode="USA-states",
            text=states["state"],
            mode="text",
            textfont=dict(
                size=9,
                color="#1f2937",
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Format map layout.
    fig.update_layout(
        margin=dict(
            l=0,
            r=0,
            t=10,
            b=0,
        ),
        coloraxis_colorbar_title=None,
        height=340,
        geo=dict(
            bgcolor="rgba(0,0,0,0)",
            lakecolor="white",
        ),
    )

    # Count missing or suppressed state estimates.
    n_missing = int(
        (~states[flag]).sum()
    )

    if n_missing:
        footnote = (
            f"{n_missing} state(s) have no reliable estimate "
            "for this career and are shown blank "
            "(BLS suppresses low-count data)."
        )
    else:
        footnote = ""

    return (
        fig,
        title,
        footnote,
    )
