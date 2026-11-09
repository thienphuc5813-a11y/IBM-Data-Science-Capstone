"""Interactive Plotly Dash dashboard.
Run from repository root: python dashboard/app.py
"""
from pathlib import Path
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "outputs" / "cleaned_automobile_sales.csv"
if not DATA_PATH.exists():
    raise FileNotFoundError("Run 'python src/analysis.py' first to create outputs/cleaned_automobile_sales.csv")
df = pd.read_csv(DATA_PATH)
df["Date"] = pd.to_datetime(df["Date"])

app = Dash(__name__)
app.title = "Automobile Sales Insights"
app.layout = html.Div([
    html.H1("Historical Automobile Sales Insights"),
    html.P("Educational analysis of a synthetic IBM course dataset (1980–2023)."),
    html.Div([
        html.Label("Economic period"),
        dcc.Dropdown(
            id="period-filter",
            options=[{"label":"All periods","value":"all"},
                     {"label":"Recession","value":"1"},
                     {"label":"Non-recession","value":"0"}],
            value="all", clearable=False
        ),
        html.Label("Vehicle type"),
        dcc.Dropdown(
            id="vehicle-filter",
            options=[{"label":v,"value":v} for v in sorted(df["Vehicle_Type"].dropna().unique())],
            value="all", clearable=False
        )
    ], style={"maxWidth":"520px","display":"grid","gap":"8px"}),
    html.Div(id="kpi-row", style={"display":"flex","gap":"24px","margin":"20px 0"}),
    dcc.Graph(id="sales-trend"),
    dcc.Graph(id="vehicle-chart"),
    dcc.Graph(id="economic-scatter"),
    html.Footer("Source: IBM Developer Skills Network historical_automobile_sales.csv. "
                "Values are synthetic and should not be interpreted as actual market statistics.")
], style={"fontFamily":"Arial","maxWidth":"1200px","margin":"auto","padding":"24px"})


@app.callback(
    Output("kpi-row","children"),
    Output("sales-trend","figure"),
    Output("vehicle-chart","figure"),
    Output("economic-scatter","figure"),
    Input("period-filter","value"),
    Input("vehicle-filter","value")
)
def update_dashboard(period, vehicle):
    view = df.copy()
    if period != "all":
        view = view[view["Recession"].astype(int) == int(period)]
    if vehicle != "all":
        view = view[view["Vehicle_Type"] == vehicle]
    total = view["Automobile_Sales"].sum()
    avg = view["Automobile_Sales"].mean()
    months = view["Date"].nunique()
    kpis = [
        html.Div([html.H3(f"{total:,.0f}"), html.P("Total sales (dataset units)")]),
        html.Div([html.H3(f"{avg:,.1f}"), html.P("Average monthly sales")]),
        html.Div([html.H3(f"{months:,}"), html.P("Months in selection")])
    ]
    annual = view.groupby("Year", as_index=False)["Automobile_Sales"].sum()
    trend = px.line(annual, x="Year", y="Automobile_Sales", markers=True,
                    title="Annual automobile sales")
    type_data = view.groupby("Vehicle_Type", as_index=False)["Automobile_Sales"].mean()
    by_type = px.bar(type_data, x="Vehicle_Type", y="Automobile_Sales",
                     title="Average sales by vehicle type")
    scatter = px.scatter(view, x="GDP", y="Automobile_Sales", color="Recession",
                         size="Advertising_Expenditure", hover_data=["Date","City"],
                         title="GDP and automobile sales")
    return kpis, trend, by_type, scatter


if __name__ == "__main__":
    app.run(debug=True)
