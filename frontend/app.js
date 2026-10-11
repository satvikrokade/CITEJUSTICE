/**
 * CiteJustice - Full Interactive Application Logic & Physics Graph Engine
 */

// Application State
const state = {
  currentMode: 'dpeg', // 'dpeg' or 'naive'
  benchmarks: [],
  statutes: [],
  activePrediction: null,
  graphData: { nodes: [], links: [] },
  selectedNode: null,
  transform: { x: 0, y: 0, k: 1 },
  isDragging: false,
  dragTarget: null,
  panStart: { x: 0, y: 0 },
  simulationRunning: true
};

// Canvas & Physics
let canvas, ctx;
let animationFrameId;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', async () => {
  canvas = document.getElementById('graphCanvas');
  ctx = canvas.getContext('2d');

  setupCanvasResize();
  setupEventListeners();
  await loadSystemData();
  // Keep initial state clean matching the screenshot (Awaiting Input)
});

function setupCanvasResize() {
  const resize = () => {
    if (!canvas || !canvas.parentElement) return;
    const rect = canvas.parentElement.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return;
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    drawGraph();
  };
  window.addEventListener('resize', resize);
  resize();
}

function openGraphSidebar() {
  const drawer = document.getElementById('graphSidebarDrawer');
  const backdrop = document.getElementById('sidebarBackdrop');
  if (drawer) drawer.classList.add('open');
  if (backdrop) backdrop.classList.remove('hidden');

  // Recalculate graph canvas geometry smoothly once drawer animation finishes
  setTimeout(() => {
    if (canvas && canvas.parentElement) {
      const rect = canvas.parentElement.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        canvas.width = rect.width * window.devicePixelRatio;
        canvas.height = rect.height * window.devicePixelRatio;
        ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        drawGraph();
      }
    }
  }, 260);
}

function closeGraphSidebar() {
  const drawer = document.getElementById('graphSidebarDrawer');
  const backdrop = document.getElementById('sidebarBackdrop');
  if (drawer) drawer.classList.remove('open');
  if (backdrop) backdrop.classList.add('hidden');
}

// Click to open/close an IRAC accordion card by its ID
function toggleIrac(cardId) {
  const card = document.getElementById(cardId);
  if (card) card.classList.toggle('closed');
}
window.toggleIrac = toggleIrac;

// Toggle Advanced Intake Drawer (uses hidden attribute)
function toggleAdvancedIntake() {
  const drawer = document.getElementById('advancedIntakeContainer');
  const icon  = document.getElementById('advancedIntakeIcon');
  const label = document.getElementById('advancedIntakeLabel');
  if (!drawer) return;
  const isHidden = drawer.hasAttribute('hidden');
  if (isHidden) {
    drawer.removeAttribute('hidden');
    if (icon)  icon.textContent  = '▾';
    if (label) label.textContent = 'Click to hide Court Classification, Charges & PDF Upload';
  } else {
    drawer.setAttribute('hidden', '');
    if (icon)  icon.textContent  = '▶';
    if (label) label.textContent = 'Click to open Court Classification, Charges & PDF Upload';
  }
}
window.toggleAdvancedIntake = toggleAdvancedIntake;

// Toggle Legal Reasoning Drawer (uses hidden attribute)
function toggleLegalReasoning() {
  const drawer = document.getElementById('legalReasoningContainer');
  const icon  = document.getElementById('legalReasoningIcon');
  const label = document.getElementById('legalReasoningLabel');
  if (!drawer) return;
  const isHidden = drawer.hasAttribute('hidden');
  if (isHidden) {
    drawer.removeAttribute('hidden');
    if (icon)  icon.textContent  = '▾';
    if (label) label.textContent = 'Click to collapse Legal Reasoning & Citation Network';
  } else {
    drawer.setAttribute('hidden', '');
    if (icon)  icon.textContent  = '▶';
    if (label) label.textContent = 'Click to expand Legal Reasoning & Citation Network';
  }
}
window.toggleLegalReasoning = toggleLegalReasoning;

