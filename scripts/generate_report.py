"""
CiteJustice - Automated Judicial Report Generator
Generates publication-quality PDF and HTML legal judgment prediction & IRAC reasoning reports.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.modules.legal_reasoner import legal_reasoner
from backend.modules.pdf_exporter import judicial_report_builder

def generate_case_report(
    case_title: str = "Rajendra Prasad v. State of U.P.",
    case_facts: str = (
        "The appellant and the deceased were neighbors who entered into an impromptu altercation "
        "regarding water flow. In the heat of the moment, the appellant picked up a wooden sickle "
        "and struck a single blow causing death. No prior enmity or premeditation existed."
    ),
    case_type: str = "Criminal Appeal",
    user_notes: str = "Section 302 IPC / Section 103 BNS invoked. Exception 4 to Section 300.",
    output_dir: str = "reports"
):
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 70)
    print("        CITEJUSTICE - AUTOMATED JUDICIAL REPORT GENERATION")
    print("=" * 70)
    print(f"[*] Case Title   : {case_title}")
    print(f"[*] Proceeding   : {case_type}")
    print("[*] Running LexGraphFormer & Precedent Reasoner...")

    result = legal_reasoner.predict_and_explain(
        case_title=case_title,
        case_facts=case_facts,
        case_type=case_type,
        user_notes=user_notes
    )

    clean_name = "".join(c for c in case_title if c.isalnum() or c in (" ", "_")).rstrip().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Generate PDF Report
    pdf_filename = f"{clean_name}_Judicial_Report_{timestamp}.pdf"
    pdf_path = os.path.join(output_dir, pdf_filename)
    pdf_bytes = judicial_report_builder.generate_pdf_report(result)
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"[+] PDF Report generated : {pdf_path} ({len(pdf_bytes)} bytes)")

    # 2. Generate HTML Report
    html_filename = f"{clean_name}_Judicial_Report_{timestamp}.html"
    html_path = os.path.join(output_dir, html_filename)
    html_content = judicial_report_builder.generate_html_report(result)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[+] HTML Report generated: {html_path} ({len(html_content)} bytes)")

    print("-" * 70)
    print(f"VERDICT PREDICTED   : {result['prediction']}")
    print(f"CONFIDENCE SCORE    : {result['confidence_score']}%")
    print(f"CONTROLLING CASE(S) : {len(result['controlling_precedents'])} active binding precedents")
    print(f"OVERRULED SUPPRESSED: {len(result['suppressed_overruled_precedents'])} zombie precedent(s)")
    print("=" * 70)

    return {
        "pdf_path": os.path.abspath(pdf_path),
        "html_path": os.path.abspath(html_path),
        "result": result
    }

if __name__ == "__main__":
    generate_case_report()
