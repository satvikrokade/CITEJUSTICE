# CiteJustice — Complete REST API Specification & Frontend Integration Guide

> **Target Audience:** Frontend Engineer (Member 1) & Backend Engineer (Member 2)  
> **Base URL:** `http://127.0.0.1:8000/api`  
> **Interactive Swagger UI:** `http://127.0.0.1:8000/docs`  
> **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`  
> **Status:** Active & Ready for Production

---

## 1. Architecture Overview & Base Conventions

### Headers
* **Standard JSON Endpoints:** `Content-Type: application/json`
* **File Upload Endpoints:** `Content-Type: multipart/form-data`
* **PDF Download Endpoints:** `Accept: application/pdf`

### HTTP Status Codes
| Status | Meaning | Scenario |
| :---: | :--- | :--- |
| **`200 OK`** | Success | Request succeeded; response payload in body. |
| **`400 Bad Request`** | Validation/Input Error | Missing required fields, unreadable PDF, or invalid text length (< 100 words). |
| **`404 Not Found`** | Resource Missing | Statute section not found in registry, or pipeline run ID doesn't exist. |
| **`500 Internal Error`** | Server / Inference Error | Model runtime exception or unhandled backend error. |

---

## 2. API Endpoint Directory

```
├── System & Catalog
│   ├── GET  /api/health
│   ├── GET  /api/benchmarks
│   ├── GET  /api/statutes
│   └── POST /api/statutes/lookup
│
├── Judicial Adjudication (Main Cockpit)
│   ├── POST /api/predict
│   ├── GET  /api/subgraph
│   ├── POST /api/export_pdf
│   └── POST /api/export_html
│
├── Phase 1 Extraction (Standalone)
│   ├── POST /api/phase1/parse-text
│   └── POST /api/phase1/parse-pdf
│
└── Pipeline Command Center (/pipeline)
    ├── GET  /api/pipeline/runs
    ├── POST /api/pipeline/create
    ├── GET  /api/pipeline/{run_id}
    ├── POST /api/pipeline/{run_id}/phase1-pdf
    ├── POST /api/pipeline/{run_id}/phase1-text
    ├── POST /api/pipeline/{run_id}/phase2
    ├── POST /api/pipeline/{run_id}/phase3
    ├── POST /api/pipeline/{run_id}/phase4
    ├── POST /api/pipeline/run-all-text
    └── POST /api/pipeline/run-all-pdf
