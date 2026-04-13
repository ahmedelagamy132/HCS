// ============================================================
// HCS — Vision Model Testing
// model-testing.js
// ============================================================

const VISION_MODELS = [
  {
    id:           'm0000001-0000-0000-0000-000000000002',
    name:         'Gait Analysis',
    slug:         'gait-analysis',
    type:         'Computer Vision',
    version:      'v2.4.0',
    architecture: 'HRNet + GRU',
    accuracy:     95.1,
    precision:    94.3,
    recall:       95.8,
    f1:           95.0,
    avg_ms:       1400,
    input_fps:    30,
    keypoints:    17,
    status:       'active',
    desc:         'Skeleton keypoint estimation detecting lameness, stride irregularities and performance metrics from stable-mounted or field cameras.',
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4">
      <circle cx="12" cy="4" r="2"/>
      <path d="M10 7l-3 5h5l-2 6"/>
      <path d="M14 7l3 5h-5"/>
      <path d="M7 21l2-3M17 21l-2-3"/>
    </svg>`,
  },
];

// Simulated analysis result templates — randomised slightly each run
function generateGaitResult(videoName) {
  const lameness    = Math.random() < 0.45;
  const grade       = lameness ? (Math.random() < 0.5 ? 1 : 2) : 0;
  const symmetry    = lameness
    ? +(58 + Math.random() * 18).toFixed(1)
    : +(86 + Math.random() * 12).toFixed(1);
  const strideLen   = +(1.8 + Math.random() * 0.6).toFixed(2);
  const strideFreq  = +(1.1 + Math.random() * 0.4).toFixed(2);
  const cadence     = Math.round(strideFreq * 60 * 2);
  const conf        = +(87 + Math.random() * 9).toFixed(1);
  const affected    = lameness
    ? (Math.random() < 0.5 ? ['LF'] : (Math.random() < 0.5 ? ['RF'] : ['LH']))
    : [];
  const limbs = {
    LF: affected.includes('LF') ? 'affected' : 'ok',
    RF: affected.includes('RF') ? 'affected' : 'ok',
    LH: affected.includes('LH') ? 'affected' : 'ok',
    RH: affected.includes('RH') ? 'affected' : 'ok',
  };

  return { lameness, grade, symmetry, strideLen, strideFreq, cadence, conf, affected, limbs, videoName };
}

// ── State ─────────────────────────────────────────────────
let selectedModelIdx = 0;
let uploadedFile     = null;
let analysisResult   = null;
let overlayInterval  = null;

// ── Render model selector ─────────────────────────────────
function renderModelSelector() {
  const el = document.getElementById('model-selector');
  if (!el) return;

  el.innerHTML = VISION_MODELS.map((m, i) => `
    <div class="ms-card ${i === selectedModelIdx ? 'selected' : ''}"
         onclick="selectModel(${i})">
      <div class="ms-top">
        <div class="ms-icon">${m.icon}</div>
        <div>
          <div class="ms-name">${m.name}</div>
          <div class="ms-type">${m.type} · ${m.version}</div>
        </div>
        <span class="badge ${m.status}" style="margin-left:auto">${m.status}</span>
      </div>
      <div class="ms-desc">${m.desc}</div>
      <div class="ms-meta">
        <div class="ms-stat"><strong>${m.accuracy}%</strong> accuracy</div>
        <div class="ms-stat"><strong>${m.keypoints}</strong> keypoints</div>
        <div class="ms-stat"><strong>${m.avg_ms}ms</strong> avg</div>
        <div class="ms-stat"><strong>${m.architecture}</strong></div>
      </div>
    </div>
  `).join('');
}

function selectModel(idx) {
  selectedModelIdx = idx;
  renderModelSelector();

  const m    = VISION_MODELS[idx];
  const badge = document.getElementById('selected-model-badge');
  if (badge) {
    badge.textContent = m.name;
    badge.style.display = '';
  }

  // Re-enable run button if video already loaded
  updateRunBtn();
}

// ── File handling ─────────────────────────────────────────
function initDropZone() {
  const zone = document.getElementById('drop-zone');
  if (!zone) return;

  zone.addEventListener('dragover', e => {
    e.preventDefault();
    zone.classList.add('drag-over');
  });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('video/')) loadVideo(file);
  });

  const input = document.getElementById('file-input');
  if (input) {
    input.addEventListener('change', e => {
      const file = e.target.files[0];
      if (file) loadVideo(file);
    });
  }
}

function loadVideo(file) {
  uploadedFile = file;
  const url    = URL.createObjectURL(file);
  const video  = document.getElementById('video-el');
  const preview = document.getElementById('video-preview');
  const idle   = document.getElementById('dz-idle');
  const zone   = document.getElementById('drop-zone');

  video.src = url;
  video.play();

  // Set info
  document.getElementById('vi-name').textContent = file.name;
  document.getElementById('vi-meta').textContent = formatSize(file.size) + ' · ' + file.type.split('/')[1].toUpperCase();

  preview.style.display = 'block';
  idle.style.display    = 'none';
  zone.classList.add('has-video');

  updateRunBtn();
  clearResults();
}

function removeVideo() {
  const video   = document.getElementById('video-el');
  const preview = document.getElementById('video-preview');
  const idle    = document.getElementById('dz-idle');
  const zone    = document.getElementById('drop-zone');
  const input   = document.getElementById('file-input');

  if (video.src) URL.revokeObjectURL(video.src);
  video.src     = '';
  uploadedFile  = null;

  preview.style.display = 'none';
  idle.style.display    = '';
  zone.classList.remove('has-video');

  const input2 = document.getElementById('file-input');
  if (input2) input2.value = '';

  clearResults();
  updateRunBtn();
}

// ── Run analysis ──────────────────────────────────────────
function runAnalysis() {
  if (!uploadedFile) return;

  const model      = VISION_MODELS[selectedModelIdx];
  const runBtn     = document.getElementById('run-btn');
  const pbWrap     = document.getElementById('progress-bar-wrap');
  const pbFill     = document.getElementById('progress-bar-fill');
  const pStatus    = document.getElementById('progress-status');
  const scanLine   = document.getElementById('scan-line');
  const clearBtn   = document.getElementById('clear-btn');
  const analysisTime = document.getElementById('analysis-time');

  // Disable controls
  runBtn.disabled  = true;
  clearResults();

  // Show progress
  pbWrap.style.display   = 'block';
  pStatus.style.display  = 'block';
  if (scanLine) scanLine.style.display = 'block';

  const steps = [
    [0,   100,  'Loading video stream…'],
    [8,   400,  'Extracting frames at 30 fps…'],
    [20,  700,  'Running pose estimation (HRNet)…'],
    [42,  900,  'Tracking keypoints across frames…'],
    [60,  600,  'Analysing stride patterns (GRU)…'],
    [72,  500,  'Computing symmetry index…'],
    [84,  400,  'Detecting lameness markers…'],
    [92,  300,  'Scoring gait quality…'],
    [97,  300,  'Compiling report…'],
    [100, 200,  'Done.'],
  ];

  const t0 = Date.now();
  let i = 0;

  function nextStep() {
    if (i >= steps.length) {
      // Finish
      const elapsed = ((Date.now() - t0) / 1000).toFixed(2);
      if (scanLine) scanLine.style.display = 'none';
      pbWrap.style.display   = 'none';
      pStatus.style.display  = 'none';
      analysisTime.style.display = '';
      analysisTime.textContent   = `Completed in ${elapsed}s`;
      clearBtn.style.display = '';

      analysisResult = generateGaitResult(uploadedFile.name);
      renderResults(analysisResult);

      // Start skeleton overlay
      startSkeletonOverlay();
      return;
    }

    const [pct, delay, msg] = steps[i];
    pbFill.style.width  = pct + '%';
    pStatus.textContent = msg;
    i++;
    setTimeout(nextStep, delay);
  }

  nextStep();
}

// ── Skeleton overlay ──────────────────────────────────────
// Draws a procedural horse skeleton on top of the video
const SKEL_CONNECTIONS = [
  [0,1],[1,2],[2,3],         // spine
  [2,4],[4,5],[5,6],         // left fore
  [2,7],[7,8],[8,9],         // right fore
  [3,10],[10,11],[11,12],    // left hind
  [3,13],[13,14],[14,15],    // right hind
  [1,16],                    // head/neck
];

function getSkeletonPoints(w, h, t, result) {
  // Base pose — a rough standing horse skeleton relative to canvas size
  const cx = w * 0.5, cy = h * 0.52;
  const sc = Math.min(w, h) * 0.38;

  // Subtle walking oscillation
  const osc  = Math.sin(t * 2.5) * 0.012 * sc;
  const osc2 = Math.sin(t * 2.5 + Math.PI) * 0.012 * sc;

  const LF_aff = result && result.limbs.LF === 'affected';
  const RF_aff = result && result.limbs.RF === 'affected';
  const LH_aff = result && result.limbs.LH === 'affected';
  const RH_aff = result && result.limbs.RH === 'affected';

  const lfShift = LF_aff ? sc * 0.04 : 0;
  const rfShift = RF_aff ? -sc * 0.04 : 0;

  return [
    // 0 withers         1 mid-back         2 shoulder         3 croup
    [cx - 0.05*sc, cy - 0.15*sc],
    [cx,           cy - 0.12*sc],
    [cx - 0.28*sc, cy - 0.10*sc],
    [cx + 0.28*sc, cy - 0.08*sc],
    // 4 LF elbow        5 LF knee          6 LF hoof
    [cx - 0.35*sc, cy + 0.05*sc + osc],
    [cx - 0.37*sc, cy + 0.28*sc + osc + lfShift],
    [cx - 0.36*sc, cy + 0.47*sc + osc + lfShift],
    // 7 RF elbow        8 RF knee          9 RF hoof
    [cx - 0.18*sc, cy + 0.05*sc + osc2],
    [cx - 0.16*sc, cy + 0.28*sc + osc2 + rfShift],
    [cx - 0.15*sc, cy + 0.47*sc + osc2 + rfShift],
    // 10 LH stifle      11 LH hock         12 LH hoof
    [cx + 0.22*sc, cy + 0.05*sc + osc2],
    [cx + 0.24*sc, cy + 0.28*sc + osc2],
    [cx + 0.23*sc, cy + 0.47*sc + osc2],
    // 13 RH stifle      14 RH hock         15 RH hoof
    [cx + 0.36*sc, cy + 0.05*sc + osc],
    [cx + 0.38*sc, cy + 0.28*sc + osc],
    [cx + 0.37*sc, cy + 0.47*sc + osc],
    // 16 head
    [cx - 0.22*sc, cy - 0.38*sc],
  ];
}

function getJointColor(idx, result) {
  if (!result) return '#C47820';
  const affectedJoints = {
    LF: [4,5,6], RF: [7,8,9], LH: [10,11,12], RH: [13,14,15]
  };
  for (const [limb, joints] of Object.entries(affectedJoints)) {
    if (joints.includes(idx) && result.limbs[limb] === 'affected') return '#C04040';
  }
  return '#E09830';
}

function getBoneColor(a, b, result) {
  if (!result) return 'rgba(196,120,32,.7)';
  const affectedJoints = {
    LF: [4,5,6], RF: [7,8,9], LH: [10,11,12], RH: [13,14,15]
  };
  for (const [limb, joints] of Object.entries(affectedJoints)) {
    if (joints.includes(a) && joints.includes(b) && result.limbs[limb] === 'affected')
      return 'rgba(192,64,64,.8)';
  }
  return 'rgba(196,120,32,.65)';
}

function startSkeletonOverlay() {
  const canvas  = document.getElementById('overlay-canvas');
  const video   = document.getElementById('video-el');
  if (!canvas || !video) return;

  if (overlayInterval) cancelAnimationFrame(overlayInterval);

  let t = 0;
  function draw() {
    const w = canvas.offsetWidth, h = canvas.offsetHeight;
    canvas.width  = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, w, h);

    t += 0.016;
    const pts = getSkeletonPoints(w, h, t, analysisResult);

    // Draw bones
    ctx.lineWidth = 1.5;
    for (const [a, b] of SKEL_CONNECTIONS) {
      ctx.beginPath();
      ctx.moveTo(pts[a][0], pts[a][1]);
      ctx.lineTo(pts[b][0], pts[b][1]);
      ctx.strokeStyle = getBoneColor(a, b, analysisResult);
      ctx.stroke();
    }

    // Draw joints
    for (let i = 0; i < pts.length; i++) {
      const [x, y] = pts[i];
      const col = getJointColor(i, analysisResult);
      ctx.beginPath();
      ctx.arc(x, y, i === 16 ? 5 : 3.5, 0, Math.PI * 2);
      ctx.fillStyle = col;
      ctx.fill();
      // glow
      ctx.beginPath();
      ctx.arc(x, y, i === 16 ? 9 : 7, 0, Math.PI * 2);
      ctx.fillStyle = col.replace(')', ',0.12)').replace('rgb', 'rgba').replace('#C04040','rgba(192,64,64,0.12)').replace('#E09830','rgba(224,152,48,0.12)').replace('#C47820','rgba(196,120,32,0.12)');
      ctx.fill();
    }

    // Symmetry line between hoof pairs
    if (analysisResult) {
      ctx.setLineDash([3, 4]);
      ctx.lineWidth = 1;
      ctx.strokeStyle = 'rgba(196,120,32,.3)';
      // Fore symmetry
      ctx.beginPath();
      ctx.moveTo(pts[6][0], pts[6][1]);
      ctx.lineTo(pts[9][0], pts[9][1]);
      ctx.stroke();
      // Hind symmetry
      ctx.beginPath();
      ctx.moveTo(pts[12][0], pts[12][1]);
      ctx.lineTo(pts[15][0], pts[15][1]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    overlayInterval = requestAnimationFrame(draw);
  }

  draw();
}

// ── Render results ─────────────────────────────────────────
function renderResults(r) {
  const container = document.getElementById('res-content');
  const empty     = document.getElementById('res-empty');
  if (!container) return;

  empty.style.display     = 'none';
  container.style.display = 'block';

  const symColor = r.symmetry >= 80 ? 'good' : r.symmetry >= 65 ? 'warn' : 'crit';
  const gradeLabel = ['None (0)', 'Grade 1 — Subtle', 'Grade 2 — Obvious', 'Grade 3 — Consistent', 'Grade 4 — Non-weight bearing', 'Grade 5 — Non-functional'][r.grade] || 'None';
  const lamenessColor = r.lameness ? (r.grade >= 2 ? 'crit' : 'warn') : 'good';

  container.innerHTML = `

    <!-- Symmetry gauge -->
    <div style="text-align:center;padding:.3rem 0 1rem">
      <div style="font-size:.52rem;letter-spacing:.18em;text-transform:uppercase;color:var(--cream-faint);margin-bottom:.4rem">Gait Symmetry Index</div>
      <div style="position:relative;display:inline-block">
        <svg class="gauge-svg" width="160" height="90" viewBox="0 0 160 90">
          <!-- track -->
          <path d="M 16 80 A 64 64 0 0 1 144 80"
                fill="none" stroke="rgba(196,120,32,.12)" stroke-width="8" stroke-linecap="round"/>
          <!-- fill — animate via JS -->
          <path id="gauge-fill"
                d="M 16 80 A 64 64 0 0 1 144 80"
                fill="none"
                stroke="${r.symmetry >= 80 ? 'var(--green)' : r.symmetry >= 65 ? 'var(--amber-lit)' : 'var(--danger)'}"
                stroke-width="8" stroke-linecap="round"
                stroke-dasharray="201"
                stroke-dashoffset="201"
                style="transition:stroke-dashoffset 1.3s cubic-bezier(.22,1,.36,1)"/>
          <!-- tick marks -->
          ${[0,25,50,75,100].map(v => {
            const ang = -180 + v * 1.8;
            const rad = ang * Math.PI / 180;
            const x1  = 80 + 56 * Math.cos(rad), y1 = 80 + 56 * Math.sin(rad);
            const x2  = 80 + 63 * Math.cos(rad), y2 = 80 + 63 * Math.sin(rad);
            return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="rgba(196,120,32,.25)" stroke-width="1"/>`;
          }).join('')}
        </svg>
        <div style="position:absolute;bottom:0;left:50%;transform:translateX(-50%)">
          <div class="gauge-number" id="gauge-number">0</div>
          <div class="gauge-label">/ 100</div>
        </div>
      </div>
    </div>

    <!-- Key findings -->
    <div class="metric-row">
      <span class="metric-lbl">Lameness Detected</span>
      <span class="metric-val ${lamenessColor}">${r.lameness ? 'Yes' : 'No'}</span>
    </div>
    <div class="metric-row">
      <span class="metric-lbl">AAEP Lameness Grade</span>
      <span class="metric-val ${lamenessColor}">${gradeLabel}</span>
    </div>
    <div class="metric-row">
      <span class="metric-lbl">Stride Length</span>
      <span class="metric-val">${r.strideLen} m</span>
    </div>
    <div class="metric-row">
      <span class="metric-lbl">Stride Frequency</span>
      <span class="metric-val">${r.strideFreq} Hz</span>
    </div>
    <div class="metric-row">
      <span class="metric-lbl">Cadence</span>
      <span class="metric-val">${r.cadence} steps/min</span>
    </div>

    <!-- Limb assessment -->
    <div style="margin-top:1rem;margin-bottom:.35rem;font-size:.52rem;letter-spacing:.16em;text-transform:uppercase;color:var(--cream-faint)">Limb Assessment</div>
    <div class="limb-diagram">
      ${['LF','RF','LH','RH'].map(l => `
        <div class="limb-cell">
          <span class="limb-name">${l === 'LF' ? 'Left Fore' : l === 'RF' ? 'Right Fore' : l === 'LH' ? 'Left Hind' : 'Right Hind'}</span>
          <span class="limb-status ${r.limbs[l] === 'affected' ? 'aff' : 'ok'}">${r.limbs[l] === 'affected' ? 'Affected' : 'Normal'}</span>
        </div>
      `).join('')}
    </div>

    <!-- Confidence -->
    <div style="margin-top:1rem;margin-bottom:.35rem;font-size:.52rem;letter-spacing:.16em;text-transform:uppercase;color:var(--cream-faint)">Model Confidence</div>
    <div class="conf-strip">
      <div class="conf-bar-track">
        <div class="conf-bar-fill" id="conf-fill" style="width:0%"></div>
      </div>
      <div class="conf-pct" id="conf-pct">0%</div>
    </div>

    <!-- Model info -->
    <div style="margin-top:1rem;padding-top:.8rem;border-top:1px solid rgba(196,120,32,.08);display:flex;gap:1.2rem;flex-wrap:wrap">
      <div><div style="font-family:'Cormorant Garamond',serif;font-size:1rem;color:var(--amber-lit)">${VISION_MODELS[selectedModelIdx].accuracy}%</div><div style="font-size:.48rem;letter-spacing:.12em;text-transform:uppercase;color:var(--cream-faint)">Model Acc.</div></div>
      <div><div style="font-family:'Cormorant Garamond',serif;font-size:1rem;color:var(--amber-lit)">${VISION_MODELS[selectedModelIdx].keypoints}</div><div style="font-size:.48rem;letter-spacing:.12em;text-transform:uppercase;color:var(--cream-faint)">Keypoints</div></div>
      <div><div style="font-family:'Cormorant Garamond',serif;font-size:1rem;color:var(--amber-lit)">${VISION_MODELS[selectedModelIdx].architecture}</div><div style="font-size:.48rem;letter-spacing:.12em;text-transform:uppercase;color:var(--cream-faint)">Architecture</div></div>
    </div>
  `;

  // Animate gauge
  requestAnimationFrame(() => {
    const arc     = document.getElementById('gauge-fill');
    const numEl   = document.getElementById('gauge-number');
    const confFill = document.getElementById('conf-fill');
    const confPct  = document.getElementById('conf-pct');

    if (arc) {
      const totalLen = 201;
      const offset   = totalLen - (r.symmetry / 100) * totalLen;
      arc.style.strokeDashoffset = offset;
    }

    // Count up symmetry number
    animateCount(numEl, r.symmetry, 1300);

    // Confidence bar
    setTimeout(() => {
      if (confFill) confFill.style.width = r.conf + '%';
      animateCount(confPct, r.conf, 1000, '%');
    }, 200);
  });
}

function animateCount(el, target, duration, suffix = '') {
  if (!el) return;
  const start = performance.now();
  const from  = 0;

  function step(now) {
    const p  = Math.min((now - start) / duration, 1);
    const ep = 1 - Math.pow(1 - p, 3); // ease-out-cubic
    const v  = from + (target - from) * ep;
    el.textContent = Number.isInteger(target) ? Math.round(v) + suffix : v.toFixed(1) + suffix;
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function clearResults() {
  const container = document.getElementById('res-content');
  const empty     = document.getElementById('res-empty');
  const clearBtn  = document.getElementById('clear-btn');
  const analysisTime = document.getElementById('analysis-time');

  if (container) { container.innerHTML = ''; container.style.display = 'none'; }
  if (empty)     empty.style.display = '';
  if (clearBtn)  clearBtn.style.display = 'none';
  if (analysisTime) analysisTime.style.display = 'none';

  analysisResult = null;

  // Clear canvas
  const canvas = document.getElementById('overlay-canvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
  if (overlayInterval) { cancelAnimationFrame(overlayInterval); overlayInterval = null; }

  updateRunBtn();
}

function updateRunBtn() {
  const btn = document.getElementById('run-btn');
  if (!btn) return;
  btn.disabled = !uploadedFile;
}

// ── Utilities ─────────────────────────────────────────────
function formatSize(bytes) {
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ── Init ──────────────────────────────────────────────────
function initPage() {
  renderModelSelector();
  initDropZone();

  // Set badge for default model
  const badge = document.getElementById('selected-model-badge');
  if (badge) { badge.textContent = VISION_MODELS[0].name; badge.style.display = ''; }
}