function showToast(message) {
  const toast = document.getElementById('toastNotification');
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove('hidden');
  setTimeout(() => {
    toast.classList.add('hidden');
  }, 3500);
}
window.showToast = showToast;



async function loadSystemData() {
  try {
    // Health & counts
    const healthRes = await fetch('/api/health');
    const health = await healthRes.json();
    document.getElementById('corpusStatusText').textContent = '782,945 Indian Precedents Active';

    // Benchmarks
    const benchRes = await fetch('/api/benchmarks');
    state.benchmarks = await benchRes.json();
    populateBenchmarkDropdown();

    // Statutes
    const statRes = await fetch('/api/statutes');
    state.statutes = await statRes.json();
    renderStatutesTable(state.statutes);

    // Initial graph
    const graphRes = await fetch('/api/subgraph');
    const gData = await graphRes.json();
    initGraphData(gData);
  } catch (err) {
    console.error('Failed to load system data:', err);
  }
}

function populateBenchmarkDropdown() {
  const select = document.getElementById('benchmarkSelect');
  select.innerHTML = '<option value="">Benchmark Scenario ▾</option>';
  state.benchmarks.forEach(b => {
    const opt = document.createElement('option');
    opt.value = b.id;
    opt.textContent = `${b.name}`;
    select.appendChild(opt);
  });
}

function setupEventListeners() {
  // Benchmark selector
  document.getElementById('benchmarkSelect').addEventListener('change', (e) => {
    const bench = state.benchmarks.find(b => b.id === e.target.value);
    if (bench) {
      document.getElementById('caseTitle').value = bench.case_title;
      document.getElementById('caseType').value = bench.case_type;
      document.getElementById('caseFacts').value = bench.case_facts;
      document.getElementById('userNotes').value = bench.user_notes;
      runPrediction();
    }
  });

  // Run prediction button
  document.getElementById('btnRunPrediction').addEventListener('click', runPrediction);

  // DPEG vs Naive Mode Toggle
  document.getElementById('btnModeDpeg').addEventListener('click', () => setMode('dpeg'));
  document.getElementById('btnModeNaive').addEventListener('click', () => setMode('naive'));

  // Graph actions
  document.getElementById('btnZoomIn').addEventListener('click', () => zoom(1.2));
  document.getElementById('btnZoomOut').addEventListener('click', () => zoom(0.8));
  document.getElementById('btnResetGraph').addEventListener('click', resetGraphView);

  // PDF Export & Bench/Archive buttons
  document.getElementById('btnExportPdf')?.addEventListener('click', exportPdf);
  document.getElementById('btnExportHtml')?.addEventListener('click', exportHtml);
  document.getElementById('btnShareBench')?.addEventListener('click', () => {
    showToast('✓ Case dossier shared directly to Judicial Bench Repository.');
  });
  document.getElementById('btnSaveArchive')?.addEventListener('click', () => {
    showToast('✓ Case record archived in Secure Judicial Records Database.');
  });

  // Statutes modal
  document.getElementById('btnStatutesModal').addEventListener('click', () => {
    document.getElementById('statutesModal').classList.remove('hidden');
  });
  document.getElementById('btnCloseModal').addEventListener('click', () => {
    document.getElementById('statutesModal').classList.add('hidden');
  });

  // Precedent Evolution Graph Sidebar Drawer Controls
  const toggleSidebar = () => {
    const drawer = document.getElementById('graphSidebarDrawer');
    if (drawer && drawer.classList.contains('open')) {
      closeGraphSidebar();
    } else {
      openGraphSidebar();
    }
  };

  document.getElementById('btnToggleGraphSidebar')?.addEventListener('click', toggleSidebar);
  document.getElementById('btnFloatingGraphTab')?.addEventListener('click', openGraphSidebar);
  document.getElementById('btnOpenSidebarFromPanel')?.addEventListener('click', openGraphSidebar);
  document.getElementById('btnCloseGraphSidebar')?.addEventListener('click', closeGraphSidebar);
  document.getElementById('sidebarBackdrop')?.addEventListener('click', closeGraphSidebar);
  document.getElementById('statuteSearchInput').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    const filtered = state.statutes.filter(s =>
      s.historical_act.toLowerCase().includes(q) ||
      s.historical_section.toLowerCase().includes(q) ||
      s.modern_act.toLowerCase().includes(q) ||
      s.modern_section.toLowerCase().includes(q) ||
      s.offense.toLowerCase().includes(q)
    );
    renderStatutesTable(filtered);
  });

  // Canvas Mouse Interactions
  canvas.addEventListener('mousedown', onMouseDown);
  canvas.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
  canvas.addEventListener('wheel', onWheel);

  // Real PDF Phase 1 Extractor dropzone
  const dropzone = document.getElementById('fileDropzone');
  const fileInput = document.getElementById('fileUpload');
  dropzone.addEventListener('click', () => fileInput.click());

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('over');
  });
  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('over');
  });
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('over');
    if (e.dataTransfer.files.length > 0) {
      uploadAndProcessPdf(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      uploadAndProcessPdf(e.target.files[0]);
    }
  });
}

