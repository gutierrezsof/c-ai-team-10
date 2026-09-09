##Imports
import dash
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import pandas as pd

##Loading Page
print("Loading page1_career_landscape.py...")


dash.register_page(__name__, path="/page1", name="Career Landscape", order=1)


print("Page registered successfully")

# --- Load both datasets ------------------------------------------------------
nat_df = pd.read_csv("data/national_careers.csv")
state_df = pd.read_csv("data/state_careers.csv")

# Strip whitespaces from national file so the titles match cleanly everywhere
nat_df["national_occ_title"] = nat_df["national_occ_title"].str.strip()

# --- We merged the two datasets to attach growth_pct and annual_openings onto the state rows -------
# occ_code is the shared key. This is a LEFT join on state_df so every state
# row is kept even if national_careers.csv is ever missing that code; growth
# and openings just come back NaN for those few rows instead of dropping them.
merged_df = state_df.merge(
    nat_df[["occ_code", "growth_pct", "annual_openings", "occupation_group"]],
    on="occ_code",
    how="left",
)
#print(merged_df.shape)

# --- Dropdown 1 options: occupation group  -----------
group_options = [{"label": "All Occupations", "value": "ALL"}] + [
    {"label": g, "value": g} for g in sorted(nat_df["occupation_group"].dropna().unique())
]

# --- Dropdown 2 options: By individual state -----------------------------------------------
state_lookup = state_df[["state", "state_name"]].drop_duplicates().sort_values("state_name")
state_options = [{"label": "National (All States)", "value": "NATIONAL"}] + [
    {"label": row["state_name"], "value": row["state"]}
    for _, row in state_lookup.iterrows()
]

OPENING_BINS = [0, 1000, 5000, 10000, 20000, 50000, float("inf")]
OPENING_LABELS = ["<1,000", "1,000-5,000", "5,000-10,000", "10,000-20,000", "20,000-50,000", "50,000+"]
OPENING_COLORS = {
    "<1,000": "#2166ac",
    "1,000-5,000": "#67a9cf",
    "5,000-10,000": "#d1e5f0",
    "10,000-20,000": "#fddbc7",
    "20,000-50,000": "#ef8a62",
    "50,000+": "#b2182b",
}

layout = html.Div(className="page-container", children=[

    html.Div(className="page-title", children="Career Opportunity Explorer"),
    html.Div(
        className="page-subtitle",
        children="Which careers offer the best combination of salary, "
                 "job growth, and employment opportunities?",
    ),

    html.Div(className="controls-row", children=[

    html.Div(className="dropdown-group", children=[
        html.Label("Select Occupation Group", className="control-label"),
        dcc.Dropdown(
            id="group-filter",
            options=group_options,
            value="Business and Financial",   # Sammie's field (home-page example)
            clearable=False,
            className="dropdown",
        ),
    ]),

    html.Div(className="dropdown-group", children=[
        html.Label("Select State", className="control-label"),
        dcc.Dropdown(
            id="state-filter",
            options=state_options,
            value="VA",   # Sammie's home state (home-page example)
            clearable=False,
            className="dropdown",
        ),
    ]),

]),

    # Chart comes first, KPIs moved below it
    html.Div(className="chart-card", children=[
        dcc.Graph(id="wage-growth-scatter"),
        html.Div(
            "— — — Dashed line = Median Annual Wage    |    ── Solid line = Median Projected Growth",
            className="chart-caption",
        ),
    ]),

    html.Div(id="kpi-row", className="kpi-row"),

    # NEW: shows a short note when a state is selected, since growth and
    # openings numbers on that view are still national, not state-specific.
    html.Div(id="state-note", className="source-note"),

    html.Div(className="source-note", children=[
        "Source: ",
        html.A(
            "U.S. Bureau of Labor Statistics, Employment Projections program — Table 1.2",
            href="https://www.bls.gov/emp/data/occupational-data.htm",
            target="_blank",
        ),
    ]),
])


