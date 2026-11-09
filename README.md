# IBM Data Science Capstone — Historical Automobile Sales

An end-to-end educational project analyzing historical automobile sales patterns across recession and non-recession periods.

## Dataset

- File: `data/historical_automobile_sales.csv`
- 528 monthly observations, 1980–2023.
- Source: IBM Developer Skills Network course dataset, mirrored in a public repository.
- **Important:** the source describes this dataset as artificially created for the assignment. Findings are educational and must not be represented as real-world automotive market facts.
- The source field `City` contains four U.S. state names: California, Georgia, Illinois and New York.

## Project structure

```text
.
├── data/                  # Source CSV
├── notebooks/             # Guided Jupyter notebooks
├── src/analysis.py        # Reproducible end-to-end analysis pipeline
├── sql/analysis_queries.sql
├── dashboard/app.py       # Plotly Dash dashboard
├── presentation/          # PowerPoint builder and final deck
├── outputs/               # Generated results (created locally; gitignored)
└── requirements.txt
```

## Setup

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/analysis.py
```

The pipeline creates cleaned data, EDA charts and a Folium HTML map under `visualizations/`, plus SQLite query exports, model metrics and a JSON summary under `outputs/`.

## Run the dashboard

```bash
python dashboard/app.py
```

Open the local URL printed by Dash (usually http://127.0.0.1:8050).

## Build the presentation

After running the analysis pipeline:

```bash
python presentation/build_presentation.py
```

This creates `presentation/Capstone_Presentation.pptx`. Export it to PDF using PowerPoint or LibreOffice.

## Analysis workflow

1. Data collection and source documentation
2. Data cleaning and feature engineering
3. Exploratory visual analytics
4. SQL-based analysis with SQLite
5. Folium map of state-level aggregates
6. Recession classification using Logistic Regression and Random Forest
7. Interactive Plotly Dash dashboard
8. Presentation of results and limitations

## Modeling note

The target is `Recession`. Models use a stratified hold-out split and report accuracy, precision, recall, F1 and ROC-AUC. The exercise is classification on synthetic course data, not a forecast of future recessions. Do not interpret the metrics as production-grade economic predictions.

## Data provenance

IBM Developer Skills Network, *Historical Automobile Sales* course dataset. A public mirror and dataset description are available at:
https://github.com/TimonaL/Historical-Automobile-Sales-Analysis

Please retain the synthetic-data limitation when reusing this dataset.
