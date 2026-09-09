######################################## AI USE DISCLOSURE ##############################################

# AI Model Used: ChatGPT
#
# Used ChatGPT to help generate/debug the following when creating the Career Match page:
#   - Overall page skeleton and layout structure
#   - Occupation group dropdown and filtering logic
#   - Salary, growth, and job opportunity sliders
#   - Weighted opportunity score calculation
#   - Top 10 career ranking chart and summary
#   - Code comments, organization, and debugging
#
# Team member reviewed, tested, and made edits/revisions to all code before including it in the app.
########################################################################################################


import dash
from dash import html, dcc, callback, Input, Output
import pandas as pd
import plotly.express as px


# ============================================================
# PAGE SETUP
# ============================================================

dash.register_page(
    __name__,
    path="/ranking",
    name="Career Match",
    order=2,
)


# ============================================================
# LOAD + CLEAN DATA
# ============================================================

df = pd.read_csv(
    "data/national_careers.csv",
    dtype={"occ_code": str}
)

df["national_occ_title"] = (
    df["national_occ_title"]
    .astype(str)
    .str.strip()
)

df = df.dropna(
    subset=[
        "national_occ_title",
        "occupation_group",
        "salary_score",
        "growth_score",
        "openings_score",
        "national_median_wage",
        "growth_pct",
        "annual_openings"
    ]
).copy()


# ============================================================
# DROPDOWN OPTIONS
# ============================================================

group_options = [
    {"label": "All Occupations", "value": "ALL"},
    *[
        {"label": group, "value": group}
        for group in sorted(df["occupation_group"].unique())
    ]
]


# ============================================================
# PAGE LAYOUT
# ============================================================

