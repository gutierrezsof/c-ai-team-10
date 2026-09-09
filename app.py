import dash
from dash import html, dcc

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
)

app.title = "Career Explorer"

nav_links = [
    dcc.Link(
        page["name"],
        href=page["path"],
        className="nav-link",
    )
    for page in dash.page_registry.values()
]

app.layout = html.Div(
    [
        html.Header(
            className="site-header",
            children=[
                html.Div(
                    className="nav-shell",
                    children=[
                        dcc.Link(
                            "Career Compass",
                            href="/",
                            className="brand-link",
                        ),
                        html.Nav(
                            className="nav-bar",
                            children=nav_links,
                        ),
                    ],
                )
            ],
        ),
        html.Main(
            className="app-main",
            children=dash.page_container,
        ),
    ],
    className="app-shell",
)

if __name__ == "__main__":
    app.run(debug=True)