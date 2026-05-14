// Model Testing Logic

let selectedTestedModel = null;
let uploadedFile = null;

function parseModelResponse(text) {
  const bMatch = text.match(/Behavior:\s*([^\n.]+[^\n]*?)(?:\.\s*Confidence|$)/i)
                 || text.match(/Behavior:\s*([^\n]+)/i);
  const cMatch = text.match(/Confidence:\s*(\d+)/i);
  const eMatch = text.match(/Evidence:\s*([^\n]+)/i);
  return {
    behavior: bMatch ? bMatch[1].trim().replace(/\.$/, '') : 'Unknown',
    confidence: cMatch ? parseInt(cMatch[1]) : null,
    evidence: eMatch ? eMatch[1].trim().replace(/\.$/, '') : text.trim()
  };
}

function behaviorColor(b) {
  const s = b.toLowerCase();
  if (s.includes('eating') || s.includes('drinking')) return '#4ade80';
  if (s.includes('walking')) return '#a78bfa';
  if (s.includes('trotting') || s.includes('running')) return '#f97316';
  if (s.includes('standing')) return '#60a5fa';
  if (s.includes('lying')) return '#94a3b8';
  if (s.includes('rearing') || s.includes('kicking')) return '#ef4444';
  if (s.includes('grooming')) return '#e879f9';
  if (s.includes('head shaking')) return '#facc15';
  return '#9ca3af';
}

function renderBehaviorTable(rows, meta) {
  const headerHtml = `
    <div style="margin-bottom:1.2rem;padding-bottom:0.9rem;border-bottom:1px solid rgba(196,120,32,0.12);">
      <div style="font-size:0.75rem;letter-spacing:0.14em;text-transform:uppercase;color:var(--amber-lit);margin-bottom:0.3rem;font-weight:500;">${meta.modelName}</div>
      <div style="font-size:0.85rem;color:var(--cream-dim);">${meta.framesExtracted} frames extracted &middot; ${meta.framesAnalyzed} analyzed${meta.duration ? ' &middot; ' + meta.duration + 's duration' : ''}</div>
    </div>`;

  const trs = rows.map((r, idx) => {
    const thumbCell = r.image_base64
      ? `<td style="padding:0.6rem 1rem 0.6rem 0;"><img src="data:image/jpeg;base64,${r.image_base64}" style="width:160px;height:100px;object-fit:cover;border-radius:6px;border:1px solid rgba(196,120,32,0.18);display:block;" /></td>`
      : `<td style="padding:0.6rem 1rem 0.6rem 0;"><div style="width:160px;height:100px;border-radius:6px;border:1px solid rgba(255,255,255,0.06);background:rgba(255,255,255,0.03);display:flex;align-items:center;justify-content:center;font-size:0.7rem;color:var(--cream-faint);">no frame</div></td>`;

    if (r.error) {
      return `<tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
        ${thumbCell}
        <td style="padding:0.6rem 1rem;color:var(--cream-dim);font-size:0.85rem;">${idx + 1}</td>
        <td style="padding:0.6rem 1rem;color:var(--cream-dim);font-size:0.85rem;white-space:nowrap;">${r.timestamp}s</td>
        <td colspan="3" style="padding:0.6rem 0;color:#ef4444;font-size:0.85rem;">Error: ${r.error}</td>
      </tr>`;
    }
    const col = behaviorColor(r.behavior);
    const conf = r.confidence !== null ? r.confidence : null;
    const confBar = conf !== null
      ? `<div style="background:rgba(255,255,255,0.06);border-radius:2px;height:4px;margin-top:6px;width:100%;"><div style="background:${col};width:${conf}%;height:100%;border-radius:2px;"></div></div>`
      : '';
    return `<tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
      ${thumbCell}
      <td style="padding:0.6rem 1rem;color:var(--cream-dim);font-size:0.85rem;">${idx + 1}</td>
      <td style="padding:0.6rem 1rem;color:var(--cream-dim);font-size:0.85rem;white-space:nowrap;">${r.timestamp}s</td>
      <td style="padding:0.6rem 1rem;">
        <span style="background:${col}1a;color:${col};border:1px solid ${col}44;border-radius:5px;padding:4px 12px;font-size:0.78rem;letter-spacing:0.04em;white-space:nowrap;font-weight:500;">${r.behavior}</span>
      </td>
      <td style="padding:0.6rem 1rem;min-width:100px;">
        <div style="font-size:0.85rem;color:var(--cream);font-weight:500;">${conf !== null ? conf + '%' : '—'}</div>
        ${confBar}
      </td>
      <td style="padding:0.6rem 0;font-size:0.82rem;color:var(--cream-dim);line-height:1.6;max-width:320px;">${r.evidence}</td>
    </tr>`;
  }).join('');

  return headerHtml + `
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;font-family:'Jost',sans-serif;">
      <thead>
        <tr style="border-bottom:1px solid rgba(196,120,32,0.25);">
          <th style="text-align:left;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--cream-dim);font-weight:500;padding:0 1rem 0.7rem 0;">Snapshot</th>
          <th style="text-align:left;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--cream-dim);font-weight:500;padding:0 1rem 0.7rem;">#</th>
          <th style="text-align:left;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--cream-dim);font-weight:500;padding:0 1rem 0.7rem;">Time</th>
          <th style="text-align:left;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--cream-dim);font-weight:500;padding:0 1rem 0.7rem;">Behavior</th>
          <th style="text-align:left;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--cream-dim);font-weight:500;padding:0 1rem 0.7rem;">Confidence</th>
          <th style="text-align:left;font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--cream-dim);font-weight:500;padding:0 0 0.7rem;">Evidence</th>
        </tr>
      </thead>
      <tbody>${trs}</tbody>
    </table>
    </div>`;
}

