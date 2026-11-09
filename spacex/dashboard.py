"""Interactive Plotly Dash dashboard for the SpaceX Falcon 9 capstone."""
from pathlib import Path
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "outputs" / "launches_clean.csv"
if not DATA.exists():
    raise FileNotFoundError("Run 'python spacex/analysis.py' first to create outputs/launches_clean.csv")
df = pd.read_csv(DATA)
app = Dash(__name__)
sites = ["All"] + sorted(df["LaunchSite"].dropna().unique().tolist())
app.layout = html.Div([
    html.H1("SpaceX Falcon 9 — Launch & Landing Dashboard"),
    html.P("Historical educational dataset; filter by launch site and payload range."),
    html.Label("Launch site"),
    dcc.Dropdown(sites, "All", id="site", clearable=False),
    html.Label("Payload mass (kg)"),
    dcc.RangeSlider(0, int(df["PayloadMass"].max() // 1000 * 1000 + 1000),
                    1000, value=[0, int(df["PayloadMass"].max() // 1000 * 1000 + 1000)],
                    id="payload"),
    html.Div(id="summary", style={"padding": "12px", "fontWeight": "bold"}),
    dcc.Graph(id="success-pie"),
    dcc.Graph(id="payload-scatter"),
    dcc.Graph(id="year-chart"),
], style={"maxWidth": "1100px", "margin": "auto", "fontFamily": "Arial"})

@app.callback(
    Output("summary", "children"), Output("success-pie", "figure"),
    Output("payload-scatter", "figure"), Output("year-chart", "figure"),
    Input("site", "value"), Input("payload", "value"))
def update(site, payload):
    d = df[df["PayloadMass"].between(payload[0], payload[1])].copy()
    if site != "All":
        d = d[d["LaunchSite"] == site]
    n = len(d)
    rate = d["Class"].mean() * 100 if n else 0
    pie = px.pie(d, names="Landing outcome", title="Landing outcomes",
                 hole=.35) if n else px.pie(title="No launches in this selection")
    if n:
        d["Landing outcome"] = d["Class"].map({1: "Successful", 0: "Unsuccessful"})
        pie = px.pie(d, names="Landing outcome", title="Landing outcomes", hole=.35)
        scatter = px.scatter(d, x="PayloadMass", y="Class", color="LaunchSite",
                             hover_data=["FlightNumber", "Orbit"],
                             title="Payload mass vs. landing outcome")
        d["Year"] = pd.to_datetime(d["Date"]).dt.year
        yearly = d.groupby("Year", as_index=False)["Class"].mean()
        yearly["Success rate (%)"] = yearly["Class"] * 100
        trend = px.line(yearly, x="Year", y="Success rate (%)", markers=True,
                        title="Annual landing success rate")
    else:
        scatter = px.scatter(title="No launches in this selection")
        trend = px.line(title="No launches in this selection")
    return f"{n} launches | Landing success rate: {rate:.1f}%", pie, scatter, trend

if __name__ == "__main__":
    app.run(debug=True)
