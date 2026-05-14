let selectedFile = null;
let currentMode = 'image';

document.addEventListener('DOMContentLoaded', () => {
    loadHealth();

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

function switchMode(mode) {
    currentMode = mode;
    removeFile({ stopPropagation: () => {} });

    document.getElementById('tab-image').classList.toggle('active', mode === 'image');
    document.getElementById('tab-video').classList.toggle('active', mode === 'video');
    document.getElementById('frame-interval-row').style.display = mode === 'video' ? 'flex' : 'none';
    document.getElementById('upload-title').textContent = mode === 'image' ? 'Upload Image' : 'Upload Video';
    document.getElementById('dz-label-text').textContent = mode === 'image'
        ? 'Drop image here or click to browse'
        : 'Drop video here or click to browse';
    document.getElementById('dz-hint-text').textContent = mode === 'image'
        ? 'JPG, PNG, BMP'
        : 'MP4, AVI, MOV, MKV';

    const fileInput = document.getElementById('file-input');
    fileInput.accept = mode === 'image'
        ? 'image/jpeg,image/png,image/bmp,.jpg,.jpeg,.png,.bmp'
        : 'video/mp4,video/avi,video/quicktime,video/x-matroska,.mkv';

    document.getElementById('result-image').style.display = 'none';
    document.getElementById('result-video').style.display = 'none';
}

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
    if (e && e.stopPropagation) e.stopPropagation();
    selectedFile = null;
    document.getElementById('dz-idle').style.display = 'flex';
    document.getElementById('dz-selected').style.display = 'none';
    document.getElementById('drop-zone').classList.remove('has-file');
    document.getElementById('run-btn').disabled = true;
    const fi = document.getElementById('file-input');
    if (fi) fi.value = '';
    document.getElementById('result-image').style.display = 'none';
    document.getElementById('result-video').style.display = 'none';
}

async function runClassification() {
    if (!selectedFile) return;

    const runBtn = document.getElementById('run-btn');
    const progressWrap = document.getElementById('progress-wrap');
    const progressFill = document.getElementById('progress-fill');
    const progressStatus = document.getElementById('progress-status');

    runBtn.disabled = true;
    runBtn.textContent = 'Processing...';
    progressWrap.style.display = 'block';
    progressStatus.style.display = 'block';
    progressStatus.style.color = 'var(--amber-lit)';
    progressStatus.textContent = 'Uploading file...';
    document.getElementById('result-image').style.display = 'none';
    document.getElementById('result-video').style.display = 'none';

    let progress = 0;
    const progressTimer = setInterval(() => {
        progress = Math.min(progress + Math.random() * 5, 85);
        progressFill.style.width = progress + '%';
    }, 800);

    try {
        const model = document.getElementById('param-model').value;
        const resize = document.getElementById('param-resize').value;
        const formData = new FormData();
        formData.append('model_name', model);
        if (resize) formData.append('resize', resize);

        let endpoint;
        if (currentMode === 'image') {
            formData.append('image', selectedFile);
            endpoint = '/api/vlm/classify-image';
            progressStatus.textContent = 'Classifying image with VLM...';
        } else {
            const interval = document.getElementById('param-interval').value;
            formData.append('video', selectedFile);
            formData.append('frame_interval', interval);
            endpoint = '/api/vlm/classify-video';
            progressStatus.textContent = 'Classifying video frames with VLM...';
        }

        const res = await fetch(endpoint, { method: 'POST', body: formData });

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }

        const data = await res.json();

        clearInterval(progressTimer);
        progressFill.style.width = '100%';
        progressStatus.textContent = 'Classification complete!';

        setTimeout(() => {
            progressWrap.style.display = 'none';
            progressStatus.style.display = 'none';
            if (currentMode === 'image') showImageResult(data);
            else showVideoResult(data);
        }, 500);

    } catch (err) {
        clearInterval(progressTimer);
        progressWrap.style.display = 'none';
        progressStatus.style.display = 'block';
        progressStatus.textContent = 'Error: ' + err.message;
        progressStatus.style.color = 'var(--danger)';
    } finally {
        runBtn.disabled = false;
        runBtn.textContent = 'Classify';
    }
}