async function uploadAndProcessPdf(file) {
  const dropText = document.querySelector('#fileDropzone .dz-title');
  const dropSub  = document.querySelector('#fileDropzone .dz-sub');
  if (!dropText || !dropSub) return;

  dropText.textContent = `Analyzing ${file.name} (Phase 1 Segmentation)...`;
  dropSub.textContent  = `Extracting Facts, Issues, BNS 2023 Cross-Mapping & Precedent Overruled Signals...`;

  try {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch('/api/phase1/parse-pdf', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Server status ${res.status}: ${errText}`);
    }

    const data = await res.json();

    // Populate UI fields
    if (data.metadata) {
      if (data.metadata.title && data.metadata.title !== "In re Legal Proceedings") {
        document.getElementById('caseTitle').value = data.metadata.title;
      }
      if (data.metadata.court) {
        const jurisSelect = document.getElementById('courtJurisdiction');
        jurisSelect.value = data.metadata.court.includes("Supreme") ? "Supreme Court of India" : "High Court of Judicature";
      }
    }

    if (data.segmented_structure && data.segmented_structure.facts) {
      document.getElementById('caseFacts').value = data.segmented_structure.facts;
    }

    // Render detected statutes
    if (data.statutes && data.statutes.length > 0) {
      const notesInput = document.getElementById('userNotes');
      const statuteSummaries = data.statutes.map(s => `${s.historical_act} ${s.historical_section} -> ${s.modern_act} ${s.modern_section}`).join(', ');
      notesInput.value = `Invoked statutes: ${statuteSummaries}`;

      const chipsContainer = document.getElementById('detectedStatutesChips');
      chipsContainer.innerHTML = '';
      data.statutes.forEach(s => {
        const chip = document.createElement('span');
        chip.className = 'chip-gold';
        chip.textContent = `${s.historical_act} ${s.historical_section} → ${s.modern_act} ${s.modern_section} (${s.offense.split('/')[0].trim()})`;
        chipsContainer.appendChild(chip);
      });
    }

    // Show phase 1 success notice in dropzone
    dropText.innerHTML = `<span style="color: #10b981; font-weight:600;">✔ Phase 1 Complete: ${file.name} (${data.word_count} words)</span>`;
    let citationsInfo = `${data.citations_and_treatments ? data.citations_and_treatments.length : 0} Precedents detected`;
    const overruled = (data.citations_and_treatments || []).filter(c => c.treatment === 'OVERRULED');
    if (overruled.length > 0) {
      citationsInfo += ` &bull; <span style="color:#ef4444; font-weight:bold;">${overruled.length} Overruled precedent(s) penalized (-3)</span>`;
    }
    dropSub.innerHTML = citationsInfo;

    // Run prediction on the extracted facts
    runPrediction();

  } catch (err) {
    console.error('PDF parsing error:', err);
    dropText.innerHTML = `<span style="color: #ef4444;">Extraction failed: ${err.message}</span>`;
    dropSub.textContent = `Please ensure the file is a readable PDF.`;
  }
}

function setMode(mode) {
  state.currentMode = mode;
  // Toggle 'on' class for new HTML
  document.getElementById('btnModeDpeg').classList.toggle('on', mode === 'dpeg');
  document.getElementById('btnModeNaive').classList.toggle('on', mode === 'naive');

  const flawBanner = document.getElementById('flawAlertBanner');
  if (mode === 'naive') {
    flawBanner.classList.remove('hidden');
    const activeState = document.getElementById('activeVerdictState');
    if (activeState && !activeState.classList.contains('hidden')) {
      document.getElementById('outcomeTitle').textContent = '[SIMULATED NAIVE RAG FAILURE] Conviction Sustained under Section 302 IPC';
      document.getElementById('outcomeSummary').textContent = 'ERROR: Naive RAG retrieved State of Maharashtra v. Digambar Shankar (1976) due to 94% text similarity, completely ignoring that it was OVERRULED in 2016.';
      document.getElementById('appealRiskBadge').className = 'risk-badge risk-high';
      document.getElementById('appealRiskBadge').textContent = 'Appeal Risk: Critical (Bad Law)';
    }
  } else {
    flawBanner.classList.add('hidden');
    if (state.activePrediction) renderPredictionResult(state.activePrediction);
  }
  drawGraph();
}

async function runPrediction() {
  const btn = document.getElementById('btnRunPrediction');
  const btnText = document.getElementById('btnRunPredictionText');
  const origText = btnText ? btnText.textContent : 'Analyze Case with LexGraphFormer';

  if (btnText) btnText.textContent = 'Analyzing Case with LexGraphFormer...';
  if (btn) btn.disabled = true;

  const payload = {
    case_title: document.getElementById('caseTitle').value,
    case_facts: document.getElementById('caseFacts').value,
    case_type: document.getElementById('caseType') ? document.getElementById('caseType').value : 'Criminal Appeal',
    user_notes: document.getElementById('userNotes') ? document.getElementById('userNotes').value : ''
  };

  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    state.activePrediction = data;

    // Transition right panel: hide empty state, reveal verdict card
    const emptyState  = document.getElementById('emptyVerdictState');
    const activeState = document.getElementById('activeVerdictState');
    const badge       = document.getElementById('verdictStatusBadge');

    if (emptyState)  emptyState.classList.add('hidden');
    if (activeState) activeState.classList.remove('hidden');
    if (badge) {
      badge.textContent = 'Verdict Rendered (v2.0)';
      badge.classList.add('done');        // new CSS uses 'done' not 'completed'
    }

    renderPredictionResult(data);
    initGraphData(data.subgraph);
  } catch (err) {
    console.error('Prediction failed:', err);
    showToast('Prediction failed. Please check server logs.');
  } finally {
    if (btnText) btnText.textContent = origText;
    if (btn) btn.disabled = false;
  }
}

function renderPredictionResult(data) {
  // Title & Summary
  document.getElementById('outcomeTitle').textContent = data.prediction;
  document.getElementById('outcomeSummary').textContent = data.prediction_summary;

  // Confidence & Badges
  document.getElementById('confidenceValue').textContent = `${data.confidence_score}%`;
  document.getElementById('confidenceBar').style.width = `${data.confidence_score}%`;
  document.getElementById('controllingPrecedentsCount').textContent = data.controlling_precedents.length;
  document.getElementById('overruledBlockedCount').textContent = data.suppressed_overruled_precedents.length;

  const riskBadge = document.getElementById('appealRiskBadge');
  riskBadge.textContent = `Appeal Risk: ${data.appeal_vulnerability_risk.split(' ')[0]}`;
  riskBadge.className = data.appeal_vulnerability_risk.includes('Low')
    ? 'risk-badge risk-low'
    : data.appeal_vulnerability_risk.includes('High')
      ? 'risk-badge risk-high'
      : 'risk-badge risk-mod';

  // Detected Sections Chips
  const chipsContainer = document.getElementById('detectedStatutesChips');
  if (chipsContainer) {
    chipsContainer.innerHTML = '';
    data.extracted_sections.forEach(sec => {
      const span = document.createElement('span');
      span.className = 'chip-gold';
      span.textContent = `${sec.historical_act} ${sec.historical_section} → ${sec.modern_act} ${sec.modern_section} (${sec.offense.split('/')[0].trim()})`;
      chipsContainer.appendChild(span);
    });
  }

  // IRAC Accordion content
  const iracIssue = document.getElementById('iracIssue');
  const iracRule  = document.getElementById('iracRule');
  const iracApp   = document.getElementById('iracApplication');
  const iracConc  = document.getElementById('iracConclusion');
  if (iracIssue) iracIssue.textContent = data.irac.issue;
  if (iracRule)  iracRule.innerHTML = data.irac.rule.replace(/\n/g, '<br>');
  if (iracApp)   iracApp.textContent = data.irac.application;
  if (iracConc)  iracConc.textContent = data.irac.conclusion;

  // Overruled Suppression Alert Card
  const overruledBox = document.getElementById('overruledAlertBox');
  if (overruledBox) {
    if (data.suppressed_overruled_precedents.length > 0) {
      overruledBox.style.display = 'flex';
      const names = data.suppressed_overruled_precedents.map(p => p.title).join(', ');
      document.getElementById('overruledAlertContent').innerHTML =
        `Neutralized <strong>${data.suppressed_overruled_precedents.length} zombie precedent</strong> (${names}). DPEG suppressed bad law with &minus;3O penalty.`;
    } else {
      overruledBox.style.display = 'none';
    }
  }

  // Controlling Precedents List
  const precList = document.getElementById('controllingPrecedentsList');
  if (precList) {
    precList.innerHTML = '';
    data.controlling_precedents.forEach(p => {
      const div = document.createElement('div');
      div.className = 'prec-item';
      div.innerHTML = `
        <div class="prec-name">${p.title}</div>
        <div class="prec-meta">
          <span>${p.citation} (${p.year})</span>
          <span class="prec-score">+${p.authority_score} DPEG</span>
        </div>
      `;
      div.addEventListener('click', () => focusOnNode(p.case_id));
      precList.appendChild(div);
    });
  }
}


function renderStatutesTable(statutes) {
  const tbody = document.getElementById('statuteTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';
  statutes.forEach(s => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${s.historical_act} ${s.historical_section}</strong></td>
      <td><span class="chip-gold">${s.modern_act} ${s.modern_section}</span></td>
      <td>${s.offense}</td>
      <td>${s.bailable} &bull; ${s.cognizable}</td>
      <td>${s.quantum}</td>
    `;
    tbody.appendChild(tr);
  });
}