function getFrameSettings() {
  const extractToggle = document.getElementById('extract-all-frames');
  const extractEnabled = extractToggle ? extractToggle.checked : true;
  return {
    frame_interval: parseFloat(document.getElementById('frame-skip-ratio')?.value) || 1.0,
    max_frames: parseInt(document.getElementById('max-frames-limit')?.value) || 25,
    resolution: document.getElementById('frame-resolution')?.value || '640x480',
    quality: parseInt(document.getElementById('frame-quality')?.value) || 80,
    start_time: parseFloat(document.getElementById('frame-start-time')?.value) || 0.0,
    end_time: parseFloat(document.getElementById('frame-end-time')?.value) || 0.0,
    analysis_mode: document.getElementById('analysis-mode')?.value || 'aggregate',
    extract_enabled: extractEnabled,
  };
}

window.openModelTesting = function(cardEl, name, category, version, id) {
  selectedTestedModel = { name, category, version, id };
  
  const th = document.getElementById('testing-header');
  if(th) th.style.display = 'block';
  
  const tm = document.getElementById('tested-model-name');
  if(tm) tm.innerText = name;
  
  const tmeta = document.getElementById('tested-model-meta');
  if(tmeta) tmeta.innerHTML = category + ' &middot; ' + version;
  
  const badge = document.getElementById('selected-model-badge');
  if(badge) {
    badge.style.display = 'inline-flex';
    badge.textContent = name;
  }
  
  const pt = document.getElementById('pt-testing');
  if(pt) pt.style.display = 'block';
  
  if (typeof switchAITab === 'function') switchAITab('vision');
  
  setTimeout(() => {
     const p = document.getElementById('model-prompt');
     if(p) p.focus();
  }, 100);
}

function initVisionTestingPage() {
  window.initDropZone();
  
  const p = document.getElementById('model-prompt');
  if(p) {
    p.addEventListener('focus', e => { 
      e.target.style.borderColor = 'rgba(196,120,32,0.4)'; 
      e.target.style.boxShadow = 'inset 0 1px 0 rgba(255,255,255,0.05), 0 0 15px rgba(196,120,32,0.1)'; 
    });
    p.addEventListener('blur', e => { 
      e.target.style.borderColor = 'rgba(196,120,32,.15)'; 
      e.target.style.boxShadow = 'inset 0 1px 0 rgba(255,255,255,0.02)'; 
    });
  }
}
window.initVisionTestingPage = initVisionTestingPage;

window.initDropZone = function() {
  const zone = document.getElementById('drop-zone');
  if (!zone) return;

  ['dragover', 'dragleave', 'drop'].forEach(evt => {
    zone.addEventListener(evt, e => e.preventDefault());
  });

  zone.addEventListener('dragover', () => zone.classList.add('drag-over'));
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    zone.classList.remove('drag-over');
    if (e.dataTransfer.files[0]) window.loadVideo(e.dataTransfer.files[0]);
  });

  const input = document.getElementById('file-input');
  if (input) {
    const newInp = input.cloneNode(true);
    input.parentNode.replaceChild(newInp, input);
    newInp.addEventListener('change', e => {
      if (e.target.files[0]) window.loadVideo(e.target.files[0]);
    });
  }
}

window.loadVideo = function(file) {
  uploadedFile = file;
  const url = URL.createObjectURL(file);
  document.getElementById('video-el').src = url;
  document.getElementById('video-el').play();

  document.getElementById('vi-name').textContent = file.name;
  document.getElementById('vi-meta').textContent = (file.size / (1024*1024)).toFixed(2) + ' MB';

  document.getElementById('video-preview').style.display = 'block';
  document.getElementById('dz-idle').style.display = 'none';
  document.getElementById('drop-zone').classList.add('has-video');

  const panel = document.getElementById('results-panel');
  if (panel) panel.style.display = 'flex';

  document.getElementById('run-btn').disabled = false;
  window.clearResults();
}

