"""Build a PPTX and PDF report after running src/analysis.py.
Run: python presentation/build_presentation.py
"""
from pathlib import Path
import json
from pptx import Presentation
from pptx.util import Inches, Pt
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
SUMMARY = OUT / "project_summary.json"
if not SUMMARY.exists():
    raise FileNotFoundError("Run 'python src/analysis.py' before building the presentation.")
summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
models = summary["model_results"]

# PowerPoint
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
    return slide

add_slide("Historical Automobile Sales Analysis", [
    "IBM Data Science Capstone — end-to-end exploratory and predictive analysis",
    "528 monthly observations, 1980–2023",
    "Focus: recession periods, vehicle categories, economic indicators and sales patterns"
])
add_slide("Business Questions & Data", [
    "How do automobile sales change during recession periods?",
    "Do vehicle categories show different recession sensitivity?",
    "How are sales associated with price, GDP, unemployment and seasonality?",
    f"Coverage: {summary['date_start']} to {summary['date_end']} ({summary['rows']} rows)",
    "The source dataset is synthetic and intended for educational use."
])
add_slide("Methodology", [
    "Data validation, date parsing, duplicate handling and feature engineering",
    "EDA with Matplotlib and Seaborn; SQL aggregation with SQLite",
    "Folium state-level map using four state labels in the source dataset",
    "Logistic Regression and Random Forest classification of recession status"
])
add_slide("Descriptive Results", [
    f"Recession observations: {summary['recession_months']}",
    f"Non-recession observations: {summary['non_recession_months']}",
    "Charts and SQL outputs are generated in the outputs/ folder.",
    "Do not generalize synthetic patterns to actual automotive markets."
])
metric_bullets = [
    f"{m['model']}: accuracy {m['accuracy']:.3f}, precision {m['precision']:.3f}, "
    f"recall {m['recall']:.3f}, F1 {m['f1']:.3f}, ROC-AUC {m['roc_auc']:.3f}"
    for m in models
]
add_slide("Predictive Analysis", metric_bullets + [
    "Stratified hold-out evaluation; target is the Recession indicator.",
    "This is classification on synthetic educational data, not a time-series forecast."
])
add_slide("Recommendations & Limitations", [
    "Use recession/non-recession comparisons as a structured learning exercise.",
    "Compare vehicle categories and seasonal patterns before forming inventory hypotheses.",
    "The dataset is synthetic; real business decisions require validated market data.",
    "Future work: validate findings against licensed real-world data."
])
add_slide("Conclusion", [
    "The workflow connects data preparation, EDA, SQL, mapping, dashboarding and classification.",
    "All metrics are computed from the source dataset by the analysis pipeline."
])
for filename, title in [
    ("annual_sales.png","Annual sales trend"),
    ("sales_recession_comparison.png","Recession comparison"),
    ("vehicle_type_recession.png","Vehicle categories"),
    ("confusion_matrix.png","Classification confusion matrix")
]:
    image_path = OUT / "figures" / filename
    if image_path.exists():
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        slide.shapes.title.text = title
        slide.shapes.add_picture(str(image_path), Inches(1.1), Inches(1.3), width=Inches(10.8))
pptx_path = ROOT / "presentation" / "Capstone_Presentation.pptx"
prs.save(pptx_path)

# PDF report, using generated metrics and charts
styles = getSampleStyleSheet()
story = [
    Paragraph("Historical Automobile Sales Analysis", styles["Title"]),
    Paragraph("IBM Data Science Capstone — Executive Summary", styles["Heading2"]),
    Paragraph(
        f"This project analyzes {summary['rows']} monthly observations from "
        f"{summary['date_start']} to {summary['date_end']}. The dataset is synthetic "
        "and is used only for educational analysis.", styles["BodyText"]),
    Spacer(1, 12),
    Paragraph("Methodology", styles["Heading2"]),
    Paragraph("Data cleaning and feature engineering; visual EDA; SQLite queries; "
              "Folium state-level mapping; Plotly Dash dashboard; and classification "
              "with Logistic Regression and Random Forest.", styles["BodyText"]),
    Spacer(1, 12),
    Paragraph("Data coverage", styles["Heading2"]),
    Paragraph(f"Recession observations: {summary['recession_months']}<br/>"
              f"Non-recession observations: {summary['non_recession_months']}", styles["BodyText"]),
    Spacer(1, 12),
    Paragraph("Classification results", styles["Heading2"])
]
for m in models:
    story.append(Paragraph(
        f"{m['model']}: accuracy={m['accuracy']:.3f}; precision={m['precision']:.3f}; "
        f"recall={m['recall']:.3f}; F1={m['f1']:.3f}; ROC-AUC={m['roc_auc']:.3f}",
        styles["BodyText"]))
story += [Spacer(1, 12), Paragraph("Visual findings", styles["Heading2"])]
for filename, title in [
    ("annual_sales.png","Annual sales"),
    ("sales_recession_comparison.png","Sales by recession status"),
    ("vehicle_type_recession.png","Sales by vehicle type"),
    ("confusion_matrix.png","Confusion matrix")
]:
    image_path = OUT / "figures" / filename
    if image_path.exists():
        story.append(Paragraph(title, styles["Heading3"]))
        story.append(Image(str(image_path), width=430, height=220))
        story.append(Spacer(1, 8))
story += [
    Paragraph("Limitations and conclusion", styles["Heading2"]),
    Paragraph("The dataset is artificially generated for the course. Its patterns and model "
              "metrics should not be treated as real market evidence or a forecast. The project "
              "demonstrates a reproducible data science workflow and should be validated with "
              "reliable real-world data before any business use.", styles["BodyText"])
]
pdf_path = ROOT / "presentation" / "Capstone_Presentation.pdf"
SimpleDocTemplate(str(pdf_path), pagesize=landscape(A4)).build(story)
print(f"Saved: {pptx_path}")
print(f"Saved: {pdf_path}")
