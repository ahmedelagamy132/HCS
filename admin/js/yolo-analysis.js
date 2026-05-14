let selectedFile = null;

document.addEventListener('DOMContentLoaded', () => {
    loadModelHealth();

    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');

    fileInput.addEventListener('change', e => {
        if (e.target.files[0]) setFile(e.target.files[0]);
    });

    dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
    });
});

function setFile(file) {
    selectedFile = file;
    document.getElementById('dz-idle').style.display = 'none';
    document.getElementById('dz-selected').style.display = 'flex';
    document.getElementById('dz-filename').textContent = file.name;
    document.getElementById('dz-filesize').textContent = (file.size / 1024 / 1024).toFixed(2) + ' MB';
    document.getElementById('drop-zone').classList.add('has-file');
    document.getElementById('run-btn').disabled = false;
}

function removeFile(e) {
    e.stopPropagation();
    selectedFile = null;
    document.getElementById('dz-idle').style.display = 'flex';
    document.getElementById('dz-selected').style.display = 'none';
    document.getElementById('drop-zone').classList.remove('has-file');
    document.getElementById('run-btn').disabled = true;
    document.getElementById('file-input').value = '';
    document.getElementById('results-section').style.display = 'none';
}

async function runDetection() {
    if (!selectedFile) return;

    const runBtn = document.getElementById('run-btn');
    const progressWrap = document.getElementById('progress-wrap');
    const progressFill = document.getElementById('progress-fill');
    const progressStatus = document.getElementById('progress-status');
    const resultsSection = document.getElementById('results-section');

    runBtn.disabled = true;
    runBtn.textContent = 'Processing...';
    resultsSection.style.display = 'none';
    progressWrap.style.display = 'block';
    progressStatus.style.display = 'block';
    progressStatus.textContent = 'Uploading video...';

    let progress = 0;
    const progressTimer = setInterval(() => {
        progress = Math.min(progress + Math.random() * 8, 88);
        progressFill.style.width = progress + '%';
    }, 600);

    try {
        const formData = new FormData();
        formData.append('video', selectedFile);
        formData.append('confidence_threshold', document.getElementById('param-conf').value);
        formData.append('iou_threshold', document.getElementById('param-iou').value);
        formData.append('line_thickness', document.getElementById('param-thickness').value);
        formData.append('show_labels', document.getElementById('param-labels').checked);
        formData.append('show_conf', document.getElementById('param-conf-show').checked);

        progressStatus.textContent = 'Running YOLOv8 detection...';

        const res = await fetch('/api/yolo/detect', { method: 'POST', body: formData });

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }

        const data = await res.json();

        clearInterval(progressTimer);
        progressFill.style.width = '100%';
        progressStatus.textContent = 'Detection complete!';

        setTimeout(() => {
            progressWrap.style.display = 'none';
            progressStatus.style.display = 'none';
            showResults(data);
        }, 600);

    } catch (err) {
        clearInterval(progressTimer);
        progressWrap.style.display = 'none';
        progressStatus.style.display = 'block';
        progressStatus.textContent = 'Error: ' + err.message;
        progressStatus.style.color = 'var(--danger)';
    } finally {
        runBtn.disabled = false;
        runBtn.textContent = 'Run Detection';
    }
}

function showResults(data) {
    const resultsSection = document.getElementById('results-section');
    resultsSection.style.display = 'block';

    document.getElementById('stat-frames').textContent = data.total_frames_processed ?? '—';
    document.getElementById('stat-detections').textContent = data.total_detections ?? '—';

    const rate = data.total_frames_processed
        ? ((data.frames_with_detections / data.total_frames_processed) * 100).toFixed(1) + '%'
        : '—';
    document.getElementById('stat-rate').textContent = rate;
    document.getElementById('stat-time').textContent = data.processing_time
        ? data.processing_time.toFixed(1) + 's'
        : '—';

    if (data.download_url) {
        const link = document.getElementById('download-link');
        link.href = data.download_url;
        link.download = data.output_video_name || 'detection_output.mp4';
        document.getElementById('download-filename').textContent = data.output_video_name || '';
        document.getElementById('download-panel').style.display = 'block';
    }
}

async function loadModelHealth() {
    const statusEl = document.getElementById('model-status');
    const infoPanel = document.getElementById('model-info-panel');
    const infoContent = document.getElementById('model-info-content');

    try {
        const res = await fetch('/api/yolo/health');
        const data = await res.json();

        if (statusEl) {
            statusEl.textContent = data.status === 'healthy' ? 'YOLOv8 Ready' : 'Model Not Loaded';
            statusEl.style.color = data.status === 'healthy' ? 'var(--green)' : 'var(--amber-lit)';
        }

        if (infoPanel && infoContent) {
            infoPanel.style.display = 'block';
            infoContent.innerHTML =
                `<div style="display:flex;justify-content:space-between;border-bottom:1px solid rgba(196,120,32,.05);padding:.4rem 0;"><span>Status</span><span style="color:${data.status === 'healthy' ? 'var(--green)' : 'var(--amber-lit)'}">${data.status}</span></div>` +
                `<div style="display:flex;justify-content:space-between;border-bottom:1px solid rgba(196,120,32,.05);padding:.4rem 0;"><span>Model</span><span style="color:var(--amber-lit);font-family:'Cormorant Garamond',serif;font-size:.85rem;">YOLOv8</span></div>` +
                `<div style="display:flex;justify-content:space-between;padding:.4rem 0;"><span>Ultralytics</span><span style="color:${data.ultralytics_available ? 'var(--green)' : 'var(--danger)'}">${data.ultralytics_available ? 'Available' : 'Missing'}</span></div>`;
        }
    } catch {
        if (statusEl) statusEl.textContent = 'Service Unavailable';
    }
}
