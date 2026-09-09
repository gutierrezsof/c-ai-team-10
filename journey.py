"""
journey.py — the wandering guide (Sammie) who turns up on every page.

Sammie is drawn once in assets/sammie.svg. This helper drops her into a
different corner of each page as a fixed-position, non-interactive figure that
is hidden on narrow screens, so she reads as a recurring character without ever
sitting on top of a chart. It's a visual thread, not a progress bar — the
narrative itself lives on the home page (pages/home.py).

Usage in a page module:

    from journey import wanderer
    layout = html.Div([wanderer("page1"), ...])

Corners: "tl", "tr", "ml" (mid-left), "bl", "br". Positions and the screen
width at which she appears are all in assets/styles.css under ".wander".
"""

from dash import html

# One corner per page. Keys match each page's route stem.
_CORNERS = {
    "home": "bl",
    "page1": "tr",
    "explore": "ml",
    "compare": "br",
    "ranking": "tl",
}


def wanderer(page_key, corner=None):
    spot = corner or _CORNERS.get(page_key, "br")
    return html.Div(
        className=f"wander wander--{spot}",
        children=html.Img(src="/assets/sammie.svg", alt="", className="wander-img"),
        **{"aria-hidden": "true"},
    )
