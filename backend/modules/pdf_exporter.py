"""
Judicial Report Export Module for CiteJustice
Generates formal, publication-ready Legal Analysis & Prediction Reports in both PDF (via ReportLab)
and styled HTML formats, compliant with Indian High Court and Supreme Court formatting conventions.
"""

import io
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


class JudicialReportBuilder:
    """Creates formal legal judgment analysis reports."""

    def generate_html_report(self, data: Dict[str, Any]) -> str:
        """Returns standalone, styled HTML report with dark/light print styling."""
        irac = data.get("irac", {})
        sections = data.get("extracted_sections", [])
        controlling = data.get("controlling_precedents", [])
        overruled = data.get("suppressed_overruled_precedents", [])

        sections_html = "".join([
            f"<div class='sec-chip'><strong>{s.get('historical_act')} {s.get('historical_section')}</strong> &rarr; "
            f"<span>{s.get('modern_act')} {s.get('modern_section')}</span> ({s.get('offense')})</div>"
            for s in sections
        ]) or "<em>No explicit sections flagged.</em>"

        controlling_html = "".join([
            f"<div class='precedent-card active'>"
            f"<h4>{p.get('title')}</h4>"
            f"<div class='prec-meta'>Citation: {p.get('citation')} | Year: {p.get('year')} | DPEG Authority: +{p.get('authority_score')}</div>"
            f"<p><strong>Ratio Decidendi:</strong> {p.get('summary')}</p>"
            f"</div>"
            for p in controlling
        ]) or "<em>No active precedents retrieved.</em>"

        overruled_html = "".join([
            f"<div class='precedent-card overruled'>"
            f"<h4>[OVERRULED / SUPPRESSED] {p.get('title')}</h4>"
            f"<div class='prec-meta'>Citation: {p.get('citation')} | DPEG Authority: {p.get('authority_score')} (Overruled: -3)</div>"
            f"<p><strong>Reason for Suppression:</strong> Precedent authority revoked by subsequent higher bench. CiteJustice automatically eliminated this zombie precedent.</p>"
            f"</div>"
            for p in overruled
        ]) if overruled else "<p class='text-muted'>None detected. All applied precedents have active legal authority.</p>"

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>CiteJustice Judicial Report - {data.get('case_title', 'Case Analysis')}</title>
<style>
  body {{ font-family: 'Georgia', serif; line-height: 1.6; color: #1e293b; background: #f8fafc; padding: 40px; margin: 0; }}
  .container {{ max-width: 900px; margin: 0 auto; background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 48px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
  .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 20px; margin-bottom: 30px; text-align: center; }}
  .header h1 {{ font-size: 24px; text-transform: uppercase; letter-spacing: 1px; color: #0f172a; margin: 0 0 8px 0; }}
  .header h2 {{ font-size: 16px; color: #64748b; font-weight: normal; margin: 0; }}
  .badge {{ display: inline-block; padding: 6px 14px; border-radius: 4px; font-weight: bold; font-size: 13px; text-transform: uppercase; margin-top: 10px; }}
  .badge-outcome {{ background: #0f172a; color: #f8fafc; }}
  .badge-conf {{ background: #e0e7ff; color: #3730a3; }}
  .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; background: #f1f5f9; padding: 16px; border-radius: 6px; margin: 20px 0; font-size: 14px; }}
  .irac-box {{ margin: 24px 0; }}
  .irac-box h3 {{ color: #0f172a; border-left: 4px solid #d4af37; padding-left: 10px; font-size: 17px; margin-bottom: 8px; }}
  .irac-box p {{ margin: 0 0 16px 0; font-size: 15px; text-align: justify; }}
  .sec-chip {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; font-size: 13.5px; }}
  .precedent-card {{ padding: 14px; border-radius: 6px; margin-bottom: 12px; font-size: 14px; }}
  .precedent-card.active {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #16a34a; }}
  .precedent-card.overruled {{ background: #fef2f2; border: 1px solid #fecaca; border-left: 4px solid #dc2626; }}
  .prec-meta {{ font-size: 12px; color: #64748b; margin-bottom: 6px; }}
  .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h2>CITEJUSTICE JUDICIAL REASONING ENGINE</h2>
    <h1>LEGAL JUDGMENT PREDICTION & EXPLAINABILITY REPORT</h1>
    <div>
      <span class="badge badge-outcome">{data.get('prediction', 'Prediction')}</span>
      <span class="badge badge-conf">Confidence: {data.get('confidence_score', 0)}%</span>
    </div>
  </div>

  <div class="meta-grid">
    <div><strong>Matter:</strong> {data.get('case_title', 'Untitled')}</div>
    <div><strong>Classification:</strong> {data.get('case_type', 'Criminal Appeal')}</div>
    <div><strong>Appeal Vulnerability:</strong> {data.get('appeal_vulnerability_risk', 'Low')}</div>
    <div><strong>DPEG Model:</strong> LexGraphFormer Precedent Evolution Engine</div>
  </div>

  <div class="irac-box">
    <h3>APPLICABLE STATUTORY CROSS-MAPPING (IPC 1860 &harr; BNS 2023)</h3>
    {sections_html}
  </div>

  <div class="irac-box">
    <h3>I. ISSUE (LEGAL QUESTIONS FRAMED)</h3>
    <p>{irac.get('issue', 'N/A')}</p>
  </div>

  <div class="irac-box">
    <h3>II. RULE (STATUTORY PROVISIONS & BINDING PRECEDENT TESTS)</h3>
    <p style="white-space: pre-line;">{irac.get('rule', 'N/A')}</p>
  </div>

  <div class="irac-box">
    <h3>III. APPLICATION (FACTUAL SYNTHESIS & DPEG PRECEDENT AUDIT)</h3>
    <p>{irac.get('application', 'N/A')}</p>
  </div>

  <div class="irac-box">
    <h3>IV. CONCLUSION (PREDICTED ADJUDICATION)</h3>
    <p><strong>{irac.get('conclusion', 'N/A')}</strong></p>
  </div>

  <div class="irac-box">
    <h3>CONTROLLING PRECEDENTS (VERIFIED ACTIVE LAW)</h3>
    {controlling_html}
  </div>

  <div class="irac-box">
    <h3>SUPPRESSED BAD LAW (OVERRULED PRECEDENTS PENALIZED VIA DPEG)</h3>
    {overruled_html}
  </div>

  <div class="footer">
    Generated automatically by CiteJustice (LexGraphFormer) &bull; Verified via Dynamic Precedent Evolution Graph &bull; Vidya Pratishthan's KBIET
  </div>
</div>
</body>
</html>"""

    def generate_pdf_report(self, data: Dict[str, Any]) -> bytes:
        """Returns binary PDF stream using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        normal_style = styles["Normal"]
        normal_style.fontSize = 10
        normal_style.leading = 14

        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            alignment=1,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6
        )

        sub_style = ParagraphStyle(
            "SubStyle",
            parent=styles["Heading3"],
            fontSize=10,
            leading=13,
            alignment=1,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=15
        )

        h2_style = ParagraphStyle(
            "H2Style",
            parent=styles["Heading2"],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=10,
            spaceAfter=4
        )

        elements = []

        elements.append(Paragraph("CITEJUSTICE: AUTOMATED LEGAL JUDGMENT PREDICTION", title_style))
        elements.append(Paragraph("EXPLAINABLE JUDICIAL REPORT (LEXGRAPHFORMER &bull; DPEG ENGINE)", sub_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceAfter=12))

        # Outcome block
        outcome_text = f"<b>PREDICTED OUTCOME:</b> {data.get('prediction', '')}<br/><b>CONFIDENCE:</b> {data.get('confidence_score', 0)}% | <b>APPEAL RISK:</b> {data.get('appeal_vulnerability_risk', '')}"
        elements.append(Paragraph(outcome_text, normal_style))
        elements.append(Spacer(1, 10))

        # Matter details table
        details_data = [
            ["Case Matter:", data.get("case_title", "")[:45]],
            ["Proceeding Type:", data.get("case_type", "Criminal Appeal")],
            ["Precedent Model:", "Dynamic Precedent Evolution Graph (Authority = 2F + R - D - 3O)"]
        ]
        t = Table(details_data, colWidths=[120, 380])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#1e293b")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

        # IRAC blocks
        irac = data.get("irac", {})
        elements.append(Paragraph("I. ISSUE", h2_style))
        elements.append(Paragraph(irac.get("issue", ""), normal_style))
        elements.append(Spacer(1, 8))

        elements.append(Paragraph("II. RULE", h2_style))
        elements.append(Paragraph(irac.get("rule", "").replace("\n", "<br/>"), normal_style))
        elements.append(Spacer(1, 8))

        elements.append(Paragraph("III. APPLICATION", h2_style))
        elements.append(Paragraph(irac.get("application", ""), normal_style))
        elements.append(Spacer(1, 8))

        elements.append(Paragraph("IV. CONCLUSION", h2_style))
        elements.append(Paragraph(f"<b>{irac.get('conclusion', '')}</b>", normal_style))
        elements.append(Spacer(1, 12))

        # Controlling Precedents
        elements.append(Paragraph("CONTROLLING PRECEDENTS (VERIFIED ACTIVE LAW)", h2_style))
        for p in data.get("controlling_precedents", [])[:2]:
            p_text = f"<b>{p.get('title')}</b> ({p.get('citation')}) &bull; DPEG Authority: +{p.get('authority_score')}<br/><i>Ratio:</i> {p.get('summary', '')}"
            elements.append(Paragraph(p_text, normal_style))
            elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 15))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
        elements.append(Paragraph("CiteJustice Research System &bull; Vidya Pratishthan's KBIET, Baramati &bull; DPEG Engine", sub_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


# Singleton instance
judicial_report_builder = JudicialReportBuilder()
