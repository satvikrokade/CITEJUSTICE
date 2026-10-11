# CiteJustice: Automated Legal Judgment Prediction for Indian Courts

**CiteJustice** is a state-of-the-art legal AI system incorporating **LexGraphFormer** and the **Dynamic Precedent Evolution Graph (DPEG)**. It solves the critical **"Stale Precedent Pitfall"** of existing legal AI systems (which blindly retrieve overruled cases based purely on semantic text similarity).

---

## 🌟 Key Features & Innovations

1. **Dynamic Precedent Evolution Graph (DPEG):**
   - Replaces naive text similarity with precedent authority tracking.
   - Evaluates legal authority using:
     $$\text{Authority} = 2F + R - D - 3O$$
     where **$F$** = Followed ($+2$), **$R$** = Relied Upon ($+1$), **$D$** = Distinguished ($-1$), and **$O$** = Overruled ($-3$ penalty).
   - Eliminates zombie law from influencing judgment predictions.

2. **Graph Transformer Precedent Reasoning (LexGraphFormer):**
   - Uses PyTorch-based multi-head Graph Attention:
     $$H_{\text{new}} = \text{Transformer}(H_{\text{old}}, G)$$
   - Propagates heterogeneous citation edges directly into the reasoning representation.

3. **Bilingual Statutory Cross-Mapper (IPC 1860 $\leftrightarrow$ BNS 2023):**
   - Resolves historical IPC / CrPC / IEA sections to the new Bharatiya Nyaya Sanhita (BNS 2023), Bharatiya Nagarik Suraksha Sanhita (BNSS 2023), and Bharatiya Sakshya Adhiniyam (BSA 2023).

4. **Obsidian Dark Glassmorphic 3-Panel Judicial Cockpit:**
   - **Panel 1 (Case Intake Studio):** Form and drag-and-drop file upload with automated statutory section detection.
   - **Panel 2 (Precedent Evolution Workspace):** Physics-driven interactive citation network showing active law vs suppressed overruled law, with comparison mode against naive RAG.
   - **Panel 3 (Adjudication & IRAC Explainer):** Predicted outcome, confidence score dial, appeal vulnerability meter, structured IRAC cards (Issue, Rule, Application, Conclusion), and controlling precedents ranking.

5. **1-Click Official Judicial Report Exporter:**
   - Generates publication-ready PDF and print-ready HTML reports for judges and legal practitioners.

---

## 🚀 How to Run Locally

### 1. Requirements
- Python 3.10+
- Dependencies installed:
  ```bash
  pip install fastapi uvicorn rank-bm25 torch transformers networkx pandas openpyxl reportlab
  ```

### 2. Start the Server
From this directory, run:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Open in Browser
Visit:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🏛️ Benchmark Demonstration Scenarios
From the top navigation bar, select from the pre-loaded legal scenarios:
1. **Sudden Quarrel Homicide (IPC 302 / BNS 103):**
   Demonstrates DPEG penalizing the overruled *Digambar Shankar (1976)* baseline and applying 5-Judge Constitution Bench *Sunder Singh (2016)* to alter conviction under Exception 4 to Section 300 IPC.
2. **Regular Bail Liberty (CrPC 439 / BNSS 483):**
   Applies *Satender Kumar Antil (2022)* and *Arnesh Kumar (2014)* liberty tenets.
3. **FIR Quashing Dispute (CrPC 482 / BNSS 528):**
   Synthesizes *State of Haryana v. Bhajan Lal (1992)* and distinguishes *Neeharika Infrastructure (2021)*.