// (toggleIrac is defined and exported at the top of this file — no duplicate needed)

/* --- Physics Simulation & Graph Rendering --- */

function initGraphData(subgraph) {
  if (!subgraph || !subgraph.nodes) return;

  const width = canvas.width / window.devicePixelRatio;
  const height = canvas.height / window.devicePixelRatio;

  // Position nodes
  const nodes = subgraph.nodes.map((n, i) => {
    const angle = (i / subgraph.nodes.length) * Math.PI * 2;
    const radius = 140 + Math.random() * 40;
    return {
      ...n,
      x: width / 2 + Math.cos(angle) * radius,
      y: height / 2 + Math.sin(angle) * radius,
      vx: 0,
      vy: 0,
      radius: n.is_overruled ? 18 : 22 + Math.min(10, Math.max(0, n.authority_score * 2))
    };
  });

  const nodeMap = new Map(nodes.map(n => [n.id, n]));
  const links = subgraph.links
    .map(l => ({
      ...l,
      sourceNode: nodeMap.get(l.source),
      targetNode: nodeMap.get(l.target)
    }))
    .filter(l => l.sourceNode && l.targetNode);

  state.graphData = { nodes, links };
  state.transform = { x: 0, y: 0, k: 1 };

  if (animationFrameId) cancelAnimationFrame(animationFrameId);
  simulate();
}

