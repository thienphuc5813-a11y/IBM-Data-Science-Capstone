"""End-to-end analysis pipeline for IBM automobile sales capstone.

The course dataset is synthetic and intended for educational analysis.
Run from the repository root: python src/analysis.py
"""
from pathlib import Path
import json
import sqlite3
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import MarkerCluster
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, confusion_matrix,
                             classification_report)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "historical_automobile_sales.csv"
OUT = ROOT / "outputs"
FIG = ROOT / "visualizations"
OUT.mkdir(exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
sns.set_theme(style="whitegrid", context="notebook")


def load_and_prepare(path=DATA):
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Month_Num"] = df["Date"].dt.month
    df["Quarter"] = df["Date"].dt.quarter
    numeric = df.select_dtypes(include="number").columns
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.drop_duplicates().dropna(subset=["Date", "Automobile_Sales", "Recession"])
    df["Recession"] = df["Recession"].astype(int)
    df["Month_Sin"] = np.sin(2 * np.pi * df["Month_Num"] / 12)
    df["Month_Cos"] = np.cos(2 * np.pi * df["Month_Num"] / 12)
    return df.sort_values("Date").reset_index(drop=True)


def save_eda(df):
    annual = df.groupby("Year", as_index=False)["Automobile_Sales"].sum()
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(annual["Year"], annual["Automobile_Sales"], marker="o", linewidth=1.8)
    ax.set(title="Annual automobile sales", xlabel="Year", ylabel="Total sales")
    fig.tight_layout(); fig.savefig(FIG / "annual_sales.png", dpi=160); plt.close(fig)

    recession = df.groupby("Recession")["Automobile_Sales"].mean().rename(
        index={0: "Non-recession", 1: "Recession"})
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.barplot(x=recession.index, y=recession.values, ax=ax)
    ax.set(title="Average monthly sales by economic period",
           xlabel="Period", ylabel="Average automobile sales")
    fig.tight_layout(); fig.savefig(FIG / "sales_recession_comparison.png", dpi=160); plt.close(fig)

    by_type = df.groupby(["Vehicle_Type", "Recession"], as_index=False)["Automobile_Sales"].mean()
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=by_type, x="Vehicle_Type", y="Automobile_Sales",
                hue="Recession", ax=ax)
    ax.set(title="Average sales by vehicle type and recession status",
           xlabel="Vehicle type", ylabel="Average sales")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout(); fig.savefig(FIG / "vehicle_type_recession.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.scatterplot(data=df, x="Price", y="Automobile_Sales",
                    hue="Recession", size="Advertising_Expenditure",
                    sizes=(20, 150), alpha=.7, ax=ax)
    ax.set(title="Price, advertising and automobile sales")
    fig.tight_layout(); fig.savefig(FIG / "price_sales_scatter.png", dpi=160); plt.close(fig)

    seasonal = df.groupby("Month_Num", as_index=False)["Automobile_Sales"].mean()
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=seasonal, x="Month_Num", y="Automobile_Sales", ax=ax)
    ax.set(title="Seasonal pattern in average monthly sales",
           xlabel="Month", ylabel="Average sales")
    fig.tight_layout(); fig.savefig(FIG / "seasonality.png", dpi=160); plt.close(fig)
    annual.to_csv(OUT / "annual_sales.csv", index=False)


def run_sql(df):
    db_path = OUT / "automobile_sales.db"
    with sqlite3.connect(db_path) as conn:
        df.to_sql("automobile_sales", conn, if_exists="replace", index=False)
        queries = {
            "sales_by_year": """SELECT Year, ROUND(SUM(Automobile_Sales),2) AS total_sales
                FROM automobile_sales GROUP BY Year ORDER BY Year""",
            "recession_vs_normal": """SELECT Recession, COUNT(*) AS months,
                ROUND(AVG(Automobile_Sales),2) AS avg_sales,
                ROUND(AVG(Price),2) AS avg_price
                FROM automobile_sales GROUP BY Recession ORDER BY Recession""",
            "sales_by_vehicle_and_period": """SELECT Vehicle_Type, Recession,
                ROUND(AVG(Automobile_Sales),2) AS avg_sales
                FROM automobile_sales GROUP BY Vehicle_Type, Recession
                ORDER BY Vehicle_Type, Recession""",
            "top_state_sales": """SELECT City AS State, ROUND(SUM(Automobile_Sales),2) AS total_sales
                FROM automobile_sales GROUP BY City ORDER BY total_sales DESC""",
            "monthly_seasonality": """SELECT Month_Num, ROUND(AVG(Automobile_Sales),2) AS avg_sales
                FROM automobile_sales GROUP BY Month_Num ORDER BY Month_Num"""
        }
        for name, query in queries.items():
            pd.read_sql_query(query, conn).to_csv(OUT / f"sql_{name}.csv", index=False)
        (OUT / "sql_queries_used.sql").write_text(
            "\n\n".join(f"-- {name}\n{query};" for name, query in queries.items()),
            encoding="utf-8")


