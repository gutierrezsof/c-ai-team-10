"""
pages/home.py — Career Compass landing page

The landing page frames the four analysis pages as a simple four-step
career exploration flow:

    01 Career Landscape        -> get oriented (the whole market)
    02 Career Match            -> make it personal (rank by what you value)
    03 Compare Careers         -> narrow it down (a short list, head to head)
    04 Explore Career+Location -> zoom in (one career, in depth)

Theme: compass / wayfinding. Reuses the shared design system in
assets/styles.css (.kpi-row / .kpi-card, .source-note) and adds the .home-*
classes at the end of that file.

Data: national_careers.csv, read once at import for the "at a glance" strip.
"""

import os
import dash
from dash import html, dcc
import pandas as pd


# ---------------------------------------------------------------------------
# Register Home Page
# ---------------------------------------------------------------------------

dash.register_page(
    __name__,
    path="/",
    name="Home",
    title="Career Compass",
    order=0,
)


# ---------------------------------------------------------------------------
# Data — headline numbers for the "at a glance" strip
# ---------------------------------------------------------------------------

_DIRS = [
    os.path.dirname(os.path.abspath(__file__)),
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    os.getcwd(),
    os.path.join(os.getcwd(), "data"),
]


def _read(filename):
    for d in _DIRS:
        path = os.path.join(d, filename)

        if os.path.exists(path):
            return pd.read_csv(path)

    raise FileNotFoundError(
        f"Couldn't find {filename}. Looked in: {_DIRS}"
    )


_nat = _read("national_careers.csv")

_nat["national_occ_title"] = (
    _nat["national_occ_title"]
    .astype(str)
    .str.strip()
)


# Keep only individual occupations.
_jobs = _nat[_nat["occupation_type"] == "line item"]

if _jobs.empty:
    _jobs = _nat


STATS = {
    "careers": len(_jobs),
    "median_wage": _jobs["national_median_wage"].median(),
    "groups": _jobs["occupation_group"].nunique(),
    "openings": _jobs["annual_openings"].sum(),
}


# ---------------------------------------------------------------------------
# Career Exploration Steps
# ---------------------------------------------------------------------------

STOPS = [
    {
        "num": "01",
        "name": "Career Landscape",
        "href": "/page1",
        "spot": "spot-binoculars.svg",
        "question": "What's even out there, and where are the good spots?",
        "does": (
            "One scatter of every occupation: median pay against projected "
            "growth, sized by how many openings it adds each year. Filter by "
            "field or by state to read the shape of the whole market."
        ),
    },
    {
        "num": "02",
        "name": "Career Match",
        "href": "/ranking",
        "spot": "spot-target.svg",
        "question": "Okay — which one fits what I care about?",
        "does": (
            "Set how much salary, projected growth, and job availability each "
            "matter to you. The page scores every career on your weights and "
            "ranks the top ten."
        ),
    },
    {
        "num": "03",
        "name": "Compare Careers",
        "href": "/compare-careers",
        "spot": "spot-scale.svg",
        "question": "I've got a short list. Which one actually wins?",
        "does": (
            "Put two to five careers side by side on median wage, with an "
            "optional growth comparison, so the trade-offs are impossible to "
            "miss."
        ),
    },
    {
        "num": "04",
        "name": "Explore Career + Location",
        "href": "/explore",
        "spot": "spot-lens.svg",
        "question": "One of these caught my eye — what's it actually like?",
        "does": (
            "Pick a single career for its national profile — pay, growth, "
            "openings, typical education — plus a U.S. map of where it pays "
            "best and employs the most people."
        ),
    },
]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _kpi(label, value):
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(
                label,
                className="kpi-label",
            ),
            html.Div(
                value,
                className="kpi-value",
            ),
        ],
    )


def _stop_card(stop):
    return dcc.Link(
        href=stop["href"],
        className="home-step",
        children=[

            html.Img(
                src=f"/assets/{stop['spot']}",
                alt="",
                className="home-step-spot",
                **{"aria-hidden": "true"},
            ),

            html.Div(
                stop["num"],
                className="home-step-badge",
            ),

            html.Div(
                className="home-step-body",
                children=[

                    html.H3(
                        stop["name"],
                        className="home-step-name",
                    ),

                    html.P(
                        stop["question"],
                        className="home-step-q",
                    ),

                    html.P(
                        stop["does"],
                        className="home-step-do",
                    ),

                    html.Span(
                        "Open this stop →",
                        className="home-step-go",
                    ),
                ],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Page Layout
# ---------------------------------------------------------------------------

layout = html.Div(
    className="home",
    children=[

        # -------------------------------------------------------------------
        # Hero
        # -------------------------------------------------------------------

        html.Div(
            className="home-hero",
            children=[

                html.Div(
                    className="home-hero-copy",
                    children=[

                        html.H1(
                            "Find your dream career!"
                        ),

                        html.P(
                            f"{STATS['careers']:,} U.S. occupations, charted by "
                            "pay, projected growth, and hiring demand. Use the "
                            "four tools below to explore the market, compare "
                            "options, and focus on the roles that match what "
                            "you value."
                        ),

                        dcc.Link(
                            "Start exploring →",
                            href="/page1",
                            className="home-cta",
                        ),
                    ],
                ),

                html.Div(
                    className="home-hero-art",
                    **{"aria-hidden": "true"},
                    children=[
                        html.Div(
                            className="home-compass"
                        ),
                    ],
                ),
            ],
        ),


        # -------------------------------------------------------------------
        # Career Market At A Glance
        # -------------------------------------------------------------------

        html.Div(
            className="home-glance",
            children=[

                html.Div(
                    "The map at a glance",
                    className="home-section-title",
                ),

                html.Div(
                    className="kpi-row",
                    children=[

                        _kpi(
                            "Careers charted",
                            f"{STATS['careers']:,}",
                        ),

                        _kpi(
                            "Median annual wage",
                            f"${STATS['median_wage']:,.0f}",
                        ),

                        _kpi(
                            "Occupation groups",
                            f"{STATS['groups']}",
                        ),

                        _kpi(
                            "Openings per year, all careers",
                            f"{STATS['openings'] / 1_000_000:.1f}M",
                        ),
                    ],
                ),
            ],
        ),


        # -------------------------------------------------------------------
        # Career Exploration Tools
        # -------------------------------------------------------------------

        html.Div(
            "Explore the career tools",
            className="home-section-title",
        ),

        html.Div(
            "Four tools, each helping you answer a different career question.",
            className="home-section-sub",
        ),

        html.Div(
            className="home-route",
            children=[
                _stop_card(stop)
                for stop in STOPS
            ],
        ),


        # -------------------------------------------------------------------
        # Source
        # -------------------------------------------------------------------

        html.Div(
            "Data: U.S. Bureau of Labor Statistics — Occupational Employment "
            "& Wage Statistics and Employment Projections, 2025–35.",
            className="source-note home-foot",
        ),
    ],
)