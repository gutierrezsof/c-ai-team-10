########################################   AI USE DISCLOSURE ##############################################

# AI Model Used: Claude 
#
#
# Design & feature decisions (made by team member, not AI):
#   - Big picture ideas and design
#   - Choice to include two dropdown filters for plot (state and occupation group)
#   - Decision to show a national-vs-state note explaining that growth/openings
#     figures are always national (no state-level projections exist)
#   - Choice of KPIs shown (median wage, median growth, total openings, total employment)
#   - Choice to bin annual openings into buckets and color the scatter by bucket,
#     and to add median reference lines to the chart
#
# Used Claude to help generate/debug the following when creating page 1:
#   - Overall page skeleton/layout structure (controls row, chart card, and KPI row)
#   - The merge of state_careers.csv and national_careers.csv on occ_code to
#     attach growth_pct/annual_openings/occupation_group onto state-level rows
#   - The update_page() callback logic for switching between the national
#     dataframe and the state-filtered merged dataframe (different wage/title
#     columns depending on selected_state)
#   - The pd.cut() bin setup for annual_openings and the OPENING_COLORS map
#   - The empty-selection guard (dff.empty check) returning a "No data" message
#     instead of erroring
#   - Plotly Express scatter code, including add_hline/add_vline for the median
#     reference lines and layout/title styling
#   - Troubleshooting (including error messages)
#   - If/Else Statement Adjustments
#
# Team member reviewed, tested, and made edits/revisions to all code before including it in the app

###########################################################################################################

##Imports
import dash
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import pandas as pd

##Loading Page
print("Loading page1_career_landscape.py...")


dash.register_page(__name__, path="/page1", name="Career Landscape")


print("Page registered successfully")

# Load national and state datasets
nat_df = pd.read_csv("data/national_careers.csv")
state_df = pd.read_csv("data/state_careers.csv")

# Strip whitespaces from national file so the titles match cleanly everywhere
nat_df["national_occ_title"] = nat_df["national_occ_title"].str.strip()

# We merged the two datasets to attach growth_pct and annual_openings onto the state rows. occ_code is the shared key.
merged_df = state_df.merge(
    nat_df[["occ_code", "growth_pct", "annual_openings", "occupation_group"]],
    on="occ_code",
    how="left",
)


#Dropdown 1 options: occupation group
group_options = [{"label": "All Occupations", "value": "ALL"}] + [
    {"label": g, "value": g} for g in sorted(nat_df["occupation_group"].dropna().unique())
]

#Dropdown 2 options: Select a state 
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

##layout (html.Div container, Title, Subtitle, Dropdowns)
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
            value="Computer and Mathematical",
            clearable=False,
            className="dropdown",
        ),
    ]),

    html.Div(className="dropdown-group", children=[
        html.Label("Select State", className="control-label"),
        dcc.Dropdown(
            id="state-filter",
            options=state_options,
            value="VA",
            clearable=False,
            className="dropdown",
        ),
    ]),

]),

    # Creates boxes for chart and our KPI Values beneath the chart
    html.Div(className="chart-card", children=[
        dcc.Graph(id="wage-growth-scatter"),
        html.Div(
            "— — — Dashed line = Median Annual Wage    |    ── Solid line = Median Projected Growth",
            className="chart-caption",
        ),
    ]),

    html.Div(id="kpi-row", className="kpi-row"),

    # Original Bureau of Labor Statistics source inside html.A
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

#callback for scatter and kpi outputs
@callback(
    Output("kpi-row", "children"),
    Output("wage-growth-scatter", "figure"),
    Output("state-note", "children"),
    Input("group-filter", "value"),
    Input("state-filter", "value"),  
)                                     
def update_page(selected_group, selected_state):

    #Selecting a dataset
    if selected_state == "NATIONAL":
        #National file, National wage column, no note.
        dff = nat_df.copy()
        wage_col = "national_median_wage"
        title_col = "national_occ_title"
        note = ""
    else:
        # State view: filter the merged file down to one state.
        dff = merged_df[merged_df["state"] == selected_state].copy()
        wage_col = "state_median_wage"
        title_col = "occ_title"
        lookup_result = state_lookup.loc[state_lookup["state"] == selected_state, "state_name"]
        state_name = lookup_result.iloc[0] if not lookup_result.empty else selected_state
        note = (f"Wage and employment are for {state_name}. Growth and annual "
                f"openings are national figures -- state-level projections "
                f"are not published.")

    # Filtering by occupation group (applies on top of the state choice) -------
    if selected_group != "ALL":
        dff = dff[dff["occupation_group"] == selected_group]

    # Show error message in case combination of selections does not feature any observations
    dff = dff.dropna(subset=[wage_col, "growth_pct", "annual_openings"])
    if dff.empty:
        empty_kpis = [html.Div("No data available for this selection.", className="kpi-label")]
        return empty_kpis, px.scatter(title="No data for this selection"), note

    # Establishes bins for different ranges of annual openings
    dff["openings_bin"] = pd.cut(
        dff["annual_openings"],
        bins=OPENING_BINS,
        labels=OPENING_LABELS,
        include_lowest=True,
    )

    # Adjust the scatter plot title based the two dropdown filters 
    group_label = "All Occupations" if selected_group == "ALL" else selected_group
    if selected_state == "NATIONAL":
        chart_title = f"Median Wage vs. Projected Growth for {group_label} Jobs (National)"
    else:
        chart_title = f"Median Wage vs. Projected Growth for {group_label} Jobs in {state_name}"

    # KPIs (Median Annual Wage, Total Job Openings, Total Annual Job Openings, Total Employment 2025)
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

    # Page 1 Scatterplot Graphic
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
# Add horizontal line for Median Annual Wage and vertical line for Projected Employment Growth Percentage
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
