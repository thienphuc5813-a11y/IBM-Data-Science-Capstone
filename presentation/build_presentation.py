"""Build a PowerPoint summary after running src/analysis.py.
Run: python presentation/build_presentation.py
The deck uses metrics generated from the dataset, not hand-entered results.
"""
from pathlib import Path
import json
from pptx import Presentation
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "outputs" / "project_summary.json"
if not SUMMARY.exists():
    raise FileNotFoundError("Run 'python src/analysis.py' before building the presentation.")
summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

def add_slide(title, bullets):
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = title
    body = slide.placeholders[1].text_frame
    body.clear()
    for i, item in enumerate(bullets):
        p = body.paragraphs[0] if i == 0 else body.add_paragraph()
        p.text = item
        p.font.size = Pt(22)
        p.level = 0

add_slide("Historical Automobile Sales Analysis", [
    "IBM Data Science Capstone — end-to-end exploratory and predictive analysis",
    "Dataset: 528 monthly synthetic observations, 1980–2023",
    "Focus: recession periods, vehicle categories, economic indicators and sales patterns"
])
add_slide("Business Questions & Data", [
    "How do automobile sales change during recession periods?",
    "Do vehicle categories show different recession sensitivity?",
    "How are sales associated with price, GDP, unemployment and seasonality?",
    f"Coverage: {summary['date_start']} to {summary['date_end']} ({summary['rows']} rows)"
])
add_slide("Methodology", [
    "Data validation, date parsing, duplicate handling and feature engineering",
    "EDA with Matplotlib and Seaborn; SQL aggregation with SQLite",
    "Folium state-level map using the four state labels in the source dataset",
    "Logistic Regression and Random Forest classification of recession status"
])
add_slide("Descriptive Results", [
    f"Recession observations: {summary['recession_months']}",
    f"Non-recession observations: {summary['non_recession_months']}",
    "See outputs/figures and outputs/sql_*.csv for computed charts and query results",
    "All results describe the synthetic educational dataset, not real-world sales"
])
model_lines = []
for m in summary["model_results"]:
    model_lines.append(f"{m['model']}: accuracy={m['accuracy']:.3f}, F1={m['f1']:.3f}, ROC-AUC={m['roc_auc']:.3f}")
add_slide("Predictive Analysis", model_lines + [
    "Metrics are computed on a held-out stratified test set.",
    "This classification exercise is not a time-series forecast."
])
add_slide("Recommendations & Limitations", [
    "Use recession/non-recession comparisons as a structured learning exercise.",
    "Compare vehicle categories and seasonal patterns before forming inventory hypotheses.",
    "Do not generalize synthetic patterns to actual manufacturers or markets.",
    "Future work: validate against licensed real-world sales and macroeconomic data."
])
add_slide("Conclusion", [
    "The project demonstrates a reproducible workflow from raw data to dashboard and model evaluation.",
    "Interpretation should remain within the scope and limitations of the synthetic dataset."
])
out = ROOT / "presentation" / "Capstone_Presentation.pptx"
prs.save(out)
print(f"Saved: {out}")
