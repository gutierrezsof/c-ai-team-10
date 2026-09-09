######################################## AI USE DISCLOSURE ##############################################

# AI Model Used: ChatGPT and Claude
#
# Used ChatGPT and Claude to help generate/debug the following when creating the App.PY page:
#   - Overall page skeleton and format structure
#   - Navigation Bar
#
# Team member reviewed, tested, and made edits/revisions to all code before including it in the app.
########################################################################################################



import dash
from dash import html, dcc

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
)
server = app.server
app.title = "Career Explorer"


# ---------------------------------------------------------
# NAVIGATION LINKS
# Define these manually so the navbar always appears
# in the exact order you want.
# ---------------------------------------------------------
nav_links = [
    dcc.Link(
        "Career Landscape",
        href="/page1",
        className="nav-link",
    ),
    dcc.Link(
        "Career Match",
        href="/ranking",
        className="nav-link",
    ),
    dcc.Link(
        "Compare Careers",
        href="/compare-careers",
        className="nav-link",
    ),
    dcc.Link(
        "Explore Career + Location",
        href="/explore",
        className="nav-link",
    ),
]


# ---------------------------------------------------------
# APP LAYOUT
# ---------------------------------------------------------
app.layout = html.Div(
    [
        html.Header(
            className="site-header",
            children=[
                html.Div(
                    className="nav-shell",
                    children=[

                        # Logo / Home button
                        dcc.Link(
                            "Career Compass",
                            href="/",
                            className="brand-link",
                        ),

                        # Main navigation
                        html.Nav(
                            className="nav-bar",
                            children=nav_links,
                        ),
                    ],
                )
            ],
        ),

        # Current Dash page appears here
        html.Main(
            className="app-main",
            children=dash.page_container,
        ),
    ],
    className="app-shell",
)


if __name__ == "__main__":
    app.run(debug=True)