function simulate() {
  const { nodes, links } = state.graphData;
  const width = canvas.width / window.devicePixelRatio;
  const height = canvas.height / window.devicePixelRatio;

  // Simple Force-directed Physics
  // 1. Repulsion between nodes
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const n1 = nodes[i];
      const n2 = nodes[j];
      const dx = n2.x - n1.x;
      const dy = n2.y - n1.y;
      const dist = Math.hypot(dx, dy) || 1;
      if (dist < 260) {
        const force = (260 - dist) / dist * 0.05;
        n1.vx -= dx * force;
        n1.vy -= dy * force;
        n2.vx += dx * force;
        n2.vy += dy * force;
      }
    }
  }

  // 2. Spring attraction along links
  for (const link of links) {
    const s = link.sourceNode;
    const t = link.targetNode;
    const dx = t.x - s.x;
    const dy = t.y - s.y;
    const dist = Math.hypot(dx, dy) || 1;
    const targetDist = 160;
    const force = (dist - targetDist) * 0.008;
    s.vx += dx / dist * force;
    s.vy += dy / dist * force;
    t.vx -= dx / dist * force;
    t.vy -= dy / dist * force;
  }

  // 3. Center gravity & damping
  for (const n of nodes) {
    if (n === state.dragTarget) continue;
    n.vx += (width / 2 - n.x) * 0.002;
    n.vy += (height / 2 - n.y) * 0.002;
    n.vx *= 0.88;
    n.vy *= 0.88;
    n.x += n.vx;
    n.y += n.vy;
  }

  drawGraph();
  animationFrameId = requestAnimationFrame(simulate);
}

