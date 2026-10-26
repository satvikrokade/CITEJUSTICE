/**
 * CiteJustice API Client Module
 * Provides unified, promise-based REST API access for the Frontend Engineer.
 * Includes complete error handling, response typing, and helper download methods.
 */

const CiteJusticeAPI = {
  BASE_URL: '/api',

  /**
   * Helper internal fetch wrapper with automatic JSON error parsing
   */
  async _request(endpoint, options = {}) {
    const url = `${this.BASE_URL}${endpoint}`;
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorJson = await response.json();
          if (errorJson && errorJson.detail) {
            errorMsg = errorJson.detail;
          }
        } catch (_) {}
        throw new Error(errorMsg);
      }
      return response;
    } catch (err) {
      console.error(`[CiteJusticeAPI] Request failed for ${endpoint}:`, err);
      throw err;
    }
  },

  // ==========================================
  // 1. SYSTEM & METADATA
  // ==========================================

  /**
   * Check backend server health, indexed nodes, and active judgment count.
   * @returns {Promise<{status: string, service: string, version: string, dpeg_nodes_indexed: number, dpeg_edges_indexed: number, corpus_judgments_indexed: number}>}
   */
  async getHealth() {
    const res = await this._request('/health');
    return await res.json();
  },

  /**
   * Fetch pre-configured benchmark legal scenarios.
   * @returns {Promise<Array<{id: string, name: string, case_title: string, case_type: string, case_facts: string, user_notes: string, highlight: string}>>}
   */
  async getBenchmarks() {
    const res = await this._request('/benchmarks');
    return await res.json();
  },

  // ==========================================
  // 2. STATUTORY CROSS-MAPPING
  // ==========================================

  /**
   * Fetch the full catalog of colonial (IPC/CrPC/IEA) to modern (BNS/BNSS/BSA 2023) mappings.
   * @returns {Promise<Array<Object>>}
   */
  async getAllStatutes() {
    const res = await this._request('/statutes');
    return await res.json();
  },

  /**
   * Lookup a specific section (e.g. "IPC 302" or "Section 439 CrPC").
   * @param {string} section 
   * @returns {Promise<Object>}
   */
  async lookupStatute(section) {
    const res = await this._request('/statutes/lookup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ section })
    });
    return await res.json();
  },

  // ==========================================
  // 3. PHASE 1 PARSING & DOCUMENT INTAKE
  // ==========================================

  /**
   * Parse a raw judicial judgment PDF file via multipart/form-data.
   * Extracts metadata, segmented facts/ratio, statutes, and citation treatments.
   * @param {File} file 
   * @returns {Promise<{metadata: Object, word_count: number, segmented_structure: Object, statutes: Array, citations_and_treatments: Array}>}
   */
  async parsePdf(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await this._request('/phase1/parse-pdf', {
      method: 'POST',
      body: formData
    });
    return await res.json();
  },

  /**
   * Parse raw text of an Indian court judgment.
   * @param {string} rawText 
   * @returns {Promise<Object>}
   */
  async parseText(rawText) {
    const res = await this._request('/phase1/parse-text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_text: rawText })
    });
    return await res.json();
  },

  // ==========================================
  // 4. JUDICIAL PREDICTION & ADJUDICATION
  // ==========================================

  /**
   * Primary Legal Judgment Prediction & Explainability pipeline.
   * @param {{case_title: string, case_facts: string, case_type?: string, user_notes?: string}} caseData 
   * @returns {Promise<{case_title: string, prediction: string, prediction_summary: string, confidence_score: number, appeal_vulnerability_risk: string, irac: Object, controlling_precedents: Array, suppressed_overruled_precedents: Array, subgraph: Object}>}
   */
  async predictCase(caseData) {
    const res = await this._request('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(caseData)
    });
    return await res.json();
  },

  /**
   * Retrieve precedent citation graph nodes and links for force-directed canvas.
   * @param {Array<string>} [caseIds] 
   * @returns {Promise<{nodes: Array, links: Array}>}
   */
  async getSubgraph(caseIds = []) {
    const query = caseIds && caseIds.length > 0 ? `?cases=${encodeURIComponent(caseIds.join(','))}` : '';
    const res = await this._request(`/subgraph${query}`);
    return await res.json();
  },

  // ==========================================
  // 5. REPORT EXPORTING
  // ==========================================

  /**
   * Generates and triggers automatic browser download for the official Judicial PDF Report.
   * @param {{case_title: string, case_facts: string, case_type?: string, user_notes?: string}} caseData 
   * @param {string} [customFilename]
   */
  async downloadPdfReport(caseData, customFilename) {
    const res = await this._request('/export_pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(caseData)
    });
    const blob = await res.blob();
    const filename = customFilename || `CiteJustice_Report_${(caseData.case_title || 'Case').replace(/\s+/g, '_')}.pdf`;
    
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => window.URL.revokeObjectURL(url), 1000);
  },

  /**
   * Generates formatted printable HTML report.
   * @param {{case_title: string, case_facts: string, case_type?: string, user_notes?: string}} caseData 
   * @returns {Promise<string>} HTML text
   */
  async getHtmlReport(caseData) {
    const res = await this._request('/export_html', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(caseData)
    });
    return await res.text();
  },

  // ==========================================
  // 6. PIPELINE DASHBOARD (/pipeline)
  // ==========================================

  /**
   * List all stored pipeline runs.
   * @returns {Promise<Array<Object>>}
   */
  async listPipelineRuns() {
    const res = await this._request('/pipeline/runs');
    return await res.json();
  },

  /**
   * Create a new tracking session.
   * @param {string} [name]
   * @returns {Promise<Object>}
   */
  async createPipelineRun(name = 'New Judicial Analysis') {
    const res = await this._request(`/pipeline/create?name=${encodeURIComponent(name)}`, {
      method: 'POST'
    });
    return await res.json();
  },

  /**
   * Fetch complete multi-phase run data by ID.
   * @param {string} runId 
   * @returns {Promise<Object>}
   */
  async getPipelineRun(runId) {
    const res = await this._request(`/pipeline/${encodeURIComponent(runId)}`);
    return await res.json();
  },

  /**
   * Execute Phase 1 for a run via uploaded PDF file.
   * @param {string} runId
   * @param {File} file
   * @returns {Promise<Object>}
   */
  async executePhase1Pdf(runId, file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await this._request(`/pipeline/${encodeURIComponent(runId)}/phase1-pdf`, {
      method: 'POST',
      body: formData
    });
    return await res.json();
  },

  /**
   * Execute Phase 1 for a run via raw text.
   * @param {string} runId
   * @param {string} rawText
   * @returns {Promise<Object>}
   */
  async executePhase1Text(runId, rawText) {
    const res = await this._request(`/pipeline/${encodeURIComponent(runId)}/phase1-text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_text: rawText })
    });
    return await res.json();
  },

  /**
   * Execute Phase 2: DPEG Multigraph & Hybrid Retrieval Indexing.
   * @param {string} runId
   * @returns {Promise<Object>}
   */
  async executePhase2(runId) {
    const res = await this._request(`/pipeline/${encodeURIComponent(runId)}/phase2`, {
      method: 'POST'
    });
    return await res.json();
  },

  /**
   * Execute Phase 3: LexGraphFormer Graph Transformer Inference.
   * @param {string} runId
   * @returns {Promise<Object>}
   */
  async executePhase3(runId) {
    const res = await this._request(`/pipeline/${encodeURIComponent(runId)}/phase3`, {
      method: 'POST'
    });
    return await res.json();
  },

  /**
   * Execute Phase 4: IRAC Verdict & Appeal Risk Synthesis.
   * @param {string} runId
   * @returns {Promise<Object>}
   */
  async executePhase4(runId) {
    const res = await this._request(`/pipeline/${encodeURIComponent(runId)}/phase4`, {
      method: 'POST'
    });
    return await res.json();
  },

  /**
   * Execute all 4 pipeline phases sequentially from judgment text.
   * @param {string} rawText 
   * @param {string} [name] 
   * @returns {Promise<Object>}
   */
  async runPipelineAllText(rawText, name = 'End-to-End Analysis') {
    const res = await this._request(`/pipeline/run-all-text?name=${encodeURIComponent(name)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_text: rawText })
    });
    return await res.json();
  },

  /**
   * Execute all 4 pipeline phases sequentially from uploaded PDF.
   * @param {File} file 
   * @returns {Promise<Object>}
   */
  async runPipelineAllPdf(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await this._request('/pipeline/run-all-pdf', {
      method: 'POST',
      body: formData
    });
    return await res.json();
  }
};

// Expose globally for vanilla JS browsers or module exports
if (typeof window !== 'undefined') {
  window.CiteJusticeAPI = CiteJusticeAPI;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CiteJusticeAPI;
}
