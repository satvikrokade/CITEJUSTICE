# CiteJustice (LexGraphFormer) — Phase 1 & Scaled Ingestion Guide

This document is your definitive operational and architectural guide for **Phase 1: Ingestion, Legal Structural Segmentation, and Precedent Treatment Analysis**. It explains what data you need, whether cleaning is required, how to ingest Hugging Face datasets, how to use the **Multi-Phase Pipeline Command Center (`/pipeline`)**, and your **Week-by-Week Implementation Plan**.

---

## 1. What Type of Data is Required?

CiteJustice can consume raw judicial judgments in multiple formats:

### A. Supported Data Formats
1. **Raw PDF Documents**: Scanned or digital judicial judgment PDFs from the Supreme Court of India or High Courts.
2. **Text / JSON / JSONL**: Text dumps or exported records from platforms like eCourts, Indian Kanoon, or SCR.
3. **Parquet / Tabular Data**: Formats like `metadata.parquet` or `.xlsx` containing judicial datasets.
4. **Hugging Face Datasets**: Public or private datasets hosted on Hugging Face (e.g., `ILDC`, `InLegalScorer`, `NyayaAnumana`).

### B. Required Fields (If Using Structured / Tabular Data)
If you are loading data from Hugging Face or Parquet, you only need **one core text column**:

| Field Name | Status | Description |
| :--- | :--- | :--- |
| **`text`** (or `judgment` / `facts`) | **MANDATORY** | The complete text or factual matrix of the judgment. |
| `case_id` / `id` | Optional | Unique identifier (auto-generated if missing). |
| `title` | Optional | E.g., *"Mohan Lal v. State of Rajasthan"* (auto-extracted if missing). |
| `court` | Optional | E.g., *"Supreme Court of India"* (auto-detected if missing). |
| `year` | Optional | Decision year (auto-extracted from text if missing). |
| `bench_strength` | Optional | Number of judges on the bench (auto-inferred from judge names). |

---

## 2. Does the Data Need to be Cleaned Beforehand?

### Short Answer: **NO heavy manual cleaning is required!**

