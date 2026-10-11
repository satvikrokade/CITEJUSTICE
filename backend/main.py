"""
CiteJustice - FastAPI Main Application Server
Exposes high-performance REST APIs for Legal Judgment Prediction,
Dynamic Precedent Evolution Graph (DPEG) inspection, Statutory Cross-Mapping,
and Judicial PDF/HTML Report Export.
"""

import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from backend.modules.statutory_mapper import statutory_mapper
from backend.modules.dpeg_engine import dpeg_engine
from backend.modules.hybrid_retriever import hybrid_retriever
from backend.modules.legal_reasoner import legal_reasoner
from backend.modules.pdf_exporter import judicial_report_builder
from backend.modules.phase1_parser import phase1_parser
from backend.modules.pipeline_manager import pipeline_manager


app = FastAPI(
    title="CiteJustice: Automated Legal Judgment Prediction API",
    description="Precedent-Aware Legal AI using Dynamic Precedent Evolution Graphs & Graph Transformers for Indian Courts",
    version="2.0.0"
)

# CORS middleware for development and web apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request & Response Models
class CasePredictionRequest(BaseModel):
    case_title: str = Field(..., example="Sanjay Kumar v. State of Maharashtra")
    case_facts: str = Field(..., example="Accused engaged in a sudden mutual dispute during village fair without weapon premeditated; inflicted single knife injury.")
    case_type: str = Field(default="Criminal Appeal", example="Criminal Appeal")
    user_notes: Optional[str] = Field(default="", example="Section 302 IPC / Section 103 BNS invoked by prosecution.")


class SectionLookupRequest(BaseModel):
    section: str = Field(..., example="IPC 302")


class Phase1TextRequest(BaseModel):
    raw_text: str = Field(..., example="Text of Indian Supreme Court or High Court judgment...")


# API Endpoints
@app.post("/api/phase1/parse-text")
async def parse_judgment_text(req: Phase1TextRequest):
    """Phase 1: Segment raw text, extract metadata, IPC <-> BNS mappings, and precedent treatments."""
    try:
        return phase1_parser.process_document(req.raw_text, is_pdf=False)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/phase1/parse-pdf")
async def parse_judgment_pdf(file: UploadFile = File(...)):
    """Phase 1: Parse uploaded judicial PDF, segment into Facts/Ratio, and extract citation graph signals."""
    try:
        content = await file.read()
        return phase1_parser.process_document(content, is_pdf=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "CiteJustice (LexGraphFormer Engine)",
        "version": "2.0.0",
        "dpeg_nodes_indexed": len(dpeg_engine.graph.nodes),
        "dpeg_edges_indexed": len(dpeg_engine.graph.edges),
        "corpus_judgments_indexed": len(hybrid_retriever.corpus_cases)
    }


@app.get("/api/statutes")
async def get_all_statutes():
    """Retrieve full catalog of IPC <-> BNS, CrPC <-> BNSS, IEA <-> BSA mappings."""
    return statutory_mapper.get_all_statutes()


@app.post("/api/statutes/lookup")
async def lookup_statute(req: SectionLookupRequest):
    details = statutory_mapper.get_details(req.section)
    if not details:
        raise HTTPException(status_code=404, detail=f"Statute '{req.section}' not found in registry.")
    return details


@app.get("/api/benchmarks")
async def get_benchmark_cases():
    """Returns curated legal scenarios showing the classic DPEG advantage over naive RAG."""
    return [
        {
            "id": "maharashtra-anand-chinchwade",
            "name": "State of Maharashtra v. Anand Chinchwade & Ors. (IPC 302/120B)",
            "case_title": "State of Maharashtra v. Anand Chinchwade & Ors.",
            "case_type": "Criminal Appeal",
            "case_facts": "The accused are charged under Sections 302, 120-B read with Section 34 of the Indian Penal Code (IPC). The informant states that on the night of 14th August, the victim was intercepted near National Highway 48 and assaulted with sharp weapons. Primary evidence includes eyewitness testimony of PW-1, medical certificates denoting cranial lacerations, and recovery of instruments of crime. Defence contends alibi and systemic delay in FIR dispatch.",
            "user_notes": "Prosecution charges under Section 302, 120-B IPC (BNS 103, 61). Defence contends systemic delay in FIR and lack of independent corroborate evidence.",
            "highlight": "Synthesizes Section 302 IPC proof standards with corroboration requirements under Indian Evidence Act."
        },
        {
            "id": "murder-sudden-fight",
            "name": "Sudden Quarrel & Single Fatal Blow (IPC 302 / BNS 103)",
            "case_title": "Rajendra Prasad v. State of U.P.",
            "case_type": "Criminal Appeal",
            "case_facts": "The appellant and the deceased were neighbors who entered into an impromptu altercation regarding water flow. In the heat of the moment, the appellant picked up a wooden sickle and struck a single blow causing death. No prior enmity or premeditation existed.",
            "user_notes": "Prosecution charged under Section 302 IPC (BNS 103). Appellant seeks conversion to Section 304 Part II (BNS 105) citing Exception 4 to Section 300.",
            "highlight": "Demonstrates DPEG penalizing overruled Digambar Shankar (1976) and adopting 5-judge Sunder Singh (2016) & Anbazhagan (2023)."
        },
        {
            "id": "bail-regular-439",
            "name": "Regular Bail in Economic Offense (CrPC 439 / BNSS 483)",
            "case_title": "Vikramaditya Singhania v. Enforcement Directorate",
            "case_type": "Bail Application",
            "case_facts": "Petitioner has been in judicial custody for 14 months under Section 420 IPC / Section 318 BNS. Investigation is complete, chargesheet filed, and 85 witnesses cited. Petitioner has deep local roots and surrendered passport.",
            "user_notes": "Section 439 CrPC / Section 483 BNSS invoked. Ground of parity and prolonged custody without trial.",
            "highlight": "Applies Satender Kumar Antil (2022) and Arnesh Kumar (2014) constitutional liberty doctrine."
        },
        {
            "id": "quash-commercial-dispute",
            "name": "Quashing of FIR in Contractual Dispute (CrPC 482 / BNSS 528)",
            "case_title": "Apex Commodities Ltd. v. State of Karnataka & Anr.",
            "case_type": "Criminal Petition",
            "case_facts": "Complainant filed FIR alleging cheating under Section 420 IPC and criminal breach of trust after goods delivered were rejected due to quality defect and payment withheld. Arbitration clause exists in contract.",
            "user_notes": "Petition under Section 482 CrPC / Section 528 BNSS to quash FIR as abuse of judicial process.",
            "highlight": "Applies Bhajan Lal (1992) Guidelines 1 & 7 while distinguishing Neeharika Infrastructure (2021)."
        }
    ]