function showImageResult(data) {
    document.getElementById('result-image').style.display = 'block';
    document.getElementById('result-state').textContent = data.state || '—';
    document.getElementById('result-model').textContent = data.model_info?.model_name || '—';
    document.getElementById('result-inference').textContent = data.inference_ms
        ? Math.round(data.inference_ms) + ' ms'
        : '—';

    if (data.download_image_url) {
        const link = document.getElementById('download-image-link');
        link.href = data.download_image_url;
        link.download = data.output_image_name || 'annotated.jpg';
        document.getElementById('download-image-row').style.display = 'block';
    }
}

function showVideoResult(data) {
    document.getElementById('result-video').style.display = 'block';

    const stats = data.statistics || {};
    document.getElementById('stat-frames').textContent = stats.total_frames_analyzed ?? data.total_frames_analyzed ?? '—';
    document.getElementById('stat-dominant').textContent = stats.most_common_state || '—';
    document.getElementById('stat-transitions').textContent = stats.state_transitions ?? '—';

    const distContainer = document.getElementById('state-distribution');
    distContainer.innerHTML = '';
    const percentages = stats.state_percentages || {};
    const sorted = Object.entries(percentages).sort((a, b) => b[1] - a[1]);
    sorted.forEach(([state, pct]) => {
        const row = document.createElement('div');
        row.className = 'dist-row';
        row.innerHTML = `<div class="dist-lbl">${state}</div><div class="dist-track"><div class="dist-fill" style="width:${pct}%"></div></div><div class="dist-pct">${pct}%</div>`;
        distContainer.appendChild(row);
    });

    const downloadPanel = document.getElementById('download-video-panel');
    if (data.download_csv_url || data.download_video_url) {
        downloadPanel.style.display = 'block';
        if (data.download_csv_url) {
            const csvLink = document.getElementById('download-csv-link');
            csvLink.href = data.download_csv_url;
            csvLink.download = data.csv_name || 'results.csv';
        }
        if (data.download_video_url) {
            const vidLink = document.getElementById('download-video-link');
            vidLink.href = data.download_video_url;
            vidLink.download = data.output_video_name || 'annotated.mp4';
        }
    }
}

async function loadHealth() {
    const statusEl = document.getElementById('model-status');
    const modelsList = document.getElementById('available-models-list');
    const modelSelect = document.getElementById('param-model');
    try {
        const res = await fetch('/api/vlm/health');
        const data = await res.json();
        if (statusEl) {
            statusEl.textContent = data.status === 'healthy' ? 'VLM Service Ready' : 'Starting up...';
            statusEl.style.color = data.status === 'healthy' ? 'var(--green)' : 'var(--amber-lit)';
        }
        if (data.available_models && data.available_models.length > 0) {
            if (modelsList) {
                modelsList.innerHTML = data.available_models.map(m =>
                    `<div style="padding:.35rem 0;border-bottom:1px solid rgba(196,120,32,.05);font-size:.65rem;color:var(--cream-dim);">${m}</div>`
                ).join('');
            }
            if (modelSelect) {
                const currentVal = modelSelect.value;
                modelSelect.innerHTML = data.available_models.map(m =>
                    `<option value="${m}"${m === currentVal ? ' selected' : ''}>${m}</option>`
                ).join('');
            }
        } else {
            if (modelsList) modelsList.textContent = 'No vision models found. Is Ollama running?';
            if (modelSelect) modelSelect.innerHTML = '<option value="">No vision models found</option>';
        }
    } catch {
        if (statusEl) statusEl.textContent = 'Service Unavailable';
        if (modelsList) modelsList.textContent = 'Could not load models';
        if (modelSelect) modelSelect.innerHTML = '<option value="">Service unavailable</option>';
    }
}