```

---

## 3. Endpoints Detail & Schemas

### 3.1. System & Health Check

#### `GET /api/health`
Checks backend engine status, count of indexed precedent nodes, and active judgment count.

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

---

### 3.2. Curated Benchmark Scenarios

#### `GET /api/benchmarks`
Returns pre-loaded landmark scenarios used for demonstrations and testing.

**Response `200 OK`:**
```json
[
  {
    "id": "murder-sudden-fight",
    "name": "Sudden Quarrel & Single Fatal Blow (IPC 302 / BNS 103)",
    "case_title": "Rajendra Prasad v. State of U.P.",
    "case_type": "Criminal Appeal",
    "case_facts": "The appellant and the deceased were neighbors who entered into an impromptu altercation regarding water flow. In the heat of the moment, the appellant picked up a wooden sickle and struck a single blow causing death. No prior enmity or premeditation existed.",
    "user_notes": "Prosecution charged under Section 302 IPC (BNS 103). Appellant seeks conversion to Section 304 Part II (BNS 105) citing Exception 4 to Section 300.",
    "highlight": "Demonstrates DPEG penalizing overruled Digambar Shankar (1976) and adopting 5-judge Sunder Singh (2016) & Anbazhagan (2023)."
  }
]
```

---

### 3.3. Statutory Cross-Mapping (Colonial $\leftrightarrow$ Modern)

#### `GET /api/statutes`
Returns all registered mappings (IPC $\leftrightarrow$ BNS 2023, CrPC $\leftrightarrow$ BNSS 2023, IEA $\leftrightarrow$ BSA 2023).

#### `POST /api/statutes/lookup`
Lookup a specific section.

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

---

### 3.4. Primary Adjudication Endpoint (`POST /api/predict`)

This is the primary endpoint for Panel 1 $\rightarrow$ Panel 2 & Panel 3 in the main Cockpit.

**Endpoint:** `POST /api/predict`  
**Headers:** `Content-Type: application/json`

**Request Body:**
```json
{
  "case_title": "Rajendra Prasad v. State of U.P.",
  "case_facts": "The appellant and the deceased were neighbors who entered into an impromptu altercation regarding irrigation water flow. In the heat of the moment, the appellant picked up a wooden stick and struck a single blow causing death. No prior enmity or premeditation existed.",
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
      "historical_act": "IPC",
      "historical_section": "302",
      "modern_act": "BNS 2023",
      "modern_section": "103",
      "offense": "Punishment for Murder"
    }
  ],
  "prediction": "Appeal Allowed in Part: Conviction Modified to Culpable Homicide Not Amounting to Murder",
  "prediction_summary": "Conviction altered from Section 302 IPC (BNS 103) to Section 304 Part I/II IPC (BNS 105). Sentence reduced to period already undergone.",
  "confidence_score": 89.4,
  "appeal_vulnerability_risk": "Low (16.2%) - Fully anchored in 5-Judge Constitution Bench ratio",
  "irac": {
    "issue": "Whether the fatal injury inflicted during a sudden and spontaneous quarrel without premeditation constitutes Murder under Section 300/302 IPC or qualifies for Exception 4 to Section 300.",
    "rule": "1. Exception 4 to Section 300 IPC (BNS 105).\n2. Sunder Singh v. State of Uttarakhand (2016 5-Judge Bench): Overruled Digambar Shankar (1976).\n3. Anbazhagan v. State (2023 INSC 644).",
    "application": "Incident occurred spontaneously without prior enmity. Under older overruled doctrine (Digambar Shankar), conviction would have been sustained. However, DPEG suppressed Digambar Shankar and applied Sunder Singh.",
    "conclusion": "Conviction under Section 302 IPC set aside; appellant convicted under Section 304 Part II IPC."
  },
  "controlling_precedents": [
    {
      "case_id": "SC_2016_SUNDER",
      "title": "Sunder Singh v. State of Uttarakhand",
      "citation": "2016 5-Judge Bench",
      "authority_score": 7.5,
      "treatment": "FOLLOWED",
      "is_overruled": false
    }
  ],
  "suppressed_overruled_precedents": [
    {
      "case_id": "SC_1976_DIGAMBAR",
      "title": "State of Maharashtra v. Digambar Shankar",
      "citation": "AIR 1976 SC 123",
      "authority_score": -3.0,
      "treatment": "OVERRULED",
      "is_overruled": true,
      "overruled_by": "Sunder Singh (2016)"
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
        "id": "CURRENT_CASE",
        "label": "Rajendra Prasad (Current Case)",
        "type": "query",
        "authority": 0,
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
        "source": "CURRENT_CASE",
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
  }
}
```

---

### 3.5. Citation Network Subgraph (`GET /api/subgraph`)

Used by the Canvas / WebGL force-directed graph viewer.

**Endpoint:** `GET /api/subgraph?cases=case1,case2`  
**Query Params:** `cases` (optional, comma-separated case IDs)

**Response `200 OK`:**
```json
{
  "nodes": [
    {
      "id": "node_1",
      "label": "Bachan Singh v. State of Punjab",
      "year": 1980,
      "authority": 8.0,
      "is_overruled": false,
      "court": "Supreme Court of India"
    }
  ],
  "links": [
    {
      "source": "node_1",
      "target": "node_2",
      "relation": "RELIED_UPON",
      "weight": 1.0
    }
  ]
}
```

---

### 3.6. PDF & HTML Report Export

#### `POST /api/export_pdf`
Generates a downloadable, publication-ready PDF judicial report.

* **Headers:** `Content-Type: application/json`
* **Body:** Same as `CasePredictionRequest`
* **Response:** Binary PDF stream (`Content-Type: application/pdf`, `Content-Disposition: attachment; filename="CiteJustice_Report_...pdf"`)

#### `POST /api/export_html`
Generates a printable HTML version of the report.

* **Response:** `200 OK` with raw HTML (`Content-Type: text/html`).

---

### 3.7. Standalone Phase 1 Parsing Endpoints

Used for file drag-and-drop auto-filling in the Case Intake panel.

#### `POST /api/phase1/parse-pdf`
* **Headers:** `Content-Type: multipart/form-data`
* **Form Field:** `file` (binary PDF file)

#### `POST /api/phase1/parse-text`
* **Headers:** `Content-Type: application/json`
* **Body:**
```json
{
  "raw_text": "IN THE SUPREME COURT OF INDIA\nCRIMINAL APPELLATE JURISDICTION..."
}
```

**Response `200 OK`:**
```json
{
  "metadata": {
    "title": "Rajendra Prasad v. State of U.P.",
    "court": "Supreme Court of India",
    "year": 2023,
    "bench_strength": 2
  },
  "word_count": 1420,
  "segmented_structure": {
    "facts": "The appellant and the deceased were neighbors...",
    "issues": "Whether single fatal injury constitutes murder under Section 302 IPC...",
    "ratio_decidendi": "Lack of premeditation invokes Exception 4 to Section 300...",
    "final_order": "Conviction altered to Section 304 Part II IPC."
  },
  "statutes": [
    {
      "historical_act": "IPC",
      "historical_section": "302",
      "modern_act": "BNS 2023",
      "modern_section": "103",
      "offense": "Punishment for Murder"
    }
  ],
  "citations_and_treatments": [
    {
      "citation": "Sunder Singh (2016)",
      "treatment": "FOLLOWED",
      "authority_mod": 2
    },
    {
      "citation": "Digambar Shankar (1976)",
      "treatment": "OVERRULED",
      "authority_mod": -3
    }
  ]
}
```

---

### 3.8. Multi-Phase Pipeline Command Center (`/pipeline`)

Used for the step-by-step inspector interface in [frontend/pipeline.html](file:///d:/DATASET%20COURT%20VERDICTS/frontend/pipeline.html).

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/pipeline/runs` | List all historical pipeline runs and status badges. |
| `POST` | `/api/pipeline/create?name=...` | Create a new run tracking container. |
| `GET` | `/api/pipeline/{run_id}` | Fetch full JSON state of all 4 phases for a specific run. |
| `POST` | `/api/pipeline/{run_id}/phase1-pdf` | Execute Phase 1 via uploaded PDF (`file`). |
| `POST` | `/api/pipeline/{run_id}/phase1-text` | Execute Phase 1 via text (`raw_text`). |
| `POST` | `/api/pipeline/{run_id}/phase2` | Execute Phase 2 (DPEG Multigraph Linking). |
| `POST` | `/api/pipeline/{run_id}/phase3` | Execute Phase 3 (LexGraphFormer GNN Attention). |
| `POST` | `/api/pipeline/{run_id}/phase4` | Execute Phase 4 (IRAC Adjudication & Verdict). |
| `POST` | `/api/pipeline/run-all-text` | Execute all 4 phases end-to-end automatically. |
| `POST` | `/api/pipeline/run-all-pdf` | Execute all 4 phases end-to-end from PDF. |

---

## 4. Frontend Developer Cheat Sheet

### Common Fetch Pattern (JavaScript)

```javascript
// Example: Predict Case
async function predictCase(caseData) {
  const response = await fetch('/api/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(caseData)
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Prediction failed');
  }
  return await response.json();
}

// Example: Upload PDF
async function uploadJudicialPdf(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/phase1/parse-pdf', {
    method: 'POST',
    body: formData
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'PDF parsing failed');
  }
  return await response.json();
}

// Example: Download Official PDF
async function downloadReport(caseData) {
  const response = await fetch('/api/export_pdf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(caseData)
  });
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `CiteJustice_Report_${caseData.case_title.replace(/\s+/g, '_')}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
}
```