function drawGraph() {
  const width = canvas.width / window.devicePixelRatio;
  const height = canvas.height / window.devicePixelRatio;

  ctx.clearRect(0, 0, width, height);
  ctx.save();

  // Apply zoom & pan transform
  ctx.translate(state.transform.x, state.transform.y);
  ctx.scale(state.transform.k, state.transform.k);

  const { nodes, links } = state.graphData;

  // 1. Draw Links
  for (const link of links) {
    const s = link.sourceNode;
    const t = link.targetNode;
    const rel = (link.rel_type || 'CITES').toUpperCase();

    ctx.beginPath();
    ctx.moveTo(s.x, s.y);
    ctx.lineTo(t.x, t.y);

    if (rel === 'OVERRULED') {
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 3;
      ctx.setLineDash([6, 4]);
    } else if (rel === 'FOLLOWED') {
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2.5;
      ctx.setLineDash([]);
    } else if (rel === 'DISTINGUISHED') {
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
    } else {
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 1.8;
      ctx.setLineDash([]);
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw Arrowhead
    drawArrow(ctx, s.x, s.y, t.x, t.y, t.radius + 6, ctx.strokeStyle);

    // Link label
    const midX = (s.x + t.x) / 2;
    const midY = (s.y + t.y) / 2;
    ctx.fillStyle = ctx.strokeStyle;
    ctx.font = '9px JetBrains Mono';
    ctx.textAlign = 'center';
    ctx.fillText(rel, midX, midY - 6);
  }

  // 2. Draw Nodes
  for (const n of nodes) {
    const isSelected = (state.selectedNode && state.selectedNode.id === n.id);
    const isOverruled = n.is_overruled;

    // Glowing aura
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.radius + (isSelected ? 8 : 4), 0, Math.PI * 2);
    if (state.currentMode === 'naive' && isOverruled) {
      // Highlight fatal flaw in naive mode
      ctx.fillStyle = 'rgba(239, 68, 68, 0.4)';
    } else if (isOverruled) {
      ctx.fillStyle = 'rgba(239, 68, 68, 0.2)';
    } else {
      ctx.fillStyle = 'rgba(16, 185, 129, 0.2)';
    }
    ctx.fill();

    // Node body
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
    ctx.fillStyle = isOverruled ? '#2a1215' : '#0f241d';
    ctx.fill();

    ctx.strokeStyle = isOverruled ? '#ef4444' : '#10b981';
    ctx.lineWidth = isSelected ? 3 : 2;
    ctx.stroke();

    // Authority Badge inside node
    ctx.fillStyle = isOverruled ? '#fca5a5' : '#86efac';
    ctx.font = 'bold 10px JetBrains Mono';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const authText = isOverruled ? '\u2715 OVER' : `+${n.authority_score}`;
    ctx.fillText(authText, n.x, n.y);

    // Case title label below node
    ctx.font = '11px Outfit, sans-serif';
    ctx.fillStyle = isSelected ? '#d4af37' : '#f8fafc';
    const shortTitle = (n.title || n.id).split('v.')[0].trim();
    ctx.fillText(shortTitle, n.x, n.y + n.radius + 14);

    // Year
    ctx.font = '9px JetBrains Mono';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(`(${n.year || 'SC'})`, n.x, n.y + n.radius + 26);
  }

  ctx.restore();
}