def build_folium_map(df):
    # Approximate state-capital coordinates; markers show aggregated state-level
    # values from the course dataset, not city-level observations.
    state_coords = {
        "California": (38.5767, -121.4944),
        "Georgia": (33.7490, -84.3880),
        "Illinois": (39.7983, -89.6544),
        "New York": (42.6526, -73.7562),
    }
    agg = df.groupby("City", as_index=False)["Automobile_Sales"].sum()
    center = (39.5, -98.35)
    m = folium.Map(location=center, zoom_start=4, tiles="CartoDB positron")
    cluster = MarkerCluster().add_to(m)
    for _, row in agg.iterrows():
        state = row["City"]
        lat, lon = state_coords[state]
        folium.CircleMarker(
            location=(lat, lon), radius=8 + 18 * row["Automobile_Sales"] / agg["Automobile_Sales"].max(),
            popup=f"{state}: {row['Automobile_Sales']:,.1f} total sales (dataset units)",
            tooltip=state, color="#2457A7", fill=True, fill_opacity=.65
        ).add_to(cluster)
    folium.LayerControl().add_to(m)
    m.save(str(FIG / "automobile_sales_by_state.html"))


def train_classifiers(df):
    target = "Recession"
    features = ["Consumer_Confidence", "Seasonality_Weight", "Price",
                "Advertising_Expenditure", "Competition", "GDP", "Growth_Rate",
                "unemployment_rate", "Month_Sin", "Month_Cos", "Vehicle_Type", "City"]
    model_df = df[features + [target]].dropna()
    X, y = model_df[features], model_df[target]
    categorical = ["Vehicle_Type", "City"]
    numeric = [c for c in features if c not in categorical]
    pre = ColumnTransformer([
        ("num", Pipeline([("imputer", SimpleImputer(strategy="median")),
                          ("scale", StandardScaler())]), numeric),
        ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                          ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical)
    ])
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=.25, random_state=42, stratify=y)
    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=2,
                                                  class_weight="balanced", random_state=42)
    }
    results = []
    best_name, best_pipe, best_f1 = None, None, -1
    for name, estimator in models.items():
        pipe = Pipeline([("preprocess", pre), ("model", estimator)])
        pipe.fit(X_train, y_train)
        pred = pipe.predict(X_test)
        prob = pipe.predict_proba(X_test)[:, 1]
        metrics = {
            "model": name,
            "accuracy": accuracy_score(y_test, pred),
            "precision": precision_score(y_test, pred, zero_division=0),
            "recall": recall_score(y_test, pred, zero_division=0),
            "f1": f1_score(y_test, pred, zero_division=0),
            "roc_auc": roc_auc_score(y_test, prob)
        }
        results.append(metrics)
        if metrics["f1"] > best_f1:
            best_name, best_pipe, best_f1 = name, pipe, metrics["f1"]
    result_df = pd.DataFrame(results).sort_values("f1", ascending=False)
    result_df.to_csv(OUT / "model_comparison.csv", index=False)
    best_pred = best_pipe.predict(X_test)
    cm = confusion_matrix(y_test, best_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                xticklabels=["Normal", "Recession"],
                yticklabels=["Normal", "Recession"])
    ax.set(title=f"Confusion matrix — {best_name}",
           xlabel="Predicted", ylabel="Actual")
    fig.tight_layout(); fig.savefig(FIG / "confusion_matrix.png", dpi=160); plt.close(fig)
    report = classification_report(y_test, best_pred, zero_division=0)
    (OUT / "classification_report.txt").write_text(
        f"Best model by F1: {best_name}\n\n{report}\n"
        "Interpretation: this is an educational classification exercise on a synthetic dataset. "
        "The random split is not a forecast of future recession events.", encoding="utf-8")
    return result_df


def main():
    df = load_and_prepare()
    df.to_csv(OUT / "cleaned_automobile_sales.csv", index=False)
    save_eda(df)
    run_sql(df)
    build_folium_map(df)
    metrics = train_classifiers(df)
    summary = {
        "rows": int(len(df)), "columns": int(df.shape[1]),
        "date_start": str(df["Date"].min().date()),
        "date_end": str(df["Date"].max().date()),
        "recession_months": int((df["Recession"] == 1).sum()),
        "non_recession_months": int((df["Recession"] == 0).sum()),
        "model_results": metrics.to_dict(orient="records")
    }
    (OUT / "project_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Outputs saved in: {OUT}")


if __name__ == "__main__":
    main()