layout = html.Div(
    className="page-container",
    children=[

        html.H1("Career Opportunity Ranking", className="page-title"),
        html.P(
            "Which careers offer the best combination of salary, projected "
            "growth, and employment opportunities based on what matters most "
            "to you?",
            className="page-subtitle",
        ),

        # --- Occupation group filter ------------------------------------------
        html.Div(
            className="controls-row",
            children=[
                html.Div(
                    className="dropdown-group",
                    children=[
                        html.Label("Occupation Group", className="control-label"),
                        dcc.Dropdown(
                            id="occupation-group-dropdown",
                            options=group_options,
                            value="Computer and Mathematical",  # Sammie's field
                            clearable=False,
                            className="dropdown",
                        ),
                    ],
                ),
            ],
        ),


        # --- Priority sliders -----------------------------------------------
        # Defaults reflect Sammie: stability first, so job openings and growth
        # outweigh salary.
        html.Div(
            className="chart-card",
            style={"display": "flex", "flexDirection": "column",
                   "gap": "26px", "padding": "22px 18px 18px"},
            children=[
                html.Div(className="dropdown-group", children=[
                    html.Label("Salary Importance", className="control-label"),
                    dcc.Slider(
                        id="salary-weight", min=0, max=100, step=5, value=15,
                        marks={0: "0", 25: "25", 50: "50", 75: "75", 100: "100"},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                ]),
                html.Div(className="dropdown-group", children=[
                    html.Label("Growth Importance", className="control-label"),
                    dcc.Slider(
                        id="growth-weight", min=0, max=100, step=5, value=35,
                        marks={0: "0", 25: "25", 50: "50", 75: "75", 100: "100"},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                ]),
                html.Div(className="dropdown-group", children=[
                    html.Label("Job Opportunities Importance", className="control-label"),
                    dcc.Slider(
                        id="openings-weight", min=0, max=100, step=5, value=50,
                        marks={0: "0", 25: "25", 50: "50", 75: "75", 100: "100"},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                ]),
            ],
        ),


        html.Div(
            id="normalized-weight-display",
            style={"textAlign": "center", "fontWeight": "600",
                   "color": "var(--text-soft)", "margin": "6px 0 22px"},
        ),

        # --- Results: ranking chart + your top career ------------------------
        html.Div(
            style={"display": "flex", "gap": "22px", "alignItems": "stretch",
                   "flexWrap": "wrap"},
            children=[
                html.Div(
                    className="chart-card",
                    style={"flex": "2", "minWidth": "520px"},
                    children=[
                        dcc.Graph(id="career-ranking-chart",
                                  config={"displayModeBar": False}),
                    ],
                ),
                html.Div(
                    className="chart-card",
                    style={"flex": "1", "minWidth": "280px"},
                    children=[
                        html.H2("Your Top Career", style={"marginTop": "0"}),
                        html.Div(id="top-career-explanation"),
                    ],
                ),
            ],
        ),

    ],
)


# ============================================================
# CALLBACK
# ============================================================

@callback(
    Output("career-ranking-chart", "figure"),
    Output("normalized-weight-display", "children"),
    Output("top-career-explanation", "children"),

    Input("occupation-group-dropdown", "value"),
    Input("salary-weight", "value"),
    Input("growth-weight", "value"),
    Input("openings-weight", "value")
)
def update_ranking(
    selected_group,
    salary_weight,
    growth_weight,
    openings_weight
):

    # --------------------------------------------------------
    # NORMALIZE USER WEIGHTS
    # --------------------------------------------------------

    total = salary_weight + growth_weight + openings_weight

    if total == 0:
        salary_n = growth_n = openings_n = 1 / 3
    else:
        salary_n = salary_weight / total
        growth_n = growth_weight / total
        openings_n = openings_weight / total


    # --------------------------------------------------------
    # FILTER BY OCCUPATION GROUP
    # --------------------------------------------------------

    ranking = df.copy()

    if selected_group != "ALL":
        ranking = ranking[
            ranking["occupation_group"] == selected_group
        ].copy()


    # --------------------------------------------------------
    # CALCULATE OPPORTUNITY SCORE
    # --------------------------------------------------------

    ranking["opportunity_score"] = (
        ranking["salary_score"] * salary_n
        + ranking["growth_score"] * growth_n
        + ranking["openings_score"] * openings_n
    )


    # --------------------------------------------------------
    # TOP 10 CAREERS
    # --------------------------------------------------------

    top10 = (
        ranking
        .nlargest(10, "opportunity_score")
        .sort_values("opportunity_score")
        .copy()
    )

    top10["score_label"] = (
        top10["opportunity_score"]
        .map(lambda x: f"{x:.1f}")
    )


    # --------------------------------------------------------
    # CREATE GRAPH
    # --------------------------------------------------------

    fig = px.bar(
        top10,
        x="opportunity_score",
        y="national_occ_title",
        orientation="h",
        text="score_label",
        title="Top 10 Career Opportunities",

        labels={
            "opportunity_score": "Career Opportunity Score",
            "national_occ_title": ""
        },

        hover_data={
            "national_median_wage": ":$,.0f",
            "growth_pct": ":.1f",
            "annual_openings": ":,.0f",
            "salary_score": ":.1f",
            "growth_score": ":.1f",
            "openings_score": ":.1f",
            "score_label": False
        }
    )

    fig.update_traces(
        textposition="outside"
    )

    fig.update_layout(
        template="plotly_white",
        height=520,

        title={
            "x": 0.5,
            "xanchor": "center"
        },

        xaxis={
            "title": "Career Opportunity Score",
            "range": [0, 105]
        },

        yaxis_title="",

        margin={
            "l": 190,
            "r": 40,
            "t": 70,
            "b": 50
        }
    )


    # --------------------------------------------------------
    # NORMALIZED WEIGHT TEXT
    # --------------------------------------------------------

    salary_pct = salary_n * 100
    growth_pct = growth_n * 100
    openings_pct = openings_n * 100

    weight_text = (
        f"Normalized Weights: "
        f"Salary {salary_pct:.0f}% | "
        f"Growth {growth_pct:.0f}% | "
        f"Job Opportunities {openings_pct:.0f}%"
    )


    # --------------------------------------------------------
    # FIND #1 CAREER
    # --------------------------------------------------------

    top = ranking.nlargest(
        1,
        "opportunity_score"
    ).iloc[0]

    career = top["national_occ_title"]
    score = top["opportunity_score"]
    wage = top["national_median_wage"]
    growth = top["growth_pct"]
    openings = top["annual_openings"]


    # --------------------------------------------------------
    # BUILD #1 CAREER CARD
    # --------------------------------------------------------

    explanation = html.Div(
        [

            html.H3(
                career,
                style={
                    "marginBottom": "5px"
                }
            ),

            html.P(
                f"Opportunity Score: {score:.1f}",
                style={
                    "fontWeight": "bold",
                    "fontSize": "18px"
                }
            ),

            html.Hr(),

            html.P([
                html.Strong("Median Salary"),
                html.Br(),
                f"${wage:,.0f}"
            ]),

            html.P([
                html.Strong("Projected Growth"),
                html.Br(),
                f"{growth:.1f}%"
            ]),

            html.P([
                html.Strong("Annual Openings"),
                html.Br(),
                f"{openings:,.0f}"
            ]),

            html.Hr(),

            html.P([
                html.Strong("Your Priorities"),
                html.Br(),
                f"Salary: {salary_pct:.0f}%",
                html.Br(),
                f"Growth: {growth_pct:.0f}%",
                html.Br(),
                f"Job Opportunities: {openings_pct:.0f}%"
            ])

        ],
        style={
            "fontSize": "17px",
            "lineHeight": "1.6"
        }
    )

    return (
        fig,
        weight_text,
        explanation
    )