The CiteJustice Phase 1 Parser ([`backend/modules/phase1_parser.py`](file:///d:/DATASET%20COURT%20VERDICTS/backend/modules/phase1_parser.py)) is specifically built with legal heuristic filters to handle raw judicial text:

### What the Parser Automatically Cleans & Handles:
1. **Boilerplate Removal**: Ignores court procedural headers, appearance rolls, advocate lists, and decree stamps.
2. **Entity & Party Extraction**: Uses regular expressions to extract Petitioner vs. Respondent, court names, and bench strength.
3. **Statute Normalization**: Identifies historical colonial references (e.g., `Section 302 IPC`, `439 CrPC`, `27 IEA`) and automatically maps them into **BNS, BNSS, and BSA 2023**.
4. **Precedent Treatment Detection**: Detects judicial treatment keywords around citations (*"overruled in"*, *"followed with approval"*, *"distinguished"*) and calculates the dynamic authority adjustment:
   $$\text{Authority Mod} = 2F + R - D - 3O$$
5. **Structural Splitting**: Isolates the operative **Facts**, **Issues**, **Ratio Decidendi**, and **Final Order**.

### The Only 2 Things to Check (Best Practices):
- **Filter Out Empty / 1-Sentence Daily Orders**: Some court scrapers include administrative notices (e.g., *"List on Tuesday"*, *"Notice returnable in 4 weeks"*). Any text shorter than **100 words** is automatically skipped by the batch engine.
- **OCR Quality**: If using scanned PDFs, ensure the PDF has a selectable text layer (Tesseract OCR). Digital PDFs (e.g. from the Supreme Court website) work immediately with 100% accuracy.

---

## 3. Can We Use Hugging Face Data? (Yes!)

Yes! India's legal AI research community has released several large-scale datasets on Hugging Face that are 100% compatible with CiteJustice:

### Recommended Hugging Face Datasets:
1. **`Exploration-Lab/InLegalScorer`**: Curated Supreme Court judgments with marked Ratio Decidendi.
2. **`ILDC` (Indian Legal Documents Corpus)**: Over 35,000 Supreme Court judgments annotated with judicial decisions.
3. **`NyayaAnumana` / `KanoonGPT`**: Indian case laws across High Courts and tribunals.
4. **Your Own Private Hugging Face Dataset**: Any dataset you upload to `https://huggingface.co/datasets`.

### How to Stream & Ingest Hugging Face Data into Phase 1:

We built a dedicated ingestion script for you: [`scripts/ingest_huggingface_dataset.py`](file:///d:/DATASET%20COURT%20VERDICTS/scripts/ingest_huggingface_dataset.py).

#### 1. Install Hugging Face `datasets`:
```bash
pip install datasets
```

#### 2. Run Ingestion (Streams directly into Phase 1):
```bash
# Ingest 1,000 cases from Hugging Face into Phase 1 JSONL
python scripts/ingest_huggingface_dataset.py --dataset "Exploration-Lab/InLegalScorer" --max_samples 1000 --output "phase1_hf_corpus.jsonl"
```

#### 3. Ingesting Your Own Private Hugging Face Dataset:
```bash
# Replace with your dataset repo and text column name
python scripts/ingest_huggingface_dataset.py --dataset "your-username/your-indian-judgments" --text_col "judgment_text" --output "phase1_extracted_corpus.jsonl"
```

The script streams the dataset without consuming your RAM and outputs a clean, segmented `phase1_extracted_corpus.jsonl` ready for Phase 2!

---

## 4. How to Manage Everything: The Pipeline Command Center (`/pipeline`)

Rather than running commands in the dark, CiteJustice includes a **dedicated web dashboard** that lets you manage each phase, inspect the stored outputs, and connect them end-to-end.

### Accessing the Dashboard:
Open your browser to:
👉 **[http://127.0.0.1:8000/pipeline](http://127.0.0.1:8000/pipeline)**

*(Or click the gold **"Phase Pipeline Manager"** button in the header of the main cockpit at `http://127.0.0.1:8000`)*

```
┌────────────────────────────────────────────────────────┐
│             Stored Runs History (Left Sidebar)         │
│   • Switch between past cases & view completion badges │
│     [P1] [P2] [P3] [P4]                                │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│            Interactive 4-Phase Stepper Cards           │
│                                                        │
│  [ Phase 1: Ingestion & Structural Segmentation ]      │
│    • Upload PDF or paste text                          │
│    • Stored Output: Title, Court, BNS 2023, Citations, │
│      Facts, Ratio Decidendi.                           │
│                                                        │
│  [ Phase 2: DPEG Multigraph & Retrieval Indexing ]     │
│    • Connects Phase 1 facts into the 907-case graph    │
│    • Stored Output: Authority scores & candidates.     │
│                                                        │
│  [ Phase 3: LexGraphFormer Graph Transformer ]         │
│    • Edge-conditioned GNN attention                    │
│    • Stored Output: Attention weights & penalty audit. │
│                                                        │
│  [ Phase 4: IRAC Verdict & Appeal Risk Synthesis ]     │
│    • Synthesizes formal legal reasoning into IRAC      │
│    • Stored Output: Verdict decree & Appeal Risk %.    │
└────────────────────────────────────────────────────────┘
```

- **Output Persistence**: Every single phase writes its output into `storage/pipeline_runs/<run_id>.json`.
- **JSON Inspector**: Every card includes an expandable **"Copy JSON"** viewer so you can verify the exact data generated.
- **One-Click End-to-End**: Click **"Execute All 4 Phases End-to-End"** to run the complete pipeline automatically.

---

## 5. Implementation Roadmap for This Week

Follow this daily plan to test and scale your dataset:

### 📅 Monday: Dataset Acquisition & Verification
- Select your data source:
  - Option A: Your local judgment PDFs in a folder.
  - Option B: A Hugging Face dataset (e.g. `Exploration-Lab/InLegalScorer` or `ILDC`).
- Run a quick 10-case test ingestion to confirm fields:
  ```bash
  python scripts/ingest_huggingface_dataset.py --max_samples 10 --output "test_sample.jsonl"
  ```

### 📅 Tuesday: Batch Phase 1 Execution
- Run the batch extractor on your primary dataset (e.g., 5,000 to 50,000 cases or on a free Kaggle GPU notebook):
  ```bash
  python scripts/batch_phase1_extractor.py --input_dir /path/to/pdfs --output_file phase1_corpus.jsonl --workers 8
  ```
- Verify the output: Ensure `phase1_corpus.jsonl` contains structured metadata, statutes mapped to BNS 2023, and citation treatment flags.

### 📅 Wednesday: Pipeline Manager Inspection & Verification
- Open **`http://127.0.0.1:8000/pipeline`**.
- Click **"New Pipeline Run"** and upload sample judgments from your extracted corpus.
- Step through Phase 1 $\rightarrow$ Phase 2 $\rightarrow$ Phase 3 $\rightarrow$ Phase 4.
- Inspect the stored JSON outputs in each phase card.

### 📅 Thursday: DPEG Multigraph Scaling (Phase 2 Linking)
- Ingest the extracted citations from `phase1_corpus.jsonl` into the DPEG multigraph engine.
- Verify that overruled cases (e.g. *Digambar Shankar*, *Bachan Singh* exceptions) correctly receive the **$-3$ penalty** and are suppressed.

### 📅 Friday: Benchmark Predictions & Thesis Documentation
- Run the 3 landmark legal benchmark scenarios in the Cockpit (`http://127.0.0.1:8000`).
- Export judicial IRAC PDF reports.
- Verify comparison against standard similarity RAG (showing how naive RAG fails on overruled cases while CiteJustice succeeds).