@callback(
    Output("kpi-row", "children"),
    Output("wage-growth-scatter", "figure"),
    Output("state-note", "children"),
    Input("group-filter", "value"),
    Input("state-filter", "value"),   # NEW second input -- order must match
)                                     # the function arguments below
def update_page(selected_group, selected_state):

    # --- Pick which dataset to work from -------------------------------------
    if selected_state == "NATIONAL":
        # Original behavior: national file, national wage column, no note.
        dff = nat_df.copy()
        wage_col = "national_median_wage"
        title_col = "national_occ_title"
        note = ""
    else:
        # State view: filter the merged file down to one state.
        dff = merged_df[merged_df["state"] == selected_state].copy()
        wage_col = "state_median_wage"
        title_col = "occ_title"
        state_name = state_lookup.loc[state_lookup["state"] == selected_state, "state_name"].iloc[0]
        note = (f"Wage and employment are for {state_name}. Growth and annual "
                f"openings are national figures -- state-level projections "
                f"are not published.")

    # --- Occupation group filter (applies on top of the state choice) -------
    if selected_group != "ALL":
        dff = dff[dff["occupation_group"] == selected_group]

    # --- Guard: the combination above produced zero rows ---------------------
    # Can happen with a real but rare combination -- e.g. a group whose wages
    # are entirely suppressed in a small state. Show a message instead of
    # crashing on an empty DataFrame.
    dff = dff.dropna(subset=[wage_col, "growth_pct", "annual_openings"])
    if dff.empty:
        empty_kpis = [html.Div("No data available for this selection.", className="kpi-label")]
        return empty_kpis, px.scatter(title="No data for this selection"), note

    # --- Bin annual openings for the color-coded legend ---------------------
    dff["openings_bin"] = pd.cut(
        dff["annual_openings"],
        bins=OPENING_BINS,
        labels=OPENING_LABELS,
        include_lowest=True,
    )

    # --- Build a dynamic chart title from the two filters --------------------
    group_label = "All Occupations" if selected_group == "ALL" else selected_group
    if selected_state == "NATIONAL":
        chart_title = f"Median Wage vs. Projected Growth for {group_label} Jobs (National)"
    else:
        chart_title = f"Median Wage vs. Projected Growth for {group_label} Jobs in {state_name}"

    # --- KPIs ------------------------------------------------------------
    kpis = [
        html.Div(className="kpi-card", children=[
            html.Div("Median Annual Wage", className="kpi-label"),
            html.Div(f"${dff[wage_col].median():,.0f}", className="kpi-value"),
        ]),
        html.Div(className="kpi-card", children=[
            html.Div("Median Projected Growth", className="kpi-label"),
            html.Div(f"{dff['growth_pct'].median():.1f}%", className="kpi-value"),
        ]),
        html.Div(className="kpi-card", children=[
            html.Div("Total Annual Job Openings", className="kpi-label"),
            html.Div(f"{dff['annual_openings'].sum():,.0f}", className="kpi-value"),
        ]),
        html.Div(className="kpi-card", children=[
            html.Div("Total Employment, 2025", className="kpi-label"),
            html.Div(
                f"{dff['employment_2025'].sum():,.0f}" if selected_state == "NATIONAL"
                else f"{dff['state_employment'].sum():,.0f}",
                className="kpi-value",
            ),
        ]),
    ]

    # --- Scatterplot Graphic -----------------------------------------------------------
    fig = px.scatter(
        dff,
        x="growth_pct",
        y=wage_col,
        size="annual_openings",
        color="openings_bin",
        category_orders={"openings_bin": OPENING_LABELS},
        color_discrete_map=OPENING_COLORS,
        hover_name=title_col,
        size_max=45,
        labels={
            "growth_pct": "Projected Employment Growth (%), 2025–35",
            wage_col: "Median Annual Wage ($)",
            "openings_bin": "Annual Openings",
        },
        title=chart_title,
    )

    fig.add_hline(y=dff[wage_col].median(), line_dash="dot", opacity=0.4,
                  annotation_text=f"Median: ${dff[wage_col].median():,.0f}", annotation_position="top left")
    fig.add_vline(x=dff["growth_pct"].median(), line_dash="solid", opacity=0.4,
                  annotation_text=f"Median: {dff['growth_pct'].median():.1f}%", annotation_position="top right")
    fig.update_layout(
        template="plotly_white",
        margin=dict(t=90, l=10, r=10, b=10),
        title=dict(
            font=dict(size=18, family="Arial Black"),
        ),
    )

    return kpis, fig, note