window.removeVideo = function() {
  uploadedFile = null;
  const video = document.getElementById('video-el');
  if (video.src) URL.revokeObjectURL(video.src);
  video.src = '';

  document.getElementById('video-preview').style.display = 'none';
  document.getElementById('dz-idle').style.display = '';
  document.getElementById('drop-zone').classList.remove('has-video');

  const panel = document.getElementById('results-panel');
  if (panel) panel.style.display = 'none';

  document.getElementById('file-input').value = '';
  document.getElementById('run-btn').disabled = true;
  window.clearResults();
}

window.clearResults = function() {
  const resEmpty = document.getElementById('res-empty');
  const resContent = document.getElementById('res-content');
  if(resEmpty) resEmpty.style.display = 'block';
  if(resContent) {
    resContent.style.display = 'none';
    resContent.innerHTML = '';
  }
  const clearBtn = document.getElementById('clear-btn');
  if(clearBtn) clearBtn.style.display = 'none';
  
  const analysisTime = document.getElementById('analysis-time');
  if(analysisTime) analysisTime.style.display = 'none';
  
  const pbWrap = document.getElementById('progress-bar-wrap');
  if(pbWrap) pbWrap.style.display = 'none';
  
  const pStat = document.getElementById('progress-status');
  if(pStat) pStat.style.display = 'none';
}

