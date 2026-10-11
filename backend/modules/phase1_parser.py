"""
CiteJustice - Phase 1 Judicial Parser & Segmenter
Extracts structural components, citations, statutory cross-mappings,
and precedent treatments from raw judgment text or uploaded PDFs.
Ready for 200,000-case scaling into Phase 2 (Vector DB + DPEG Graph).
"""

import re
import io
from typing import Dict, Any, List, Optional
import pypdf
from backend.modules.statutory_mapper import statutory_mapper

class Phase1Parser:
    def __init__(self):
        # Common citation patterns in Indian judgments:
        # e.g., AIR 1973 SC 1461, (2014) 5 SCC 738, 2021 INSC 450, 1980 CriLJ 1234
        self.citation_regex = re.compile(
            r'(\b(?:AIR|SCC|SCR|CriLJ|INSC|SCC\s+Online)\s*(?:\[\d{4}\]|\(\d{4}\)|\d{4})?\s*[\w\s\(\)]*?\d+\b|\(\d{4}\)\s*\d+\s*SCC\s*\d+|AIR\s*\d{4}\s*SC\s*\d+)',
            re.IGNORECASE
        )
        
        # Treatment patterns: Overruled, Followed, Distinguished, Referred
        self.treatment_patterns = {
            "OVERRULED": [
                r'\boverruled\b', r'\bno longer good law\b', r'\bset aside\b',
                r'\bper incuriam\b', r'\bnot good law\b', r'\bstands overruled\b'
            ],
            "FOLLOWED": [
                r'\bfollowed\b', r'\brelied upon\b', r'\baffirmed\b',
                r'\bapproved\b', r'\bin line with\b', r'\bconsistent with\b'
            ],
            "DISTINGUISHED": [
                r'\bdistinguished\b', r'\binapplicable\b', r'\bnot applicable\b',
                r'\bfacts are distinct\b', r'\bdiffers materially\b'
            ],
            "REFERRED": [
                r'\breferred to\b', r'\bcited\b', r'\bnoticed\b', r'\bconsidered\b'
            ]
        }
        
        # Statutory regex
        self.statute_regex = re.compile(
            r'\b(?:Section|Sec\.?|s\.)\s*(\d+[A-Z]?)\s*(?:of\s+the\s+)?(IPC|Indian\s+Penal\s+Code|CrPC|Code\s+of\s+Criminal\s+Procedure|BNS|Bharatiya\s+Nyaya\s+Sanhita|BNSS|Evidence\s+Act|BSA)\b',
            re.IGNORECASE
        )

    def extract_text_from_pdf(self, pdf_file: bytes) -> str:
        """Extract plain text from uploaded PDF bytes."""
        reader = pypdf.PdfReader(io.BytesIO(pdf_file))
        text_chunks = []
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
        return "\n\n".join(text_chunks)

    def parse_metadata(self, text: str) -> Dict[str, Any]:
        """Extract Court, Title, Bench Strength, and Year."""
        court = "Supreme Court of India" if ("SUPREME COURT" in text.upper() or "INSC" in text) else "High Court"
        
        # Search for Petitioner v. Respondent
        title = "In re Legal Proceedings"
        vs_match = re.search(r'([A-Z][A-Za-z\s\.\,\(\)]+)\s+(?:VERSUS|VS\.?|V\.)\s+([A-Z][A-Za-z\s\.\,\(\)]+)', text[:1500], re.IGNORECASE)
        if vs_match:
            petitioner = vs_match.group(1).strip().replace('\n', ' ')
            respondent = vs_match.group(2).strip().replace('\n', ' ')
            title = f"{petitioner} v. {respondent}"
            if len(title) > 90:
                title = title[:87] + "..."

        # Bench strength estimation
        judges_match = re.findall(r'\b([A-Z\.\s]+),\s*(?:C\.?J\.?|J\.?|JJ\.?)\b', text[:2000])
        bench_count = max(len(judges_match), 2)
        if "CONSTITUTION BENCH" in text.upper():
            bench_count = max(bench_count, 5)

        # Year extraction
        year_match = re.search(r'\b(19\d{2}|20[0-2]\d)\b', text[:800])
        year = int(year_match.group(1)) if year_match else 2024

        return {
            "title": title,
            "court": court,
            "year": year,
            "bench_strength": bench_count,
            "judges": judges_match[:bench_count] if judges_match else ["Division Bench"]
        }

    def extract_statutes(self, text: str) -> List[Dict[str, Any]]:
        """Extract statutes and provide automatic IPC <-> BNS cross-mapping."""
        results = statutory_mapper.extract_sections(text)
        # Also check for explicit BNS/BNSS/BSA references
        for bns_key in ["BNS 103", "BNS 105", "BNS 106", "BNS 109", "BNSS 482", "BNSS 483"]:
            if bns_key.lower() in text.lower():
                detail = statutory_mapper.get_details(bns_key)
                if detail and detail not in results:
                    results.append(detail)
        return results

    def extract_citations_and_treatments(self, text: str) -> List[Dict[str, Any]]:
        """Identify cited precedents and their treatment status (Overruled, Followed, etc.)."""
        citations = set()
        for match in self.citation_regex.finditer(text):
            cit = match.group(0).strip()
            if len(cit) > 6 and not cit.isnumeric():
                citations.add(cit)

        # Contextual treatment detection
        precedents = []
        for cit in list(citations)[:12]:  # Top candidates
            # Find snippet around citation
            pos = text.find(cit)
            snippet = text[max(0, pos - 250):min(len(text), pos + len(cit) + 250)].lower()
            
            treatment = "REFERRED"
            authority_mod = +1
            status_desc = "Referred as supportive reference"

            for treat_type, patterns in self.treatment_patterns.items():
                if any(re.search(pat, snippet) for pat in patterns):
                    treatment = treat_type
                    break

            if treatment == "OVERRULED":
                authority_mod = -3
                status_desc = "FATAL: Overruled by larger bench / No longer valid precedent"
            elif treatment == "FOLLOWED":
                authority_mod = +2
                status_desc = "Binding: Followed with approval"
            elif treatment == "DISTINGUISHED":
                authority_mod = -1
                status_desc = "Distinguished: Factual elements differ"

            precedents.append({
                "citation": cit,
                "treatment": treatment,
                "authority_adjustment": authority_mod,
                "status_description": status_desc,
                "context_snippet": snippet[:180] + "..." if len(snippet) > 180 else snippet
            })

        return precedents

    def segment_judgment_structure(self, text: str) -> Dict[str, str]:
        """Segment raw judgment into Facts, Issues, Ratio Decidendi, and Final Verdict."""
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
        
        facts = []
        issues = []
        ratio = []
        order = []

        for p in paragraphs:
            p_lower = p.lower()
            if any(k in p_lower for k in ["factual matrix", "case of the prosecution", "the facts are", "brief facts", "the appellant"]):
                if len(facts) < 3:
                    facts.append(p)
            elif any(k in p_lower for k in ["question of law", "issue arises", "point for determination", "whether the court"]):
                if len(issues) < 2:
                    issues.append(p)
            elif any(k in p_lower for k in ["we are of the considered view", "the settled law is", "held that", "it is clear that", "ratio"]):
                if len(ratio) < 3:
                    ratio.append(p)
            elif any(k in p_lower for k in ["in the result", "appeal is allowed", "appeal is dismissed", "accordingly ordered", "conviction is set aside"]):
                if len(order) < 2:
                    order.append(p)

        # Fallbacks if section markers are implicit
        if not facts:
            facts = paragraphs[:2] if len(paragraphs) >= 2 else paragraphs
        if not issues:
            issues = ["Primary question regarding applicability of statutory charges and standard of proof beyond reasonable doubt."]
        if not ratio:
            mid = len(paragraphs) // 2
            ratio = paragraphs[mid:mid+2] if mid < len(paragraphs) else ["Judicial interpretation based on established statutory precedents."]
        if not order:
            order = paragraphs[-2:] if len(paragraphs) >= 2 else ["Final judicial decree as recorded by the bench."]

        return {
            "facts": " \n\n".join(facts[:3]),
            "issues": " \n\n".join(issues[:2]),
            "ratio_decidendi": " \n\n".join(ratio[:3]),
            "operative_order": " \n\n".join(order[:2])
        }

    def process_document(self, content: Any, is_pdf: bool = False) -> Dict[str, Any]:
        """Full Phase 1 pipeline execution."""
        if is_pdf:
            raw_text = self.extract_text_from_pdf(content)
        else:
            raw_text = str(content)

        if not raw_text or len(raw_text.strip()) < 50:
            raise ValueError("Judgment text is too short or empty to extract legal structure.")

        metadata = self.parse_metadata(raw_text)
        statutes = self.extract_statutes(raw_text)
        citations = self.extract_citations_and_treatments(raw_text)
        structure = self.segment_judgment_structure(raw_text)

        # Phase 2 export payload representation
        phase2_record = {
            "document_id": f"INSC_{metadata['year']}_{hash(metadata['title']) % 100000:05d}",
            "metadata": metadata,
            "statutes": statutes,
            "citations_and_treatments": citations,
            "segmented_structure": structure,
            "word_count": len(raw_text.split()),
            "character_count": len(raw_text),
            "status": "PHASE_1_COMPLETE_READY_FOR_PHASE_2_GRAPH"
        }

        return phase2_record

phase1_parser = Phase1Parser()
