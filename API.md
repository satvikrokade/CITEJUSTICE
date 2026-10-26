# CiteJustice REST API — Complete Frontend Integration Guide

> **Document Name:** `API` / `API.md`  
> **Version:** 2.0.0 (LexGraphFormer Engine)  
> **Backend Base URL (Local):** `http://127.0.0.1:8000` (or `http://localhost:8000`)  
> **API Root:** `http://127.0.0.1:8000/api`  
> **Interactive Swagger UI:** `http://127.0.0.1:8000/docs`  
> **ReDoc Alternative:** `http://127.0.0.1:8000/redoc`  
> **CORS Policy:** `*` (All origins, headers, and methods permitted)  
> **Status:** Production-Ready & Tested

---

## Table of Contents

1. [Architectural Overview & Global Conventions](#1-architectural-overview--global-conventions)
   - Base URLs & Environments
   - Content Types & Headers
   - HTTP Status Codes & Error Envelope
   - CORS & Development Server Setup
2. [Master API Directory & Matrix](#2-master-api-directory--matrix)
3. [Section A: System & Metadata Endpoints](#3-section-a-system--metadata-endpoints)
   - `GET /api/health`
   - `GET /api/benchmarks`
4. [Section B: Statutory Cross-Mapping (Colonial ↔ Modern)](#4-section-b-statutory-cross-mapping-colonial--modern)
   - `GET /api/statutes`
   - `POST /api/statutes/lookup`
5. [Section C: Standalone Phase 1 Document Parsing](#5-section-c-standalone-phase-1-document-parsing)
   - `POST /api/phase1/parse-text`
   - `POST /api/phase1/parse-pdf`
6. [Section D: Legal Adjudication & Explainability Cockpit](#6-section-d-legal-adjudication--explainability-cockpit)
   - `POST /api/predict`
   - `GET /api/subgraph`
   - `POST /api/export_pdf`
   - `POST /api/export_html`
7. [Section E: Multi-Phase Pipeline Command Center (`/pipeline`)](#7-section-e-multi-phase-pipeline-command-center-pipeline)
   - `GET /api/pipeline/runs`
   - `POST /api/pipeline/create`
   - `GET /api/pipeline/{run_id}`
   - `POST /api/pipeline/{run_id}/phase1-pdf`
   - `POST /api/pipeline/{run_id}/phase1-text`
   - `POST /api/pipeline/{run_id}/phase2`
   - `POST /api/pipeline/{run_id}/phase3`
   - `POST /api/pipeline/{run_id}/phase4`
   - `POST /api/pipeline/run-all-text`
   - `POST /api/pipeline/run-all-pdf`
8. [Section F: Static Web & Page Routes](#8-section-f-static-web--page-routes)
   - `GET /`
   - `GET /pipeline`
   - `GET /static/{path}`
9. [Complete TypeScript Type Definitions (`CiteJusticeTypes.ts`)](#9-complete-typescript-type-definitions-citejusticetypests)
10. [Frontend Ready-to-Use SDK (`frontend/apiClient.js`)](#10-frontend-ready-to-use-sdk-frontendapiclientjs)
11. [Frontend Recipes & Common Integrations](#11-frontend-recipes--common-integrations)
    - Handling File Uploads (`FormData`)
    - Downloading Official PDF Reports as Blobs
    - Visualizing the Precedent Subgraph (D3 / Cytoscape)
    - React Custom Hook (`useCiteJustice`)

---

## 1. Architectural Overview & Global Conventions

### 1.1 Base URLs & Ports
When running the FastAPI backend locally:
```
Local Server:      http://127.0.0.1:8000
API Endpoint Base: http://127.0.0.1:8000/api
Swagger Docs:      http://127.0.0.1:8000/docs
```
If your frontend runs on a separate port (e.g. Next.js on `3000`, Vite on `5173`), API calls should point to `http://127.0.0.1:8000/api/...` or use a Vite/Webpack proxy.

### 1.2 Headers & Content Types
* **Standard JSON Calls:**
  ```http
  Content-Type: application/json
  Accept: application/json
  ```
* **PDF Upload Calls:**
  ```http
  Content-Type: multipart/form-data
  ```
  *(Note: When using `fetch()` or `axios()`, do not manually set `Content-Type` for `FormData`—the browser will append the boundary automatically.)*
* **PDF Report Download Calls:**
  ```http
  Accept: application/pdf
  ```

### 1.3 HTTP Status Codes & Error Envelope
All error responses from FastAPI return standard status codes and a JSON envelope:
```json
{
  "detail": "Detailed descriptive explanation of why the request failed."
}
```

| HTTP Status | Meaning | Typical Trigger |
| :--- | :--- | :--- |
| **`200 OK`** | Success | Standard request succeeded; response payload in body. |
| **`400 Bad Request`** | Input / Parse Error | Missing required fields, corrupted PDF, unparsable text. |
| **`404 Not Found`** | Missing Entity | Section not in statute registry, or `run_id` not found in storage. |
| **`422 Unprocessable`**| Validation Error | Pydantic schema validation error (e.g., missing required body param). |
| **`500 Internal Error`**| Server Exception | Unhandled runtime failure in model or parsing engine. |

### 1.4 How to Start the Backend Locally
To test any endpoint directly from the frontend:
```powershell
# From project root
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 2. Master API Directory & Matrix

| # | HTTP Method | Endpoint Path | Content-Type | Frontend View / UI Component |
| :---: | :---: | :--- | :---: | :--- |
| **1** | `GET` | `/api/health` | `application/json` | Header Status Badge / System Diagnostics |
| **2** | `GET` | `/api/benchmarks` | `application/json` | Case Intake Quick-Load Preset Dropdown |
| **3** | `GET` | `/api/statutes` | `application/json` | Statutory Cross-Reference Catalog Tab |
| **4** | `POST` | `/api/statutes/lookup` | `application/json` | Statute Search Bar / Auto-suggest Modal |
| **5** | `POST` | `/api/phase1/parse-text` | `application/json` | "Auto-Extract from Text" Intake Button |
| **6** | `POST` | `/api/phase1/parse-pdf` | `multipart/form-data` | "Upload Judgment PDF" Drag & Drop Zone |
| **7** | `POST` | `/api/predict` | `application/json` | "Run Adjudication" Main Predict Button |
| **8** | `GET` | `/api/subgraph` | `application/json` | Interactive 2D/3D Citation Network Canvas |
| **9** | `POST` | `/api/export_pdf` | `application/json` | "Download Official PDF Report" Button |
| **10** | `POST` | `/api/export_html` | `application/json` | "Print / View HTML Verdict" Button |
| **11** | `GET` | `/api/pipeline/runs` | `application/json` | Pipeline Dashboard: Historical Runs List |
| **12** | `POST` | `/api/pipeline/create` | Query Param | Pipeline Dashboard: "New Pipeline Session" |
| **13** | `GET` | `/api/pipeline/{run_id}` | `application/json` | Pipeline Dashboard: Run Details & Phase Inspector |
| **14** | `POST` | `/api/pipeline/{run_id}/phase1-pdf` | `multipart/form-data` | Phase 1 Stepper: Upload PDF Card |
| **15** | `POST` | `/api/pipeline/{run_id}/phase1-text` | `application/json` | Phase 1 Stepper: Paste Judgment Card |
| **16** | `POST` | `/api/pipeline/{run_id}/phase2` | `application/json` | Phase 2 Stepper: "Index DPEG Multigraph" |
| **17** | `POST` | `/api/pipeline/{run_id}/phase3` | `application/json` | Phase 3 Stepper: "Run Graph Transformer" |
| **18** | `POST` | `/api/pipeline/{run_id}/phase4` | `application/json` | Phase 4 Stepper: "Synthesize IRAC Verdict" |
| **19** | `POST` | `/api/pipeline/run-all-text` | `application/json` | One-Click Full Analysis (Text input) |
| **20** | `POST` | `/api/pipeline/run-all-pdf` | `multipart/form-data` | One-Click Full Analysis (PDF file upload) |

---

## 3. Section A: System & Metadata Endpoints

### 3.1 Health & Engine Diagnostics

#### `GET /api/health`
* **Purpose:** Returns the operational status of the server, total indexed precedent nodes in the Dynamic Precedent Evolution Graph (DPEG), total graph edges, and corpus size.
* **Frontend Trigger:** App load, network status indicators, header status pills.
* **Headers:** `Accept: application/json`
* **Request Parameters:** None.

**Response `200 OK`:**
```json
{
  "status": "healthy",
  "service": "CiteJustice (LexGraphFormer Engine)",
  "version": "2.0.0",
  "dpeg_nodes_indexed": 907,
  "dpeg_edges_indexed": 3412,
  "corpus_judgments_indexed": 907
}
```

**Frontend JavaScript Snippet:**
```javascript
const res = await fetch('/api/health');
const data = await res.json();
console.log(`Backend online with ${data.dpeg_nodes_indexed} legal precedents.`);
```

---

### 3.2 Benchmark Scenarios Catalog

#### `GET /api/benchmarks`
* **Purpose:** Returns 4 curated landmark Indian legal scenarios (Murder sudden fight, regular bail, commercial dispute quashing, circumstantial murder) configured to demonstrate the DPEG's ability to discard overruled colonial precedents.
* **Frontend Trigger:** "Load Sample Scenario" dropdown or button group in the Intake Panel.
* **Headers:** `Accept: application/json`
* **Request Parameters:** None.

**Response `200 OK`:**
```json
[
  {
    "id": "maharashtra-anand-chinchwade",
    "name": "State of Maharashtra v. Anand Chinchwade & Ors. (IPC 302/120B)",
    "case_title": "State of Maharashtra v. Anand Chinchwade & Ors.",
    "case_type": "Criminal Appeal",
    "case_facts": "The accused are charged under Sections 302, 120-B read with Section 34 of the Indian Penal Code (IPC)... Primary evidence includes eyewitness testimony of PW-1...",
    "user_notes": "Prosecution charges under Section 302, 120-B IPC (BNS 103, 61). Defence contends systemic delay in FIR.",
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
```

**Frontend JavaScript Snippet:**
```javascript
async function populateBenchmarkDropdown() {
  const res = await fetch('/api/benchmarks');
  const benchmarks = await res.json();
  const select = document.getElementById('benchmark-select');
  benchmarks.forEach(bm => {
    const opt = document.createElement('option');
    opt.value = bm.id;
    opt.textContent = bm.name;
    opt.dataset.case = JSON.stringify(bm);
    select.appendChild(opt);
  });
}
```

---

## 4. Section B: Statutory Cross-Mapping (Colonial ↔ Modern)

### 4.1 Full Statutory Catalog

#### `GET /api/statutes`
* **Purpose:** Returns the complete dictionary of colonial laws (IPC 1860, CrPC 1973, Indian Evidence Act 1872) mapped to modern Indian statutes (Bharatiya Nyaya Sanhita 2023 [BNS], Bharatiya Nagarik Suraksha Sanhita 2023 [BNSS], Bharatiya Sakshya Adhiniyam 2023 [BSA]).
* **Frontend Trigger:** Statutory Reference Modal, legal glossary table, autocomplete registries.
* **Headers:** `Accept: application/json`

**Response `200 OK`:**
```json
[
  {
    "historical_act": "Indian Penal Code, 1860 (IPC)",
    "historical_section": "Section 302",
    "modern_act": "Bharatiya Nyaya Sanhita, 2023 (BNS)",
    "modern_section": "Section 103",
    "offense": "Punishment for Murder",
    "bailable": "Non-bailable",
    "cognizable": "Cognizable",
    "court": "Court of Session"
  },
  {
    "historical_act": "Indian Penal Code, 1860 (IPC)",
    "historical_section": "Section 304",
    "modern_act": "Bharatiya Nyaya Sanhita, 2023 (BNS)",
    "modern_section": "Section 105",
    "offense": "Punishment for Culpable Homicide not amounting to murder",
    "bailable": "Non-bailable",
    "cognizable": "Cognizable",
    "court": "Court of Session"
  },
  {
    "historical_act": "Code of Criminal Procedure, 1973 (CrPC)",
    "historical_section": "Section 439",
    "modern_act": "Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)",
    "modern_section": "Section 483",
    "offense": "Special powers of High Court or Court of Session regarding bail",
    "bailable": "N/A",
    "cognizable": "N/A",
    "court": "High Court or Court of Session"
  }
]
```

---

### 4.2 Specific Section Lookup

#### `POST /api/statutes/lookup`
* **Purpose:** Looks up a single section query (e.g. `"IPC 302"`, `"Section 420"`, `"CrPC 482"`, or `"BNS 103"`).
* **Frontend Trigger:** Search input or hovering over highlighted legal pill tags in judgment texts.
* **Headers:** `Content-Type: application/json`

**Request Body:**
```json
{
  "section": "IPC 302"
}
```

**Response `200 OK`:**
```json
{
  "historical_act": "Indian Penal Code, 1860 (IPC)",
  "historical_section": "Section 302",
  "modern_act": "Bharatiya Nyaya Sanhita, 2023 (BNS)",
  "modern_section": "Section 103",
  "offense": "Punishment for Murder",
  "bailable": "Non-bailable",
  "cognizable": "Cognizable",
  "court": "Court of Session"
}
```

**Response `404 Not Found`:**
```json
{
  "detail": "Statute 'IPC 999' not found in registry."
}
```

---

## 5. Section C: Standalone Phase 1 Document Parsing

Used by the frontend to allow advocates or judges to paste judgment text or drop judgment PDF files, auto-populating metadata, legal facts, ratio, statutes, and citations.

### 5.1 Parse Raw Judgment Text

#### `POST /api/phase1/parse-text`
* **Purpose:** Takes raw text of an Indian High Court or Supreme Court judgment, extracts structural sections (Facts, Issues, Ratio Decidendi, Final Order), legal metadata (bench strength, court, parties), statutes, and citation treatments.
* **Frontend Trigger:** "Parse Pasted Judgment" button in Case Intake Panel.
* **Headers:** `Content-Type: application/json`

**Request Body:**
```json
{
  "raw_text": "IN THE SUPREME COURT OF INDIA\nCRIMINAL APPELLATE JURISDICTION\nCRIMINAL APPEAL NO. 452 OF 2023\n\nRajendra Prasad ... Appellant\nVERSUS\nState of Uttar Pradesh ... Respondent\n\nJUDGMENT\nDr. D.Y. Chandrachud, C.J. & Sanjay Kishan Kaul, J.\n\n1. The present appeal arises out of the judgment passed by the High Court of Judicature at Allahabad affirming the conviction of the appellant under Section 302 of the Indian Penal Code (IPC)...\n2. The facts disclose that a sudden dispute arose over irrigation water... The appellant struck a single blow with a wooden stick without premeditation...\n3. In Sunder Singh v. State of Uttarakhand (2016), a 5-Judge Constitution Bench held that Exception 4 to Section 300 applies to spontaneous quarrels without premeditation. We expressly affirm that the older view in State of Maharashtra v. Digambar Shankar (1976) stands overruled...\n4. Consequently, the conviction is altered from Section 302 to Section 304 Part II IPC."
}
```

**Response `200 OK`:**
```json
{
  "metadata": {
    "title": "Rajendra Prasad v. State of Uttar Pradesh",
    "court": "Supreme Court of India",
    "year": 2023,
    "bench_strength": 2,
    "judges": ["Dr. D.Y. Chandrachud", "Sanjay Kishan Kaul"]
  },
  "word_count": 845,
  "segmented_structure": {
    "facts": "The present appeal arises out of the judgment passed by the High Court of Judicature at Allahabad affirming conviction... The facts disclose that a sudden dispute arose over irrigation water...",
    "issues": "Whether a single fatal blow during an unpremeditated sudden quarrel falls under Section 302 IPC or Exception 4 to Section 300 IPC.",
    "ratio_decidendi": "Exception 4 to Section 300 applies where bodily injury causing death is inflicted in heat of passion during sudden quarrel without premeditation.",
    "final_order": "Consequently, the conviction is altered from Section 302 to Section 304 Part II IPC."
  },
  "statutes": [
    {
      "historical_act": "Indian Penal Code, 1860 (IPC)",
      "historical_section": "Section 302",
      "modern_act": "Bharatiya Nyaya Sanhita, 2023 (BNS)",
      "modern_section": "Section 103",
      "offense": "Punishment for Murder",
      "bailable": "Non-bailable",
      "cognizable": "Cognizable",
      "court": "Court of Session"
    },
    {
      "historical_act": "Indian Penal Code, 1860 (IPC)",
      "historical_section": "Section 304",
      "modern_act": "Bharatiya Nyaya Sanhita, 2023 (BNS)",
      "modern_section": "Section 105",
      "offense": "Punishment for Culpable Homicide not amounting to murder",
      "bailable": "Non-bailable",
      "cognizable": "Cognizable",
      "court": "Court of Session"
    }
  ],
  "citations_and_treatments": [
    {
      "citation": "Sunder Singh v. State of Uttarakhand (2016)",
      "treatment": "FOLLOWED",
      "authority_mod": 2,
      "status_desc": "Followed or affirmed as binding authority"
    },
    {
      "citation": "State of Maharashtra v. Digambar Shankar (1976)",
      "treatment": "OVERRULED",
      "authority_mod": -3,
      "status_desc": "Overruled or declared bad law"
    }
  ]
}
```

---

### 5.2 Parse Uploaded Judgment PDF

#### `POST /api/phase1/parse-pdf`
* **Purpose:** Uploads a judicial PDF document, extracts plain text using PyPDF, and runs the Phase 1 structural segmenter.
* **Frontend Trigger:** Drag & drop dropzone or file input element.
* **Headers:** `Content-Type: multipart/form-data`
* **Form Field:** `file` (Binary PDF File)

**Frontend Vanilla JS Upload Example:**
```javascript
async function handlePdfUpload(fileObject) {
  const formData = new FormData();
  formData.append('file', fileObject);

  const response = await fetch('/api/phase1/parse-pdf', {
    method: 'POST',
    body: formData // Browser sets multipart boundary automatically
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'PDF parsing failed');
  }

  const parsedData = await response.json();
  
  // Auto-fill Case Intake form fields:
  document.getElementById('case_title').value = parsedData.metadata.title;
  document.getElementById('case_facts').value = parsedData.segmented_structure.facts;
  document.getElementById('case_type').value = parsedData.metadata.court.includes('Supreme') ? 'Criminal Appeal' : 'Writ Petition';
}
```

---

## 6. Section D: Legal Adjudication & Explainability Cockpit

This section powers the central adjudication cockpit (`index.html`), converting case facts into an explainable legal prediction, IRAC brief, overruled precedent warnings, and interactive citation graph.

### 6.1 Predict Case Adjudication (`POST /api/predict`)

* **Purpose:** Runs the entire 5-step LexGraphFormer pipeline:
  1. Statutory extraction (IPC ↔ BNS, CrPC ↔ BNSS, IEA ↔ BSA)
  2. DPEG authority-conditioned hybrid retrieval
  3. Precedent status validation (detects overruled bad law)
  4. Graph Attention Network reasoning over citation subgraph
  5. Calibrated IRAC synthesis and Appeal Vulnerability Risk calculation.
* **Frontend Trigger:** "Adjudicate Case" or "Run LexGraphFormer Engine" button.
* **Headers:** `Content-Type: application/json`

**Request Body Schema (`CasePredictionRequest`):**
| Field | Type | Required | Description | Example |
| :--- | :---: | :---: | :--- | :--- |
| `case_title` | `string` | **Yes** | Title or parties in the dispute | `"Rajendra Prasad v. State of U.P."` |
| `case_facts` | `string` | **Yes** | Narrative factual matrix of the case | `"Impromptu altercation regarding water flow; single blow struck..."` |
| `case_type` | `string` | No (Default: `"Criminal Appeal"`) | Type of legal proceeding | `"Criminal Appeal"`, `"Bail Application"`, `"Criminal Petition"` |
| `user_notes` | `string` | No | Additional statutory hints or advocate notes | `"Section 302 IPC / Section 103 BNS invoked by prosecution."` |

**Example Request:**
```json
{
  "case_title": "Rajendra Prasad v. State of U.P.",
  "case_facts": "The appellant and the deceased were neighbors who entered into an impromptu altercation regarding water flow. In the heat of the moment, the appellant picked up a wooden sickle and struck a single blow causing death. No prior enmity or premeditation existed.",
  "case_type": "Criminal Appeal",
  "user_notes": "Section 302 IPC / Section 103 BNS invoked by prosecution."
}
```

**Response `200 OK`:**
```json
{
  "case_title": "Rajendra Prasad v. State of U.P.",
  "case_type": "Criminal Appeal",
  "extracted_sections": [
    {
      "historical_act": "Indian Penal Code, 1860 (IPC)",
      "historical_section": "Section 302",
      "modern_act": "Bharatiya Nyaya Sanhita, 2023 (BNS)",
      "modern_section": "Section 103",
      "offense": "Punishment for Murder",
      "bailable": "Non-bailable",
      "cognizable": "Cognizable",
      "court": "Court of Session"
    }
  ],
  "prediction": "Appeal Allowed in Part: Conviction Modified to Culpable Homicide Not Amounting to Murder",
  "prediction_summary": "Conviction altered from Section 302 IPC (BNS 103) to Section 304 Part I/II IPC (BNS 105). Sentence reduced to period already undergone (or rigorous imprisonment of 7 years).",
  "confidence_score": 89.4,
  "appeal_vulnerability_risk": "Low (16.2%) - Fully anchored in 5-Judge Constitution Bench ratio",
  "irac": {
    "issue": "Whether the fatal injury inflicted during a sudden and spontaneous quarrel without premeditation constitutes Murder under Section 300/302 IPC (BNS 103) or qualifies for Exception 4 to Section 300, altering conviction to Section 304 Part II IPC (BNS 105).",
    "rule": "1. Exception 4 to Section 300 IPC (BNS 105): Culpable homicide is not murder if committed without premeditation in a sudden fight in heat of passion.\n2. Sunder Singh v. State of Uttarakhand (2016 5-Judge Bench): Explicitly overruled older rigid interpretation in State of Maharashtra v. Digambar Shankar (1976).\n3. Anbazhagan v. State (2023 INSC 644): Proportionality of single blow in spontaneous altercations.",
    "application": "The factual record proves the incident occurred spontaneously over a trivial dispute regarding irrigation flow, with no prior enmity. Under the older doctrine in Digambar Shankar (1976), this would have resulted in Section 302 murder conviction. However, CiteJustice's Dynamic Precedent Evolution Graph penalized Digambar Shankar (-3.0 authority score) as overruled and surfaced 5-Judge Bench authority in Sunder Singh.",
    "conclusion": "Conviction under Section 302 IPC is unsustainable and hereby altered to Section 304 Part II IPC (BNS 105). Sentence modified to rigorous imprisonment for 7 years."
  },
  "controlling_precedents": [
    {
      "case_id": "SC_2016_SUNDER",
      "title": "Sunder Singh v. State of Uttarakhand",
      "citation": "2016 5-Judge Bench",
      "bench_strength": 5,
      "authority_score": 7.5,
      "treatment": "FOLLOWED",
      "is_overruled": false,
      "cosine_similarity": 0.884,
      "dpeg_hybrid_rank": 1
    },
    {
      "case_id": "SC_2023_ANBAZHAGAN",
      "title": "Anbazhagan v. State Represented by Inspector of Police",
      "citation": "2023 INSC 644",
      "bench_strength": 2,
      "authority_score": 5.0,
      "treatment": "FOLLOWED",
      "is_overruled": false,
      "cosine_similarity": 0.852,
      "dpeg_hybrid_rank": 2
    }
  ],
  "suppressed_overruled_precedents": [
    {
      "case_id": "SC_1976_DIGAMBAR",
      "title": "State of Maharashtra v. Digambar Shankar",
      "citation": "AIR 1976 SC 123",
      "bench_strength": 2,
      "authority_score": -3.0,
      "treatment": "OVERRULED",
      "is_overruled": true,
      "overruled_by": "Sunder Singh v. State of Uttarakhand (2016)",
      "trap_warning": "Naive RAG systems rank this as top match due to high lexical similarity, which would result in wrongful murder conviction."
    }
  ],
  "dpeg_audit_trail": {
    "active_count": 5,
    "overruled_detected_count": 1,
    "naive_top_case": "State of Maharashtra v. Digambar Shankar (1976)",
    "naive_top_is_overruled": true,
    "dpeg_top_case": "Sunder Singh v. State of Uttarakhand (2016)"
  },
  "subgraph": {
    "nodes": [
      {
        "id": "CURRENT_QUERY",
        "label": "Rajendra Prasad (Current Case)",
        "type": "query",
        "authority": 0.0,
        "is_overruled": false
      },
      {
        "id": "SC_2016_SUNDER",
        "label": "Sunder Singh (2016)",
        "type": "precedent",
        "authority": 7.5,
        "is_overruled": false
      },
      {
        "id": "SC_1976_DIGAMBAR",
        "label": "Digambar Shankar (1976)",
        "type": "precedent",
        "authority": -3.0,
        "is_overruled": true
      }
    ],
    "links": [
      {
        "source": "CURRENT_QUERY",
        "target": "SC_2016_SUNDER",
        "relation": "FOLLOWED",
        "weight": 2.0
      },
      {
        "source": "SC_2016_SUNDER",
        "target": "SC_1976_DIGAMBAR",
        "relation": "OVERRULES",
        "weight": -3.0
      }
    ]
  },
  "graph_reasoning": {
    "layers_evaluated": 2,
    "attention_entropy": 0.34,
    "binding_precedent_ratio": 1.0,
    "status": "CONVERGED"
  }
}
```

---

### 6.2 Precedent Citation Subgraph

#### `GET /api/subgraph`
* **Purpose:** Returns nodes and links for rendering interactive force-directed graph diagrams (Cytoscape.js, D3.js, Force-Graph 3D). Overruled nodes are flagged with `is_overruled: true` so the frontend can color them crimson with warning pulses.
* **Frontend Trigger:** Precedent Network Explorer tab or expanding full-screen graph viewer.
* **Query Parameters:**
  | Parameter | Type | Required | Description |
  | :--- | :---: | :---: | :--- |
  | `cases` | `string` | No | Comma-separated list of case IDs (e.g. `SC_2016_SUNDER,SC_1976_DIGAMBAR`). If omitted, returns benchmark subgraph. |

**Request Example:**
```http
GET /api/subgraph?cases=SC_2016_SUNDER,SC_1976_DIGAMBAR
```

**Response `200 OK`:**
```json
{
  "nodes": [
    {
      "id": "SC_2016_SUNDER",
      "label": "Sunder Singh v. State of Uttarakhand",
      "year": 2016,
      "court": "Supreme Court of India",
      "bench_strength": 5,
      "authority_score": 7.5,
      "is_overruled": false,
      "category": "binding"
    },
    {
      "id": "SC_1976_DIGAMBAR",
      "label": "State of Maharashtra v. Digambar Shankar",
      "year": 1976,
      "court": "Supreme Court of India",
      "bench_strength": 2,
      "authority_score": -3.0,
      "is_overruled": true,
      "category": "overruled"
    }
  ],
  "links": [
    {
      "source": "SC_2016_SUNDER",
      "target": "SC_1976_DIGAMBAR",
      "relation": "OVERRULES",
      "weight": -3.0
    }
  ]
}
```

---

### 6.3 PDF Official Report Export

#### `POST /api/export_pdf`
* **Purpose:** Generates a downloadable, court-ready PDF judicial report complete with seal, IRAC legal breakdown, BNS statutory tables, and precedent authority audit trail.
* **Frontend Trigger:** "Export PDF Report" button.
* **Headers:** `Content-Type: application/json`, `Accept: application/pdf`
* **Request Body:** Same as `CasePredictionRequest`.
* **Response:** Binary Stream (`application/pdf`) with `Content-Disposition: attachment; filename="CiteJustice_Report_...pdf"`.

**Frontend Download Recipe:**
```javascript
async function downloadJudicialPdf(casePayload) {
  const response = await fetch('/api/export_pdf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(casePayload)
  });

  if (!response.ok) throw new Error('PDF generation failed');

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = `CiteJustice_Report_${casePayload.case_title.replace(/\s+/g, '_')}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}
```

---

### 6.4 Printable HTML Report Export

#### `POST /api/export_html`
* **Purpose:** Generates a clean, print-styled HTML report suitable for opening in a new browser tab or triggering `window.print()`.
* **Frontend Trigger:** "Print Preview" button.
* **Headers:** `Content-Type: application/json`
* **Request Body:** Same as `CasePredictionRequest`.
* **Response:** HTML Text (`text/html; charset=utf-8`).

**Frontend Snippet:**
```javascript
async function openPrintableHtmlReport(casePayload) {
  const response = await fetch('/api/export_html', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(casePayload)
  });
  const html = await response.text();
  const printWindow = window.open('', '_blank');
  printWindow.document.write(html);
  printWindow.document.close();
}
```

---

## 7. Section E: Multi-Phase Pipeline Command Center (`/pipeline`)

The Pipeline Command Center enables stepping through or inspecting the 4 individual phases of the LexGraphFormer system:
* **Phase 1:** Ingestion, structural parsing, and statutory mapping
* **Phase 2:** Multigraph building and authority score indexing ($2F + R - D - 3O$)
* **Phase 3:** LexGraphFormer Graph Transformer attention scoring
* **Phase 4:** Formal IRAC Adjudication & Appeal Vulnerability synthesis

Runs are persisted on disk in `backend/storage/pipeline_runs/{run_id}.json`.

---

### 7.1 List All Pipeline Runs

#### `GET /api/pipeline/runs`
* **Purpose:** Returns a list of all historical pipeline sessions with their current progress.
* **Frontend Trigger:** Run History Sidebar or Run Selector Dropdown.
* **Headers:** `Accept: application/json`

**Response `200 OK`:**
```json
[
  {
    "run_id": "run_1740000000_a1b2c3",
    "name": "State of Maharashtra v. Anand Chinchwade",
    "created_at": "2026-10-26 15:30:00",
    "current_phase": 4,
    "phase_statuses": {
      "phase1": "COMPLETED",
      "phase2": "COMPLETED",
      "phase3": "COMPLETED",
      "phase4": "COMPLETED"
    }
  },
  {
    "run_id": "run_1739999000_f4e5d6",
    "name": "Rajendra Prasad v. State of U.P.",
    "created_at": "2026-10-26 14:15:22",
    "current_phase": 2,
    "phase_statuses": {
      "phase1": "COMPLETED",
      "phase2": "COMPLETED",
      "phase3": "PENDING",
      "phase4": "PENDING"
    }
  }
]
```
`
---

### 7.2 Create New Pipeline Run

#### `POST /api/pipeline/create`
* **Purpose:** Initializes a new tracking container and returns an empty 4-phase session structure.
* **Frontend Trigger:** "New Case Analysis" button on `/pipeline`.
* **Query Parameters:**
  | Parameter | Type | Required | Default | Description |
  | :--- | :---: | :---: | :--- | :--- |
  | `name` | `string` | No | `"New Judicial Analysis"` | Display title of the pipeline run |

**Request Example:**
```http
POST /api/pipeline/create?name=Sanjay%20Kumar%20Appeal
```

**Response `200 OK`:**
```json
{
  "run_id": "run_1740001234_d9e8f7",
  "name": "Sanjay Kumar Appeal",
  "created_at": "2026-10-26 16:00:00",
  "current_phase": 0,
  "phases": {
    "phase1": {
      "title": "Phase 1: Ingestion & Structural Segmentation",
      "status": "PENDING",
      "summary": "Extracts Facts, Issues, Ratio Decidendi, Statutes, and Precedent Treatments.",
      "completed_at": null,
      "output": null
    },
    "phase2": {
      "title": "Phase 2: DPEG Multigraph & Retrieval Indexing",
      "status": "PENDING",
      "summary": "Builds citation multigraph with authority scores (2F + R - D - 3O) and hybrid retrieval.",
      "completed_at": null,
      "output": null
    },
    "phase3": {
      "title": "Phase 3: LexGraphFormer Graph Transformer",
      "status": "PENDING",
      "summary": "Runs edge-conditioned multi-head graph attention to penalize overruled law.",
      "completed_at": null,
      "output": null
    },
    "phase4": {
      "title": "Phase 4: IRAC Verdict & Appeal Risk Prediction",
      "status": "PENDING",
      "summary": "Generates formal judicial conclusion, conviction alterations, and appeal risk.",
      "completed_at": null,
      "output": null
    }
  }
}
```

---

### 7.3 Fetch Pipeline Run Details

#### `GET /api/pipeline/{run_id}`
* **Purpose:** Fetches the entire JSON state of a specific pipeline run, including all stored outputs and parameters of every completed phase.
* **Path Parameters:**
  | Parameter | Type | Description |
  | :--- | :---: | :--- |
  | `run_id` | `string` | Unique identifier (e.g. `run_1740001234_d9e8f7`) |

**Response `200 OK`:** Full JSON matching the structure in Section 7.2, with outputs populated for completed phases.

**Response `404 Not Found`:**
```json
{
  "detail": "Pipeline run 'invalid_id' not found."
}
```

---

### 7.4 Execute Phase 1 on Run (PDF or Text)

#### `POST /api/pipeline/{run_id}/phase1-pdf`
* **Purpose:** Ingests and parses a PDF document directly into an active run container.
* **Headers:** `Content-Type: multipart/form-data`
* **Form Field:** `file` (Binary PDF File)

#### `POST /api/pipeline/{run_id}/phase1-text`
* **Purpose:** Ingests raw text into an active run container.
* **Headers:** `Content-Type: application/json`
* **Request Body:**
  ```json
  {
    "raw_text": "Text of the judicial judgment..."
  }
  ```

**Phase 1 Output Payload in Run:**
```json
{
  "metadata": { "title": "...", "court": "...", "year": 2024, "bench_strength": 3 },
  "word_count": 1840,
  "segmented_structure": {
    "facts": "...",
    "issues": "...",
    "ratio_decidendi": "...",
    "final_order": "..."
  },
  "statutes": [ ... ],
  "citations_and_treatments": [ ... ]
}
```

---

### 7.5 Execute Phase 2: DPEG Multigraph & Retrieval Indexing

#### `POST /api/pipeline/{run_id}/phase2`
* **Purpose:** Executes candidate precedent retrieval using hybrid (BM25 + Dense) search on Phase 1 facts, extracts the citation multigraph, and calculates authority scores for all candidates using the formula:
  $$\text{Authority} = 2 \times \text{Followed} + 1 \times \text{Referred} - 1 \times \text{Distinguished} - 3 \times \text{Overruled}$$
* **Pre-requisite:** Phase 1 must be `COMPLETED`.
* **Headers:** `Content-Type: application/json`
* **Body:** Empty `{}`

**Phase 2 Output Structure:**
```json
{
  "retrieved_candidates": [
    {
      "case_id": "SC_2016_SUNDER",
      "title": "Sunder Singh v. State of Uttarakhand",
      "year": 2016,
      "bench_strength": 5,
      "authority_score": 7.5,
      "overruled": false,
      "cosine_similarity": 0.884,
      "hybrid_score": 0.912
    },
    {
      "case_id": "SC_1976_DIGAMBAR",
      "title": "State of Maharashtra v. Digambar Shankar",
      "year": 1976,
      "bench_strength": 2,
      "authority_score": -3.0,
      "overruled": true,
      "cosine_similarity": 0.891,
      "hybrid_score": 0.825
    }
  ],
  "subgraph_edges": [
    {
      "source": "SC_2016_SUNDER",
      "target": "SC_1976_DIGAMBAR",
      "relation": "OVERRULES",
      "weight": -3.0
    }
  ],
  "statutes_mapped": [ ... ],
  "total_nodes_in_dpeg": 907,
  "status": "PHASE_2_GRAPH_INDEXED"
}
```

---

### 7.6 Execute Phase 3: LexGraphFormer Graph Transformer Inference

#### `POST /api/pipeline/{run_id}/phase3`
* **Purpose:** Feeds the candidate citation multigraph into the Graph Attention layer. Attention weights towards overruled precedent traps are crushed to near-zero ($0.05$), while active Constitution Bench precedents are amplified.
* **Pre-requisite:** Phase 2 must be `COMPLETED`.
* **Headers:** `Content-Type: application/json`
* **Body:** Empty `{}`

**Phase 3 Output Structure:**
```json
{
  "graph_transformer_layer": "EdgeConditionedMultiHeadAttention(heads=4, d_model=256)",
  "precedents_evaluated": [
    {
      "case_id": "SC_2016_SUNDER",
      "title": "Sunder Singh v. State of Uttarakhand",
      "attention_weight": 0.925,
      "authority_score": 7.5,
      "is_binding": true,
      "is_overruled_trap": false,
      "gnn_adjusted_score": 1.259
    },
    {
      "case_id": "SC_1976_DIGAMBAR",
      "title": "State of Maharashtra v. Digambar Shankar",
      "attention_weight": 0.05,
      "authority_score": -3.0,
      "is_binding": false,
      "is_overruled_trap": true,
      "gnn_adjusted_score": -0.061
    }
  ],
  "binding_precedent": {
    "case_id": "SC_2016_SUNDER",
    "title": "Sunder Singh v. State of Uttarakhand",
    "attention_weight": 0.925,
    "authority_score": 7.5,
    "is_binding": true,
    "is_overruled_trap": false,
    "gnn_adjusted_score": 1.259
  },
  "status": "PHASE_3_GNN_SCORING_COMPLETE"
}
```

---

### 7.7 Execute Phase 4: IRAC Verdict & Appeal Risk Synthesis

#### `POST /api/pipeline/{run_id}/phase4`
* **Purpose:** Synthesizes the conclusive judicial verdict, generates the structured IRAC reasoning text, and evaluates the appeal vulnerability risk percentage.
* **Pre-requisite:** Phase 3 must be `COMPLETED`.
* **Headers:** `Content-Type: application/json`
* **Body:** Empty `{}`

**Phase 4 Output Structure:**
```json
{
  "case_title": "Rajendra Prasad v. State of U.P.",
  "predicted_outcome": "Appeal Allowed in Part: Conviction Modified to Culpable Homicide Not Amounting to Murder",
  "prediction_summary": "Conviction altered from Section 302 IPC (BNS 103) to Section 304 Part I/II IPC (BNS 105). Sentence reduced to period already undergone.",
  "confidence_score": 89.4,
  "appeal_vulnerability": "Low (16.2%) - Fully anchored in 5-Judge Constitution Bench ratio",
  "irac_report": {
    "issue": "Whether the fatal injury inflicted during a sudden quarrel without premeditation...",
    "rule": "1. Exception 4 to Section 300 IPC...",
    "application": "Incident occurred spontaneously without prior enmity...",
    "conclusion": "Conviction under Section 302 IPC set aside; altered to Section 304 Part II IPC."
  },
  "controlling_precedents": [ ... ],
  "suppressed_overruled_precedents": [ ... ],
  "status": "PHASE_4_VERDICT_DELIVERED"
}
```

---

### 7.8 Run All 4 Phases End-to-End

#### `POST /api/pipeline/run-all-text`
* **Purpose:** Creates a new run and executes Phase 1 $\to$ Phase 2 $\to$ Phase 3 $\to$ Phase 4 sequentially from raw text in a single API call.
* **Query Parameters:** `name` (optional run title)
* **Body:** `{"raw_text": "..."}`
* **Response:** Complete `run` JSON object with all 4 phases marked `COMPLETED`.

#### `POST /api/pipeline/run-all-pdf`
* **Purpose:** Creates a new run and executes all 4 phases sequentially from an uploaded PDF file.
* **Headers:** `Content-Type: multipart/form-data`
* **Form Field:** `file` (Binary PDF File)
* **Response:** Complete `run` JSON object with all 4 phases marked `COMPLETED`.

---

## 8. Section F: Static Web & Page Routes

The backend includes a pre-configured static file server that serves the frontend directly:

| Method | Path | Target File | Purpose |
| :---: | :--- | :--- | :--- |
| `GET` | `/` | `frontend/index.html` | Serves the main Adjudication Cockpit |
| `GET` | `/pipeline` | `frontend/pipeline.html`| Serves the 4-Phase Step-by-Step Command Center |
| `GET` | `/static/{path}` | `frontend/{path}` | Serves static assets (`app.js`, `apiClient.js`, `index.css`, etc.) |

---

## 9. Complete TypeScript Type Definitions (`CiteJusticeTypes.ts`)

Frontend developers using TypeScript, Next.js, or React can copy and paste the following definitions:

```typescript
// ==========================================
// CITEJUSTICE TYPESCRIPT INTERFACES
// ==========================================

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  dpeg_nodes_indexed: number;
  dpeg_edges_indexed: number;
  corpus_judgments_indexed: number;
}

export interface BenchmarkCase {
  id: string;
  name: string;
  case_title: string;
  case_type: string;
  case_facts: string;
  user_notes: string;
  highlight: string;
}

export interface StatuteMapping {
  historical_act: string;
  historical_section: string;
  modern_act: string;
  modern_section: string;
  offense: string;
  bailable: string;
  cognizable: string;
  court: string;
}

export interface CasePredictionRequest {
  case_title: string;
  case_facts: string;
  case_type?: string;
  user_notes?: string;
}

export interface IRACReport {
  issue: string;
  rule: string;
  application: string;
  conclusion: string;
}

export interface PrecedentItem {
  case_id: string;
  title: string;
  citation: string;
  bench_strength?: number;
  authority_score: number;
  treatment: string;
  is_overruled: boolean;
  overruled_by?: string;
  trap_warning?: string;
  cosine_similarity?: number;
  dpeg_hybrid_rank?: number;
}

export interface SubgraphNode {
  id: string;
  label: string;
  type?: string;
  year?: number;
  court?: string;
  bench_strength?: number;
  authority_score?: number;
  is_overruled: boolean;
  category?: 'binding' | 'overruled' | 'persuasive';
}

export interface SubgraphLink {
  source: string;
  target: string;
  relation: string;
  weight: number;
}

export interface SubgraphData {
  nodes: SubgraphNode[];
  links: SubgraphLink[];
}

export interface PredictionResponse {
  case_title: string;
  case_type: string;
  extracted_sections: StatuteMapping[];
  prediction: string;
  prediction_summary: string;
  confidence_score: number;
  appeal_vulnerability_risk: string;
  irac: IRACReport;
  controlling_precedents: PrecedentItem[];
  suppressed_overruled_precedents: PrecedentItem[];
  dpeg_audit_trail: {
    active_count: number;
    overruled_detected_count: number;
    naive_top_case: string;
    naive_top_is_overruled: boolean;
    dpeg_top_case: string;
  };
  subgraph: SubgraphData;
  graph_reasoning: {
    layers_evaluated: number;
    attention_entropy: number;
    binding_precedent_ratio: number;
    status: string;
  };
}

export interface Phase1Output {
  metadata: {
    title: string;
    court: string;
    year: number;
    bench_strength: number;
    judges: string[];
  };
  word_count: number;
  segmented_structure: {
    facts: string;
    issues: string;
    ratio_decidendi: string;
    final_order: string;
  };
  statutes: StatuteMapping[];
  citations_and_treatments: Array<{
    citation: string;
    treatment: 'OVERRULED' | 'FOLLOWED' | 'DISTINGUISHED' | 'REFERRED';
    authority_mod: number;
    status_desc: string;
  }>;
}

export interface PipelinePhaseState<T = any> {
  title: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  summary: string;
  completed_at: string | null;
  output: T | null;
}

export interface PipelineRun {
  run_id: string;
  name: string;
  created_at: string;
  current_phase: number;
  phases: {
    phase1: PipelinePhaseState<Phase1Output>;
    phase2: PipelinePhaseState<any>;
    phase3: PipelinePhaseState<any>;
    phase4: PipelinePhaseState<any>;
  };
}
```

---

## 10. Frontend Ready-to-Use SDK (`frontend/apiClient.js`)

A complete client library is already included in [`frontend/apiClient.js`](file:///d:/DATASET%20COURT%20VERDICTS/frontend/apiClient.js). You can import it into any modern frontend:

```javascript
// Import for ES6 / Vite / Webpack / Next.js
import { CiteJusticeAPI } from './apiClient.js';

// Or in vanilla HTML:
// <script src="/static/apiClient.js"></script>
```

### Complete Method Directory in `CiteJusticeAPI`
* `CiteJusticeAPI.getHealth()` $\to$ System diagnostics
* `CiteJusticeAPI.getBenchmarks()` $\to$ Array of 4 landmark cases
* `CiteJusticeAPI.getAllStatutes()` $\to$ All IPC/CrPC/IEA $\leftrightarrow$ BNS/BNSS/BSA mappings
* `CiteJusticeAPI.lookupStatute(section)` $\to$ Single section details
* `CiteJusticeAPI.parsePdf(file)` $\to$ Phase 1 extraction from PDF
* `CiteJusticeAPI.parseText(rawText)` $\to$ Phase 1 extraction from text
* `CiteJusticeAPI.predictCase(caseData)` $\to$ Adjudication, IRAC & graph
* `CiteJusticeAPI.getSubgraph(caseIds)` $\to$ Force-directed graph data
* `CiteJusticeAPI.downloadPdfReport(caseData, filename)` $\to$ Auto-triggers PDF download
* `CiteJusticeAPI.getHtmlReport(caseData)` $\to$ Returns raw printable HTML
* `CiteJusticeAPI.listPipelineRuns()` $\to$ All pipeline tracking sessions
* `CiteJusticeAPI.createPipelineRun(name)` $\to$ Create new session
* `CiteJusticeAPI.getPipelineRun(runId)` $\to$ Fetch multi-phase run state
* `CiteJusticeAPI.executePhase1Pdf(runId, file)` $\to$ Run Phase 1 via PDF
* `CiteJusticeAPI.executePhase1Text(runId, rawText)` $\to$ Run Phase 1 via Text
* `CiteJusticeAPI.executePhase2(runId)` $\to$ Run Phase 2 DPEG Indexing
* `CiteJusticeAPI.executePhase3(runId)` $\to$ Run Phase 3 Graph Transformer
* `CiteJusticeAPI.executePhase4(runId)` $\to$ Run Phase 4 IRAC Adjudication
* `CiteJusticeAPI.runPipelineAllText(rawText, name)` $\to$ Run all 4 phases end-to-end
* `CiteJusticeAPI.runPipelineAllPdf(file)` $\to$ Run all 4 phases from PDF

---

## 11. Frontend Recipes & Common Integrations

### 11.1 Drag-and-Drop PDF Upload Handler
```javascript
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('border-primary');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('border-primary');
});

dropZone.addEventListener('drop', async (e) => {
  e.preventDefault();
  dropZone.classList.remove('border-primary');
  const file = e.dataTransfer.files[0];
  if (file && file.type === 'application/pdf') {
    await processPdf(file);
  } else {
    alert('Please upload a valid PDF document.');
  }
});

async function processPdf(file) {
  try {
    dropZone.innerText = 'Extracting judgment structure...';
    const parsed = await CiteJusticeAPI.parsePdf(file);
    
    // Auto-populate case inputs
    document.getElementById('case_title').value = parsed.metadata.title;
    document.getElementById('case_facts').value = parsed.segmented_structure.facts;
  } catch (err) {
    alert(`Upload failed: ${err.message}`);
  }
}
```

### 11.2 Rendering Subgraph with D3.js or Force-Graph
```javascript
async function loadAndRenderGraph(caseIds) {
  const graphData = await CiteJusticeAPI.getSubgraph(caseIds);
  
  // Example node color rule:
  function getNodeColor(node) {
    if (node.is_overruled) return '#ef4444'; // Red for overruled bad law
    if (node.type === 'query') return '#3b82f6'; // Blue for current case
    return '#10b981'; // Green for binding precedent
  }

  // Pass graphData.nodes and graphData.links to your D3 simulation or Cytoscape
  console.log('Rendering nodes:', graphData.nodes);
}
```

### 11.3 React Custom Hook (`useCiteJustice`)
```typescript
import { useState } from 'react';
import { CiteJusticeAPI } from './apiClient';
import type { PredictionResponse, CasePredictionRequest } from './CiteJusticeTypes';

export function useCiteJustice() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);

  const predict = async (payload: CasePredictionRequest) => {
    setLoading(true);
    setError(null);
    try {
      const data = await CiteJusticeAPI.predictCase(payload);
      setResult(data);
      return data;
    } catch (err: any) {
      setError(err.message || 'Adjudication failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { predict, loading, error, result };
}
```

---

## 12. Support & Verification

To verify that the entire system and all endpoints are functional:
1. Start the server: `python -m uvicorn backend.main:app --port 8000 --reload`
2. Open `http://127.0.0.1:8000/docs` in your browser to test endpoints interactively.
3. Open `http://127.0.0.1:8000/` for the Adjudication Cockpit.
4. Open `http://127.0.0.1:8000/pipeline` for the Multi-Phase Pipeline Command Center.