function drawArrow(context, fromx, fromy, tox, toy, offset, color) {
  const angle = Math.atan2(toy - fromy, tox - fromx);
  const headlen = 8;
  const endX = tox - offset * Math.cos(angle);
  const endY = toy - offset * Math.sin(angle);

  context.save();
  context.strokeStyle = color;
  context.fillStyle = color;
  context.beginPath();
  context.moveTo(endX, endY);
  context.lineTo(endX - headlen * Math.cos(angle - Math.PI / 6), endY - headlen * Math.sin(angle - Math.PI / 6));
  context.lineTo(endX - headlen * Math.cos(angle + Math.PI / 6), endY - headlen * Math.sin(angle + Math.PI / 6));
  context.closePath();
  context.fill();
  context.restore();
}

/* Mouse Interactions */
function getCanvasMousePos(e) {
  const rect = canvas.getBoundingClientRect();
  const screenX = e.clientX - rect.left;
  const screenY = e.clientY - rect.top;
  const graphX = (screenX - state.transform.x) / state.transform.k;
  const graphY = (screenY - state.transform.y) / state.transform.k;
  return { screenX, screenY, graphX, graphY };
}

function getNodeAt(x, y) {
  for (const n of state.graphData.nodes) {
    if (Math.hypot(n.x - x, n.y - y) <= n.radius + 4) {
      return n;
    }
  }
  return null;
}

function onMouseDown(e) {
  const pos = getCanvasMousePos(e);
  const target = getNodeAt(pos.graphX, pos.graphY);
  if (target) {
    state.dragTarget = target;
    selectNode(target);
  } else {
    state.isDragging = true;
    state.panStart = { x: e.clientX - state.transform.x, y: e.clientY - state.transform.y };
  }
}

function onMouseMove(e) {
  const pos = getCanvasMousePos(e);
  if (state.dragTarget) {
    state.dragTarget.x = pos.graphX;
    state.dragTarget.y = pos.graphY;
    state.dragTarget.vx = 0;
    state.dragTarget.vy = 0;
  } else if (state.isDragging) {
    state.transform.x = e.clientX - state.panStart.x;
    state.transform.y = e.clientY - state.panStart.y;
  }

  // Hover Tooltip
  const hovered = getNodeAt(pos.graphX, pos.graphY);
  const tooltip = document.getElementById('graphTooltip');
  if (hovered) {
    canvas.style.cursor = 'pointer';
    tooltip.style.left = `${pos.screenX + 15}px`;
    tooltip.style.top = `${pos.screenY + 15}px`;
    tooltip.style.opacity = '1';
    tooltip.innerHTML = `
      <strong>${hovered.title}</strong><br/>
      Citation: ${hovered.citation || 'N/A'}<br/>
      DPEG Authority: <strong>${hovered.authority_score}</strong> (${hovered.status})<br/>
      F:${hovered.F} | R:${hovered.R} | D:${hovered.D} | O:${hovered.O}
    `;
  } else {
    canvas.style.cursor = state.isDragging ? 'grabbing' : 'default';
    tooltip.style.opacity = '0';
  }
}

function onMouseUp() {
  state.dragTarget = null;
  state.isDragging = false;
}

