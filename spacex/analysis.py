"""Reproducible SpaceX Falcon 9 capstone analysis."""
from pathlib import Path
import json, sqlite3, warnings
import numpy as np
import pandas as pd
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import folium
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
FIG = OUT / "visualizations"
OUT.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
URLS = [
 "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DS0321EN-SkillsNetwork/datasets/dataset_part_2.csv",
 "https://raw.githubusercontent.com/Abhigyan-RA/SpaceX-capstone/main/dataset_part_2.csv",
]

def load_data():
    last = None
    for url in URLS:
        try:
            response = requests.get(url, timeout=30); response.raise_for_status()
            df = pd.read_csv(pd.io.common.BytesIO(response.content))
            if {"FlightNumber", "Class", "LaunchSite"}.issubset(df.columns) and len(df) > 30:
                df.to_csv(OUT / "dataset_part_2_source.csv", index=False)
                return df, url
        except Exception as exc:
            last = exc
    raise RuntimeError(f"Unable to download the SpaceX course dataset: {last}")

def main():
    warnings.filterwarnings("ignore")
    df, source = load_data()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["PayloadMass"] = pd.to_numeric(df["PayloadMass"], errors="coerce")
    df["Class"] = pd.to_numeric(df["Class"], errors="coerce")
    df = df.dropna(subset=["Class", "LaunchSite", "Date"]).copy()
    df["Class"] = df["Class"].astype(int)
    df["Year"] = df["Date"].dt.year
    df["Landing outcome"] = df["Class"].map({1:"Successful", 0:"Unsuccessful"})
    df.to_csv(OUT / "launches_clean.csv", index=False)

    n, successes = len(df), int(df["Class"].sum())
    success_rate = float(df["Class"].mean() * 100)
    site = df.groupby("LaunchSite").agg(launches=("Class","size"), success_rate=("Class","mean")).reset_index()
    site["success_rate_pct"] = site["success_rate"] * 100
    orbit = df.groupby("Orbit").agg(launches=("Class","size"), success_rate=("Class","mean")).reset_index()
    orbit["success_rate_pct"] = orbit["success_rate"] * 100
    yearly = df.groupby("Year").agg(launches=("Class","size"), success_rate=("Class","mean")).reset_index()
    yearly["success_rate_pct"] = yearly["success_rate"] * 100
    payload = df.groupby("Class")["PayloadMass"].agg(["count","mean","median"]).reset_index()
    site.to_csv(OUT/"sql_site_summary.csv", index=False)
    orbit.to_csv(OUT/"sql_orbit_summary.csv", index=False)
    yearly.to_csv(OUT/"yearly_summary.csv", index=False)
    payload.to_csv(OUT/"payload_by_outcome.csv", index=False)

    db = sqlite3.connect(OUT/"spacex_launches.sqlite")
    df.to_sql("launches", db, if_exists="replace", index=False)
    queries = {
      "overall": "SELECT COUNT(*) launches, SUM(Class) successes, ROUND(100.0*AVG(Class),1) success_pct FROM launches",
      "sites": "SELECT LaunchSite, COUNT(*) launches, ROUND(100.0*AVG(Class),1) success_pct FROM launches GROUP BY LaunchSite ORDER BY success_pct DESC",
      "orbits": "SELECT Orbit, COUNT(*) launches, ROUND(100.0*AVG(Class),1) success_pct FROM launches GROUP BY Orbit ORDER BY success_pct DESC",
      "payload": "SELECT Class, COUNT(*) launches, ROUND(AVG(PayloadMass),1) avg_payload_kg FROM launches GROUP BY Class"
    }
    sql_results={}
    for name, query in queries.items():
        sql_results[name]=pd.read_sql_query(query, db).replace({np.nan:None}).to_dict(orient="records")
    db.close()
    (OUT/"sql_results.json").write_text(json.dumps(sql_results, indent=2))

    # EDA figures
    fig, ax = plt.subplots(figsize=(8,4.5))
    yearly.plot(x="Year", y="launches", kind="bar", ax=ax, legend=False, color="#2878B5")
    ax.set_title("Falcon 9 launches by year"); ax.set_ylabel("Launch count"); ax.set_xlabel("")
    fig.tight_layout(); fig.savefig(FIG/"launches_by_year.png", dpi=170); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8,4.5))
    site.plot(x="LaunchSite", y="success_rate_pct", kind="bar", ax=ax, legend=False, color="#2A9D8F")
    ax.set_title("Landing success rate by launch site"); ax.set_ylabel("Success rate (%)"); ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=15); fig.tight_layout(); fig.savefig(FIG/"success_by_site.png", dpi=170); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8,4.5))
    for label, group in df.groupby("Class"):
        ax.hist(group["PayloadMass"].dropna(), bins=12, alpha=.55, label="Successful" if label else "Unsuccessful")
    ax.set_title("Payload mass distribution by landing outcome"); ax.set_xlabel("Payload mass (kg)")
    ax.set_ylabel("Launch count"); ax.legend(); fig.tight_layout()
    fig.savefig(FIG/"payload_outcomes.png", dpi=170); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8,4.5))
    yearly.plot(x="Year", y="success_rate_pct", ax=ax, marker="o", legend=False, color="#E76F51")
    ax.set_title("Landing success rate over time"); ax.set_ylabel("Success rate (%)"); ax.set_xlabel("Year")
    ax.set_ylim(0,105); fig.tight_layout(); fig.savefig(FIG/"success_over_time.png", dpi=170); plt.close(fig)

    # Folium launch-site map with outcome counts and marker size
    coords = df.groupby(["LaunchSite","Latitude","Longitude"], dropna=True).agg(
        launches=("Class","size"), successes=("Class","sum")).reset_index()
    m = folium.Map(location=[28.5,-90], zoom_start=3, tiles="CartoDB positron")
    for _, row in coords.iterrows():
        rate = row["successes"]/row["launches"]*100
        folium.CircleMarker(
            location=[row["Latitude"],row["Longitude"]],
            radius=8+row["launches"]**0.5,
            color="#168AAD", fill=True, fill_opacity=.75,
            popup=(f"<b>{row['LaunchSite']}</b><br>Launches: {row['launches']}"
                   f"<br>Successful landings: {int(row['successes'])}<br>Success rate: {rate:.1f}%")
        ).add_to(m)
    m.save(str(OUT/"spacex_launch_sites_map.html"))

    # Classification; keep the target out of the feature matrix
    feature_candidates=["FlightNumber","PayloadMass","Flights","GridFins","Reused","Legs",
                        "Block","ReusedCount","Orbit","LaunchSite"]
    features=[c for c in feature_candidates if c in df.columns]
    X=df[features].copy(); y=df["Class"].astype(int)
    numeric=[c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
    categorical=[c for c in X.columns if c not in numeric]
    pre=ColumnTransformer([
      ("num", Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler())]), numeric),
      ("cat", Pipeline([("impute",SimpleImputer(strategy="most_frequent")),("onehot",OneHotEncoder(handle_unknown="ignore"))]), categorical)
    ])
    X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
    models={
      "Logistic Regression": (LogisticRegression(max_iter=2000), {"model__C":[.1,1,10]}),
      "Support Vector Machine": (SVC(), {"model__C":[.1,1,10], "model__kernel":["linear","rbf"]}),
      "Decision Tree": (DecisionTreeClassifier(random_state=42), {"model__max_depth":[2,4,6,None], "model__min_samples_split":[2,4]}),
      "K-Nearest Neighbors": (KNeighborsClassifier(), {"model__n_neighbors":[3,5,7]})
    }
    results=[]; best_name=None; best_score=-1; best_model=None
    for name,(estimator,grid) in models.items():
        pipe=Pipeline([("prep",pre),("model",estimator)])
        search=GridSearchCV(pipe,grid,cv=5,scoring="f1",n_jobs=-1)
        search.fit(X_train,y_train)
        pred=search.best_estimator_.predict(X_test)
        row={"model":name,"accuracy":accuracy_score(y_test,pred),
             "precision":precision_score(y_test,pred,zero_division=0),
             "recall":recall_score(y_test,pred,zero_division=0),
             "f1":f1_score(y_test,pred,zero_division=0),
             "best_params":search.best_params_}
        results.append(row)
        if row["f1"]>best_score: best_score=row["f1"]; best_name=name; best_model=search.best_estimator_
    metrics=pd.DataFrame(results).sort_values(["f1","accuracy"],ascending=False)
    metrics.to_csv(OUT/"model_metrics.csv",index=False)
    pred=best_model.predict(X_test)
    cm=confusion_matrix(y_test,pred,labels=[0,1])
    fig,ax=plt.subplots(figsize=(5,4)); ax.imshow(cm,cmap="Blues")
    ax.set_title(f"Confusion matrix — {best_name}")
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_xticks([0,1],["Unsuccessful","Successful"]); ax.set_yticks([0,1],["Unsuccessful","Successful"])
    for (i,j),v in np.ndenumerate(cm): ax.text(j,i,str(v),ha="center",va="center",fontsize=13)
    fig.tight_layout(); fig.savefig(FIG/"confusion_matrix.png",dpi=170); plt.close(fig)

    summary={"source":source,"launches":n,"successful_landings":successes,
             "success_rate_pct":round(success_rate,1),"date_start":str(df["Date"].min().date()),
             "date_end":str(df["Date"].max().date()),"sites":site.to_dict(orient="records"),
             "orbits":orbit.to_dict(orient="records"),"yearly":yearly.to_dict(orient="records"),
             "best_model":best_name,"best_model_f1":round(float(best_score),3),
             "models":metrics.to_dict(orient="records"),"features":features,
             "note":"Small historical educational dataset; holdout metrics are sample-specific, not operational guarantees."}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps({k:summary[k] for k in ["launches","successful_landings","success_rate_pct","best_model","best_model_f1"]},indent=2))

if __name__=="__main__": main()