window.runAnalysis = async function() {
  if (!uploadedFile) return;

  const btn = document.getElementById('run-btn');
  btn.disabled = true;
  
  const pbWrap = document.getElementById('progress-bar-wrap');
  const pStat = document.getElementById('progress-status');
  const fill = document.getElementById('progress-bar-fill');
  
  if(pbWrap) pbWrap.style.display = 'block';
  if(pStat) pStat.style.display = 'block';
  
  fill.style.width = '0%';
  
  const modelName = selectedTestedModel ? selectedTestedModel.name : 'Unknown';
  const ollamaModelId = selectedTestedModel ? (selectedTestedModel.id || 'moondream:latest') : 'moondream:latest';
  const isVisionModel = selectedTestedModel && (selectedTestedModel.category === 'Vision Model');

  if (!isVisionModel) {
    fill.style.width = '100%';
    pStat.innerText = 'Model not supported for visual analysis';
    setTimeout(() => {
      if(pbWrap) pbWrap.style.display = 'none';
      if(pStat) pStat.style.display = 'none';
    }, 400);
    document.getElementById('res-empty').style.display = 'none';
    const resContent = document.getElementById('res-content');
    resContent.style.whiteSpace = 'normal';
    resContent.style.display = 'block';
    const clearBtn = document.getElementById('clear-btn');
    if(clearBtn) clearBtn.style.display = 'inline-block';
    btn.disabled = false;
    resContent.innerHTML = '<span style="color:#ef4444;font-size:0.75rem;">This model does not support image/video input. Please select a Vision Model (e.g., MOONDREAM, QWEN3-VL, QWEN2.5VL) to analyze visual content.</span>';
    return;
  }

  const settings = getFrameSettings();
  const promptInput = document.getElementById('model-prompt');
  const promptValue = promptInput ? (promptInput.value || 'Analyze the horse\'s behavior in this frame. Classify into ONE of: Standing, Walking, Trotting/Running, Eating/Drinking, Lying Down, Rearing, Kicking, Grooming, Head Shaking, or Unknown. Output format — Behavior: [label]. Confidence: [0-100]%. Evidence: [1 sentence].') : 'Analyze this image.';

  const useServerExtraction = settings.extract_enabled && settings.analysis_mode !== 'single';

  if (settings.analysis_mode === 'single' || !settings.extract_enabled) {
    // Single-frame mode: capture one frame client-side and send to /api/analyze
    pStat.innerText = 'Capturing single frame...';
    fill.style.width = '15%';

    const video = document.getElementById('video-el');
    let base64Image = "";
    if (video && video.videoWidth > 0) {
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/jpeg', settings.quality / 100);
      base64Image = dataUrl.split(',')[1];
    }

    pStat.innerText = 'Running single-frame inference...';
    fill.style.width = '50%';

    let rawResponse = "";
    let analysisError = null;
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: ollamaModelId,
          prompt: promptValue,
          image: base64Image || undefined
        })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || err.error || "Analysis failed");
      }
      const data = await res.json();
      rawResponse = data.response || "No response generated.";
    } catch (err) {
      console.error("Analysis Error:", err);
      analysisError = err.message;
    }

    fill.style.width = '100%';
    pStat.innerText = 'Done.';
    setTimeout(() => {
      if(pbWrap) pbWrap.style.display = 'none';
      if(pStat) pStat.style.display = 'none';
    }, 400);

    document.getElementById('res-empty').style.display = 'none';
    const resContent = document.getElementById('res-content');
    resContent.style.cssText = resContent.style.cssText + '; white-space: normal;';
    resContent.style.display = 'block';
    const clearBtn = document.getElementById('clear-btn');
    if(clearBtn) clearBtn.style.display = 'inline-block';
    btn.disabled = false;

    if (analysisError) {
      resContent.innerHTML = `<span style="color:#ef4444;font-size:0.75rem;">Error: ${analysisError}</span>`;
    } else {
      const parsed = parseModelResponse(rawResponse);
      const rows = [{ timestamp: '0.0', image_base64: base64Image || null, behavior: parsed.behavior, confidence: parsed.confidence, evidence: parsed.evidence }];
      resContent.innerHTML = renderBehaviorTable(rows, {
        modelName: modelName + ' — Single Frame',
        framesExtracted: 1,
        framesAnalyzed: 1,
        duration: null
      });
    }
    return;
  }

  // Multi-frame mode: upload video + settings to /api/analyze-video
  pStat.innerText = 'Uploading video...';
  fill.style.width = '10%';

  const formData = new FormData();
  formData.append('file', uploadedFile);
  formData.append('model', ollamaModelId);
  formData.append('prompt', promptValue);
  formData.append('frame_interval', settings.frame_interval);
  formData.append('max_frames', settings.max_frames);
  formData.append('resolution', settings.resolution);
  formData.append('quality', settings.quality);
  formData.append('start_time', settings.start_time);
  formData.append('end_time', settings.end_time);
  formData.append('analysis_mode', settings.analysis_mode);

  pStat.innerText = 'Extracting frames & running inference...';
  fill.style.width = '30%';

  // Simulate progress while waiting
  let progressSim = setInterval(() => {
    let current = parseFloat(fill.style.width) || 30;
    if (current < 85) {
      fill.style.width = (current + 0.5) + '%';
    }
  }, 500);

  let resultHTML = "";
  try {
    const res = await fetch("/api/analyze-video", {
      method: "POST",
      body: formData
    });

    clearInterval(progressSim);

    if (!res.ok) {
      let detail = res.statusText;
      try { const j = await res.json(); detail = j.detail || j.error || detail; } catch(_) {}
      throw new Error(detail);
    }

    const data = await res.json();
    fill.style.width = '100%';
    pStat.innerText = 'Done.';

    if (data.mode === 'per_frame') {
      const rows = data.results.map(r => {
        if (r.error) return { timestamp: r.timestamp, image_base64: r.image_base64 || null, error: r.error };
        const parsed = parseModelResponse(r.response || '');
        return { timestamp: r.timestamp, image_base64: r.image_base64 || null, behavior: parsed.behavior, confidence: parsed.confidence, evidence: parsed.evidence };
      });
      resultHTML = renderBehaviorTable(rows, {
        modelName,
        framesExtracted: data.frames_sent,
        framesAnalyzed: data.successful_frames,
        duration: (data.video_info || {}).duration
      });
    } else {
      const vi = data.video_info || {};
      const raw = (data.response || '').trim();
      const parsed = parseModelResponse(raw);
      const rows = [{ timestamp: '—', image_base64: data.first_frame_image || null, behavior: parsed.behavior, confidence: parsed.confidence, evidence: parsed.evidence }];
      resultHTML = renderBehaviorTable(rows, {
        modelName,
        framesExtracted: data.frames_sent || '?',
        framesAnalyzed: data.successful_frames !== undefined ? data.successful_frames : '?',
        duration: vi.duration
      });
    }

  } catch (err) {
    clearInterval(progressSim);
    console.error("Analysis Error:", err);
    resultHTML = `<span style="color:#ef4444;font-size:0.75rem;">Error: ${err.message}</span>`;
    fill.style.width = '100%';
    pStat.innerText = 'Failed.';
  }

  setTimeout(() => {
    if(pbWrap) pbWrap.style.display = 'none';
    if(pStat) pStat.style.display = 'none';
  }, 600);

  document.getElementById('res-empty').style.display = 'none';
  const resContent = document.getElementById('res-content');
  resContent.style.whiteSpace = 'normal';
  resContent.style.display = 'block';
  const clearBtn = document.getElementById('clear-btn');
  if(clearBtn) clearBtn.style.display = 'inline-block';
  btn.disabled = false;

  resContent.innerHTML = resultHTML;
}

if(document.readyState === 'complete') {
  initVisionTestingPage();
} else {
  window.addEventListener('load', initVisionTestingPage);
}