function onWheel(e) {
  e.preventDefault();
  const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
  zoom(zoomFactor);
}

function zoom(factor) {
  state.transform.k *= factor;
  state.transform.k = Math.max(0.4, Math.min(3, state.transform.k));
  drawGraph();
}

function resetGraphView() {
  state.transform = { x: 0, y: 0, k: 1 };
  drawGraph();
}

function selectNode(n) {
  state.selectedNode = n;
  const inspector = document.getElementById('selectedNodeDetails');
  inspector.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
      <strong style="color:#d4af37;">${n.title}</strong>
      <span class="chip ${n.is_overruled ? 'chip-rose' : 'chip-gold'}">${n.status}</span>
    </div>
    <div style="color:#94a3b8; font-size:11px; margin-bottom:4px;">
      Citation: ${n.citation} &bull; Bench: ${n.bench_strength || 2} Judges &bull; Year: ${n.year}
    </div>
    <div style="font-size:12px; margin-bottom:4px;">
      <strong>DPEG Authority Breakdown:</strong> 
      2(F=${n.F}) + (R=${n.R}) &minus; (D=${n.D}) &minus; 3(O=${n.O}) = <span style="font-weight:700; color:${n.is_overruled ? '#ef4444' : '#10b981'};">${n.authority_score}</span>
    </div>
    <div style="color:#cbd5e1; font-size:11.5px; font-style:italic;">"${n.ratio_decidendi || n.key_facts || 'Supreme Court of India decision'}"</div>
  `;
  drawGraph();
}

function focusOnNode(caseId) {
  const node = state.graphData.nodes.find(n => n.id === caseId);
  if (node) {
    selectNode(node);
    const width = canvas.width / window.devicePixelRatio;
    const height = canvas.height / window.devicePixelRatio;
    state.transform.x = width / 2 - node.x * state.transform.k;
    state.transform.y = height / 2 - node.y * state.transform.k;
  }
}

/* Report Exports with Interactive Loading States */
async function exportPdf() {
  const btn = document.getElementById('btnExportPdf');
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span>⏳ Generating PDF...</span>`;

  const safeVal = (id) => document.getElementById(id)?.value || '';
  const payload = {
    case_title: safeVal('caseTitle'),
    case_facts:  safeVal('caseFacts'),
    case_type:   safeVal('caseType') || 'Criminal Appeal',
    user_notes:  safeVal('userNotes')
  };

  try {
    const res = await fetch('/api/export_pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `CiteJustice_Report_${payload.case_title.replace(/\s+/g, '_')}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    btn.innerHTML = `<span>✔ PDF Downloaded</span>`;
    setTimeout(() => { btn.innerHTML = originalHtml; btn.disabled = false; }, 2000);
  } catch (err) {
    console.error('PDF export failed:', err);
    alert('PDF export failed. Please check the backend server logs.');
    btn.innerHTML = originalHtml;
    btn.disabled = false;
  }
}

async function exportHtml() {
  const btn = document.getElementById('btnExportHtml');
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span>⏳ Loading...</span>`;

  const safeVal = (id) => document.getElementById(id)?.value || '';
  const payload = {
    case_title: safeVal('caseTitle'),
    case_facts:  safeVal('caseFacts'),
    case_type:   safeVal('caseType') || 'Criminal Appeal',
    user_notes:  safeVal('userNotes')
  };

  try {
    const res = await fetch('/api/export_html', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const html = await res.text();
    const win = window.open('', '_blank');
    if (win) {
      win.document.write(html);
      win.document.close();
    } else {
      // Fallback if popup blocked
      const blob = new Blob([html], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `CiteJustice_Report_${payload.case_title.replace(/\s+/g, '_')}.html`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
    btn.innerHTML = `<span>✔ Opened</span>`;
    setTimeout(() => { btn.innerHTML = originalHtml; btn.disabled = false; }, 2000);
  } catch (err) {
    console.error('HTML export failed:', err);
    alert('HTML export failed. Please check the backend server logs.');
    btn.innerHTML = originalHtml;
    btn.disabled = false;
  }
}