@app.post("/api/predict")
async def predict_judgment(req: CasePredictionRequest):
    """Executes the complete LexGraphFormer judgment prediction & explainability pipeline."""
    result = legal_reasoner.predict_and_explain(
        case_title=req.case_title,
        case_facts=req.case_facts,
        case_type=req.case_type,
        user_notes=req.user_notes or ""
    )
    return result


@app.get("/api/subgraph")
async def get_citation_subgraph(cases: Optional[str] = None):
    """Returns interactive graph nodes and links for WebGL visualization."""
    if cases:
        case_list = [c.strip() for c in cases.split(",") if c.strip()]
    else:
        # Return entire benchmark graph
        case_list = list(dpeg_engine.graph.nodes.keys())[:15]
    
    return dpeg_engine.get_subgraph_for_cases(case_list, hops=1)


@app.post("/api/export_pdf")
async def export_pdf_report(req: CasePredictionRequest):
    """Generates official judicial PDF report."""
    result = legal_reasoner.predict_and_explain(
        case_title=req.case_title,
        case_facts=req.case_facts,
        case_type=req.case_type,
        user_notes=req.user_notes or ""
    )
    pdf_bytes = judicial_report_builder.generate_pdf_report(result)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=CiteJustice_Report_{req.case_title.replace(' ', '_')}.pdf"}
    )


@app.post("/api/export_html")
async def export_html_report(req: CasePredictionRequest):
    """Generates styled printable judicial HTML report."""
    result = legal_reasoner.predict_and_explain(
        case_title=req.case_title,
        case_facts=req.case_facts,
        case_type=req.case_type,
        user_notes=req.user_notes or ""
    )
    html_content = judicial_report_builder.generate_html_report(result)
    return HTMLResponse(content=html_content)


# --- Pipeline Manager & Phase-by-Phase API Endpoints ---
@app.get("/api/pipeline/runs")
async def list_pipeline_runs():
    """List all pipeline runs with their phase completion status."""
    return pipeline_manager.list_runs()


@app.post("/api/pipeline/create")
async def create_pipeline_run(name: Optional[str] = "New Judicial Analysis"):
    """Create a new pipeline tracking session."""
    return pipeline_manager.create_run(name=name or "New Judicial Analysis")


@app.get("/api/pipeline/{run_id}")
async def get_pipeline_run(run_id: str):
    """Retrieve full data, inputs, and stored outputs for all 4 phases."""
    run = pipeline_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found.")
    return run


@app.post("/api/pipeline/{run_id}/phase1-pdf")
async def run_phase1_pdf(run_id: str, file: UploadFile = File(...)):
    """Run Phase 1: Parse PDF, extract metadata, BNS statutes, and precedent signals."""
    try:
        content = await file.read()
        return pipeline_manager.execute_phase1(run_id, content, is_pdf=True, run_name=file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/pipeline/{run_id}/phase1-text")
async def run_phase1_text(run_id: str, req: Phase1TextRequest):
    """Run Phase 1: Parse raw judgment text."""
    try:
        return pipeline_manager.execute_phase1(run_id, req.raw_text, is_pdf=False)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/pipeline/{run_id}/phase2")
async def run_phase2(run_id: str):
    """Run Phase 2: DPEG Multigraph & Hybrid Retrieval Indexing."""
    try:
        return pipeline_manager.execute_phase2(run_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/pipeline/{run_id}/phase3")
async def run_phase3(run_id: str):
    """Run Phase 3: LexGraphFormer Graph Transformer Inference."""
    try:
        return pipeline_manager.execute_phase3(run_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/pipeline/{run_id}/phase4")
async def run_phase4(run_id: str):
    """Run Phase 4: IRAC Verdict & Appeal Risk Synthesis."""
    try:
        return pipeline_manager.execute_phase4(run_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/pipeline/run-all-text")
async def run_all_phases_text(req: Phase1TextRequest, name: Optional[str] = "End-to-End Analysis"):
    """Execute all 4 phases end-to-end sequentially from text."""
    try:
        return pipeline_manager.run_all(req.raw_text, is_pdf=False, run_name=name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/pipeline/run-all-pdf")
async def run_all_phases_pdf(file: UploadFile = File(...)):
    """Execute all 4 phases end-to-end sequentially from uploaded PDF."""
    try:
        content = await file.read()
        return pipeline_manager.run_all(content, is_pdf=True, run_name=file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Mount static frontend directory if it exists
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def serve_index():
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return {"message": "Frontend index.html not found"}

    @app.get("/pipeline")
    async def serve_pipeline_dashboard():
        pipeline_file = os.path.join(static_dir, "pipeline.html")
        if os.path.exists(pipeline_file):
            with open(pipeline_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>Pipeline Dashboard not found</h1>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
