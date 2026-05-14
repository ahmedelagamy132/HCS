document.addEventListener("DOMContentLoaded", async () => {

  // ── Horse info ─────────────────────────────────────────────────────────────
  const urlParams = new URLSearchParams(window.location.search);
  const horseId = urlParams.get('id');

  if (horseId) {
    try {
      const res = await fetch("/api/horses");
      if (res.ok) {
        const horses = await res.json();
        const horse = horses.find(h => String(h.id) === String(horseId));
        if (horse) {
          document.getElementById("horse-id-display").innerText =
            horse.horse_code || ('HR-' + String(horse.id).substring(0, 4).toUpperCase());
          document.getElementById("horse-name-display").innerHTML =
            `${horse.name || 'Unnamed'} <em>Live</em>`;
          document.getElementById("inf-breed").innerText   = horse.breed        || 'Unknown';
          document.getElementById("inf-age").innerText     = horse.age_years != null ? horse.age_years + ' yrs' : '-';
          document.getElementById("inf-stable").innerText  = horse.stable_name  || 'Unassigned';
          document.getElementById("inf-owner").innerText   = horse.owner_name   || 'N/A';
          document.getElementById("inf-health").innerText  = horse.health_status || 'Unknown';
        }
      }
    } catch (e) {
      console.error("Horse fetch error:", e);
    }
  }

  // ── Populate VLM model dropdown ────────────────────────────────────────────
  const modelSelect = document.getElementById("vlm-model");
  try {
    const res = await fetch("/api/models");
    if (res.ok) {
      const models = await res.json();
      const visionModels = models.filter(m =>
        m.category === "Vision Model" && m.id !== "dlc-gait-pose"
      );
      modelSelect.innerHTML = "";
      if (visionModels.length === 0) {
        modelSelect.innerHTML = '<option value="">No vision models found</option>';
      } else {
        visionModels.forEach(m => {
          const opt = document.createElement("option");
          opt.value = m.id;
          opt.textContent = `${m.name} (${m.version})`;
          modelSelect.appendChild(opt);
        });
      }
    }
  } catch (e) {
    modelSelect.innerHTML = '<option value="">Cannot reach server</option>';
  }

  // ── Quality slider label ────────────────────────────────────────────────────
  const qualitySlider = document.getElementById("vlm-quality");
  const qualityVal    = document.getElementById("quality-val");
  qualitySlider.addEventListener("input", () => {
    qualityVal.textContent = qualitySlider.value;
  });

  // ── State ──────────────────────────────────────────────────────────────────
  let ws               = null;
  let canvas           = document.getElementById("stream-canvas");
  let ctx              = canvas.getContext("2d");
  let frameCount       = 0;
  let isConnected      = false;
  let isAnalyzing      = false;
  let pendingAnalysis  = false;
  let lastAnalysisTime = 0;
  let rowCounter       = 0;
  let logCount         = 0;

  // ── DOM refs ───────────────────────────────────────────────────────────────
  const connectBtn  = document.getElementById("connect-btn");
  const streamSys   = document.getElementById("stream-sys");
  const vSpinner    = document.getElementById("v-spinner");
  const vText       = document.getElementById("v-text");
  const statusLbl   = document.getElementById("conn-status-lbl");
  const videoLoading = document.getElementById("video-loading");
  const analysisBtn = document.getElementById("analysis-btn");
  const logTbody    = document.getElementById("log-tbody");
  const logTable    = document.getElementById("log-table");
  const logEmpty    = document.getElementById("log-empty");
  const logCountEl  = document.getElementById("log-count");
  const logWrap     = document.getElementById("log-table-wrap");
  const clearBtn    = document.getElementById("btn-clear-log");

  // ── Connect / disconnect ───────────────────────────────────────────────────
  connectBtn.addEventListener("click", () => {
    if (!isConnected) {
      startStream();
    } else {
      stopStream();
    }
  });

  function startStream() {
    const rtspUrl = document.getElementById("rtsp-url").value.trim();
    if (!rtspUrl) return;

    vSpinner.style.display = "block";
    vText.innerText = "Buffering Stream…";
    connectBtn.innerText = "Connecting…";
    connectBtn.disabled = true;

    const wsProto = location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(`${wsProto}//${location.host}/ws/stream?url=${encodeURIComponent(rtspUrl)}`);
    ws.binaryType = "blob";

    ws.onopen = () => {
      isConnected = true;
      connectBtn.disabled = false;
      connectBtn.innerText = "Disconnect Stream";
      connectBtn.style.background = "var(--danger)";
      streamSys.classList.remove("disconnected");
      statusLbl.innerText = "Live — 15 FPS";
      videoLoading.style.display = "none";
      canvas.style.display = "block";
      analysisBtn.disabled = false;
      frameCount = 0;
    };

    ws.onmessage = (e) => {
      if (!(e.data instanceof Blob)) return;
      const blobUrl = URL.createObjectURL(e.data);
      const img = new Image();
      img.onload = () => {
        if (canvas.width !== img.naturalWidth || canvas.height !== img.naturalHeight) {
          canvas.width  = img.naturalWidth  || 640;
          canvas.height = img.naturalHeight || 480;
        }
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(blobUrl);
        frameCount++;
        maybeSendToVLM();
      };
      img.onerror = () => URL.revokeObjectURL(blobUrl);
      img.src = blobUrl;
    };

    ws.onclose = () => onDisconnected();
    ws.onerror = () => onDisconnected();
  }

  function stopStream() {
    if (ws) {
      ws.close();
      ws = null;
    }
    onDisconnected();
  }

  function onDisconnected() {
    isConnected = false;
    isAnalyzing = false;
    connectBtn.disabled = false;
    connectBtn.innerText = "Connect Stream";
    connectBtn.style.background = "";
    streamSys.classList.add("disconnected");
    statusLbl.innerText = "Disconnected";
    canvas.style.display = "none";
    videoLoading.style.display = "flex";
    vSpinner.style.display = "none";
    vText.innerText = "Awaiting Source";
    analysisBtn.disabled = true;
    analysisBtn.classList.remove("active");
    analysisBtn.innerText = "Start Analysis";
  }

  // ── Analysis toggle ────────────────────────────────────────────────────────
  analysisBtn.addEventListener("click", () => {
    if (!isAnalyzing) {
      isAnalyzing = true;
      lastAnalysisTime = 0;
      analysisBtn.classList.add("active");
      analysisBtn.innerText = "Stop Analysis";
    } else {
      isAnalyzing = false;
      analysisBtn.classList.remove("active");
      analysisBtn.innerText = "Start Analysis";
    }
  });

  // ── Frame sampling ─────────────────────────────────────────────────────────
  function maybeSendToVLM() {
    if (!isAnalyzing || pendingAnalysis) return;
    const intervalSec = parseFloat(document.getElementById("vlm-interval").value) || 5;
    const now = Date.now();
    if (now - lastAnalysisTime < intervalSec * 1000) return;
    lastAnalysisTime = now;
    sendFrameToVLM();
  }

  // ── VLM frame analysis ─────────────────────────────────────────────────────
  async function sendFrameToVLM() {
    if (pendingAnalysis || canvas.width === 0) return;
    pendingAnalysis = true;

    const model     = document.getElementById("vlm-model").value;
    const prompt    = document.getElementById("vlm-prompt").value.trim();
    const quality   = parseInt(qualitySlider.value, 10) / 100;
    const resolution = document.getElementById("vlm-resolution").value;
    const [rw, rh]  = resolution.split("x").map(Number);

    if (!model) {
      pendingAnalysis = false;
      return;
    }

    // Resize frame to target resolution
    const offscreen = document.createElement("canvas");
    offscreen.width  = rw;
    offscreen.height = rh;
    const offCtx = offscreen.getContext("2d");
    offCtx.drawImage(canvas, 0, 0, rw, rh);
    const base64 = offscreen.toDataURL("image/jpeg", quality).split(",")[1];

    const now = new Date();
    const ts  = now.toTimeString().substring(0, 8);
    const snapshotDataUrl = `data:image/jpeg;base64,${base64}`;
    const rowId = addPendingRow(ts, frameCount, snapshotDataUrl);

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model, prompt, image: base64 }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        updateRow(rowId, err.detail || `HTTP ${res.status}`, "error");
      } else {
        const data = await res.json();
        updateRow(rowId, data.response || "(no response)", "done");
      }
    } catch (e) {
      updateRow(rowId, "Network error: " + e.message, "error");
    } finally {
      pendingAnalysis = false;
    }
  }

  // ── Table helpers ──────────────────────────────────────────────────────────
  function addPendingRow(timestamp, frame, snapshotUrl) {
    const id = ++rowCounter;
    logCount++;
    updateLogCount();

    logEmpty.style.display = "none";
    logTable.style.display = "table";

    const snapCell = snapshotUrl
      ? `<img src="${snapshotUrl}" alt="frame ${frame}" onclick="window.open('${snapshotUrl}','_blank')">`
      : `<div class="snap-empty">N/A</div>`;

    const tr = document.createElement("tr");
    tr.id = `row-${id}`;
    tr.innerHTML = `
      <td class="ts">${timestamp}</td>
      <td class="frm">${frame}</td>
      <td class="snap">${snapCell}</td>
      <td class="behavior" id="beh-${id}" style="color:var(--cream-faint);font-style:italic;">Analyzing…</td>
      <td id="sts-${id}">
        <span class="status-pill pending">
          <span class="status-dot-s"></span>Pending
        </span>
      </td>`;
    logTbody.appendChild(tr);
    logWrap.scrollTop = logWrap.scrollHeight;
    return id;
  }

  function updateRow(id, text, status) {
    const behCell = document.getElementById(`beh-${id}`);
    const stsCell = document.getElementById(`sts-${id}`);
    if (!behCell || !stsCell) return;

    behCell.style.color = "";
    behCell.style.fontStyle = "";
    behCell.textContent = text;

    if (status === "done") {
      stsCell.innerHTML = `<span class="status-pill done"><span class="status-dot-s"></span>Done</span>`;
    } else {
      stsCell.innerHTML = `<span class="status-pill error"><span class="status-dot-s"></span>Error</span>`;
    }
    logWrap.scrollTop = logWrap.scrollHeight;
  }

  function updateLogCount() {
    logCountEl.textContent = `${logCount} ${logCount === 1 ? 'entry' : 'entries'}`;
  }

  clearBtn.addEventListener("click", () => {
    logTbody.innerHTML = "";
    logCount = 0;
    updateLogCount();
    logTable.style.display = "none";
    logEmpty.style.display = "block";
  });

});
