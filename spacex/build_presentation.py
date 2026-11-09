"""Build the stakeholder-ready SpaceX Falcon 9 capstone PDF from analysis outputs."""
from pathlib import Path
import json
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
                                Table, TableStyle, KeepTogether)

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"outputs"
FIG=OUT/"visualizations"
PDF=ROOT/"Capstone_Presentation.pdf"

def main():
    if not (OUT/"summary.json").exists():
        import subprocess,sys
        subprocess.run([sys.executable,str(ROOT/"analysis.py")],check=True)
    s=json.loads((OUT/"summary.json").read_text())
    metrics=json.loads((OUT/"summary.json").read_text())["models"]
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Cover",parent=styles["Title"],fontSize=30,leading=36,
        textColor=colors.HexColor("#102A43"),alignment=TA_CENTER,spaceAfter=16))
    styles.add(ParagraphStyle(name="Sub",parent=styles["Normal"],fontSize=15,leading=21,
        textColor=colors.HexColor("#486581"),alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="H",parent=styles["Heading1"],fontSize=21,leading=25,
        textColor=colors.HexColor("#102A43"),spaceAfter=10))
    styles.add(ParagraphStyle(name="Body2",parent=styles["BodyText"],fontSize=10.5,leading=15,
        spaceAfter=7))
    styles.add(ParagraphStyle(name="Small",parent=styles["BodyText"],fontSize=8,leading=11,
        textColor=colors.HexColor("#52606D")))
    doc=SimpleDocTemplate(str(PDF),pagesize=landscape(A4),rightMargin=1.5*cm,leftMargin=1.5*cm,
                          topMargin=1.3*cm,bottomMargin=1.3*cm)
    story=[]
    def p(t,style="Body2"): story.append(Paragraph(t,styles[style]))
    def img(name,w=23*cm,h=12*cm):
        path=FIG/name
        if path.exists():
            im=Image(str(path)); scale=min(w/im.imageWidth,h/im.imageHeight)
            im.drawWidth=im.imageWidth*scale; im.drawHeight=im.imageHeight*scale
            story.append(im)
    def table(rows,widths=None):
        t=Table(rows,colWidths=widths,repeatRows=1)
        t.setStyle(TableStyle([
          ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#102A43")),
          ("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
          ("FONTSIZE",(0,0),(-1,-1),9),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#BCCCDC")),
          ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F0F4F8")]),
          ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),7),
          ("RIGHTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),6),
          ("BOTTOMPADDING",(0,0),(-1,-1),6)]))
        story.append(t)
    # Cover
    story += [Spacer(1,2.4*cm),Paragraph("WINNING THE SPACE RACE<br/>WITH DATA SCIENCE",styles["Cover"]),
              Paragraph("SpaceX Falcon 9 First-Stage Landing Analysis & Prediction",styles["Sub"]),
              Spacer(1,1.2*cm)]
    p("IBM Applied Data Science Capstone | End-to-end data collection, analysis, interactive analytics and classification", "Sub")
    story += [Spacer(1,1.5*cm)]
    table([["DATASET SNAPSHOT","LAUNCHES","SUCCESSFUL LANDINGS","OBSERVED SUCCESS RATE"],
           ["Historical Falcon 9 course subset",str(s["launches"]),str(s["successful_landings"]),f'{s["success_rate_pct"]:.1f}%']])
    story += [Spacer(1,1.1*cm)]
    p("Prepared as a reproducible educational analysis. Historical sample only; not a live launch forecast.","Small")
    story.append(PageBreak())

    p("1. Executive Summary","H")
    p(f"This project analyzes {s['launches']} historical Falcon 9 launches from {s['date_start']} to {s['date_end']}. "
      f"The first-stage landing success rate in this prepared sample is {s['success_rate_pct']:.1f}% "
      f"({s['successful_landings']} successful landings). The work combines launch-data preparation, exploratory "
      "visualization, SQL aggregation, geographic mapping, an interactive dashboard, and supervised classification.")
    p(f"The best-performing model on the held-out test split by F1 score was <b>{s['best_model']}</b> "
      f"(F1={s['best_model_f1']:.3f}). This is a small historical teaching dataset, so model performance is "
      "illustrative and should not be treated as a dependable operational prediction.")
    p("Decision-useful takeaway: launch site, mission profile, payload and booster reuse history provide useful "
      "context for comparing historical outcomes. The analysis supports structured comparison—not a causal claim "
      "that any one variable guarantees landing success.")
    story.append(PageBreak())

    p("2. Introduction & Business Question","H")
    p("SpaceX's Falcon 9 is designed for partial reusability. Recovering and reusing the first stage can reduce "
      "launch-system costs. A competing launch provider would therefore benefit from understanding historical "
      "landing outcomes when assessing the economics and operational profile of a mission.")
    p("<b>Primary question:</b> Can historical launch characteristics help classify whether the Falcon 9 first "
      "stage lands successfully?")
    p("<b>Supporting questions:</b> How do landing outcomes vary by launch site, payload mass, orbit, launch year "
      "and booster flight history? Which classification approach performs best on a held-out sample?")
    p("<b>Target:</b> Class = 1 indicates a successful first-stage landing; Class = 0 indicates an unsuccessful "
      "landing, following the prepared capstone dataset's definition.")
    story.append(PageBreak())

    p("3. Data Collection &amp; Wrangling","H")
    p("The analysis loads the IBM Skills Network Falcon 9 capstone dataset, with a public GitHub mirror as a "
      "fallback. The course dataset consolidates historical launch information derived from SpaceX launch records "
      "and course web-scraping work. The source URL used for this run is:")
    p(f'<font size="8">{s["source"]}</font>',"Small")
    p("<b>Preparation steps:</b> parse launch dates; coerce payload mass and target values to numeric types; remove "
      "rows missing the target, launch site or date; create calendar year and readable landing-outcome labels; "
      "retain numeric and categorical launch characteristics for analysis.")
    p("<b>Model features:</b> flight number, payload mass, flights, grid fins, reuse, legs, block, reuse count, "
      "orbit and launch site (when present). The target column is excluded from the input features. Numeric values "
      "are median-imputed and standardized; categorical values are mode-imputed and one-hot encoded inside a "
      "scikit-learn pipeline to avoid fitting preprocessing on the test data.")
    table([["FIELD","MEANING"],["FlightNumber / Date","Launch sequence and launch date"],
           ["PayloadMass / Orbit","Mission payload mass (kg) and target orbit"],
           ["LaunchSite","Launch complex identifier"],["Flights / ReusedCount","Booster flight and reuse history"],
           ["Class","Binary first-stage landing outcome"]])
    story.append(PageBreak())

    p("4. Exploratory Data Analysis — Launch Patterns","H")
    p("Annual launch counts show how Falcon 9 activity changed across the observed period. The small course subset "
      "ends in 2020; it should not be interpreted as a current launch inventory.")
    img("launches_by_year.png",22*cm,12*cm)
    story.append(PageBreak())

    p("5. Exploratory Data Analysis — Landing Outcomes","H")
    p("Comparing payload mass distributions by outcome helps identify overlap and variation across missions. "
      "Payload alone is not a sufficient rule for deciding landing success.")
    img("payload_outcomes.png",22*cm,12*cm)
    story.append(PageBreak())

    p("6. Launch Site &amp; SQL Insights","H")
    p("SQL analysis is executed with SQLite over the cleaned launch table. Queries calculate overall landing "
      "success, success rate by launch site and orbit, and average payload mass by outcome.")
    rows=[["LAUNCH SITE","LAUNCHES","SUCCESS RATE (%)"]]
    for r in s["sites"]:
        rows.append([str(r["LaunchSite"]),str(int(r["launches"])),f'{r["success_rate_pct"]:.1f}'])
    table(rows,[8*cm,4*cm,5*cm])
    story += [Spacer(1,.35*cm)]
    img("success_by_site.png",18*cm,8.5*cm)
    story.append(PageBreak())

    p("7. Interactive Geographic Analysis — Folium","H")
    p("The generated Folium map is saved as <b>outputs/spacex_launch_sites_map.html</b>. Each marker represents "
      "a launch-site coordinate and its popup reports the number of launches, successful landings and observed "
      "success rate. Marker size scales with the number of launches. Open the HTML file in a browser to pan, zoom "
      "and inspect each site.")
    p("The map connects the statistical analysis to geography: launch-site comparisons should be interpreted in "
      "the context of different mission mixes and the small number of observations at some sites.")
    table([["INTERACTIVE MAP FILE","WHAT IT SHOWS"],
           ["outputs/spacex_launch_sites_map.html","Launch-site locations, launch counts, successful landings and site-level success rates"]])
    story.append(PageBreak())

    p("8. Interactive Analytics — Plotly Dash","H")
    p("The Dash application is provided in <b>spacex/dashboard.py</b>. Run it after the analysis pipeline has "
      "created the cleaned CSV. Users can filter by launch site and payload range. The dashboard updates the "
      "landing-outcome split, payload-versus-outcome scatter plot and annual landing-success trend.")
    p("Run from the repository root: <b>python spacex/dashboard.py</b>, then open the local address printed by Dash "
      "(normally http://127.0.0.1:8050).")
    img("success_over_time.png",21*cm,10*cm)
    story.append(PageBreak())

    p("9. Predictive Analysis — Classification","H")
    p("Four classifiers are tuned with GridSearchCV using stratified five-fold cross-validation on the training "
      "portion: Logistic Regression, Support Vector Machine, Decision Tree and K-Nearest Neighbors. A stratified "
      "75/25 train-test split is used. Metrics below are calculated only on the held-out test subset.")
    rows=[["MODEL","ACCURACY","PRECISION","RECALL","F1"]]
    for r in metrics:
        rows.append([r["model"],f'{r["accuracy"]:.3f}',f'{r["precision"]:.3f}',f'{r["recall"]:.3f}',f'{r["f1"]:.3f}'])
    table(rows,[7.5*cm,3*cm,3*cm,3*cm,3*cm])
    story += [Spacer(1,.3*cm)]
    img("confusion_matrix.png",12*cm,9*cm)
    p("The winning model is selected by F1 score to balance precision and recall. Because the sample is small and "
      "historical, the results may vary with the split and should be validated on a larger, more recent dataset "
      "before any real-world use.")
    story.append(PageBreak())

    p("10. Conclusion, Limitations & Next Steps","H")
    p("This capstone demonstrates a complete applied data-science workflow: structured launch data, cleaning and "
      "feature preparation, EDA, SQL, interactive mapping, a Dash dashboard and classification model comparison.")
    p("Key limitations: (1) only a small historical course subset is used; (2) some features may reflect the "
      "historical operational context and may not be available with the same quality before a future launch; "
      "(3) a random holdout split does not fully simulate predicting later launches from earlier launches; "
      "(4) class balance and mission mix can affect evaluation metrics; and (5) the analysis does not establish "
      "causation or estimate actual launch costs.")
    p("<b>Recommended next steps:</b> expand and refresh the dataset from documented primary sources; evaluate "
      "a time-based holdout; calibrate probabilities; report confidence intervals and class-specific errors; "
      "and add cost assumptions only when supported by verified cost data.")
    p("<b>Reproducibility:</b> source code, SQL, dashboard, map and generated outputs are included in the GitHub "
      "repository. The GitHub Actions workflow regenerates the PDF and packages the deliverables.")
    p("Sources: IBM Skills Network SpaceX capstone dataset; public dataset mirror at "
      "https://github.com/Abhigyan-RA/SpaceX-capstone. All numerical findings in this deck are generated from "
      "the downloaded dataset at build time.","Small")

    def footer(canvas,doc):
        canvas.saveState()
        canvas.setFont("Helvetica",8); canvas.setFillColor(colors.HexColor("#627D98"))
        canvas.drawString(1.5*cm,.65*cm,"IBM Applied Data Science Capstone | SpaceX Falcon 9")
        canvas.drawRightString(landscape(A4)[0]-1.5*cm,.65*cm,f"Page {doc.page}")
        canvas.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(f"Created {PDF} ({PDF.stat().st_size} bytes)")

if __name__=="__main__": main()
