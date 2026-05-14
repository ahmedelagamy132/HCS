document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const dzIdle = document.getElementById('dz-idle');
    const videoPreview = document.getElementById('video-preview');
    const videoEl = document.getElementById('video-el');
    const viName = document.getElementById('vi-name');
    const viMeta = document.getElementById('vi-meta');
    const runBtn = document.getElementById('run-btn');

    let selectedFile = null;

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--amber-lit)';
        dropZone.style.background = 'rgba(196,120,32,0.05)';
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'rgba(196,120,32,0.15)';
        dropZone.style.background = 'var(--bg2)';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'rgba(196,120,32,0.15)';
        dropZone.style.background = 'var(--bg2)';

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        if (!file.type.startsWith('video/')) {
            alert('Please select a video file.');
            return;
        }

        selectedFile = file;
        viName.textContent = file.name;
        viMeta.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';

        dropZone.classList.add('has-video');
        dzIdle.style.display = 'none';
        videoPreview.style.display = 'block';
        
        const resultsPanel = document.getElementById('results-panel');
        if(resultsPanel) resultsPanel.style.display = 'block';
        
        const viRemove = document.getElementById('vi-remove');
        if(viRemove) viRemove.style.display = 'block';

        videoEl.src = URL.createObjectURL(file);
        videoEl.style.display = 'block';
        videoEl.play();

        runBtn.disabled = false;
        resetResults();
    }

    function resetResults() {
        const pbWrap = document.getElementById('progress-bar-wrap');
        const pStat = document.getElementById('progress-status');
        const resContent = document.getElementById('res-content');
        
        if (pbWrap) pbWrap.style.display = 'none';
        if (pStat) pStat.style.display = 'none';
        if (resContent) {
            resContent.style.display = 'none';
            resContent.innerHTML = '';
        }
        
        const existingOutput = document.getElementById('dlc-output-video');
        if (existingOutput) existingOutput.remove();
        
        const statsDisplay = document.getElementById('behavior-stats-display');
        if (statsDisplay) statsDisplay.remove();
    }

    window.removeVideo = function() {
        selectedFile = null;
        fileInput.value = '';
        viName.textContent = '—';
        viMeta.textContent = '0.00 MB';

        dropZone.classList.remove('has-video');
        dzIdle.style.display = 'flex';
        videoPreview.style.display = 'none';
        
        const resultsPanel = document.getElementById('results-panel');
        if(resultsPanel) resultsPanel.style.display = 'none';

        const viRemove = document.getElementById('vi-remove');
        if(viRemove) viRemove.style.display = 'none';
        
        videoEl.style.display = 'none';
        videoEl.pause();
        videoEl.removeAttribute('src');

        runBtn.disabled = true;
        resetResults();
    };

    window.runAnalysis = async function() {
        if (!selectedFile) return;

        runBtn.disabled = true;

        const pbWrap = document.getElementById('progress-bar-wrap');
        const pStat = document.getElementById('progress-status');
        const resContent = document.getElementById('res-content');

        if (resContent) {
            resContent.style.display = 'block';
            resContent.innerHTML = '';
        }

        if (pbWrap) pbWrap.style.display = 'flex';
        if (pStat) {
            pStat.style.display = 'block';
            pStat.textContent = 'Processing frame by frame...';
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        function showError(msg) {
            if (pbWrap) pbWrap.style.display = 'none';
            if (pStat) pStat.style.display = 'none';
            if (resContent) {
                resContent.innerHTML = `<span style="color:#ff6b6b">Error: ${msg}</span>`;
                resContent.style.display = 'block';
            }
        }

        try {
            const resp = await fetch('/api/analyze-direct-dlc', {
                method: 'POST',
                body: formData
            });

            if (pStat) pStat.textContent = 'Finalizing rendering...';

            if (!resp.ok) {
                let detail = resp.statusText;
                try { const j = await resp.json(); detail = j.detail || j.error || detail; } catch(_) {}
                throw new Error(detail);
            }

            const data = await resp.json();

            setTimeout(() => {
                try {
                    if (pbWrap) pbWrap.style.display = 'none';
                    if (pStat) pStat.style.display = 'none';

                    resContent.innerHTML = `<div style="display:flex; justify-content:space-between; margin-bottom:1rem; border-bottom:1px solid rgba(196,120,32,0.1); padding-bottom:0.5rem;"><span style="color:var(--amber-lit);">Analysis Complete</span><span>Frames: ${data.total_frames || '?'} • FPS: ${data.fps ? data.fps.toFixed(1) : '?'}</span></div>`;
                    resContent.style.display = 'block';

                    if (data.download_url) {
                        const outputVid = document.createElement('video');
                        outputVid.id = 'dlc-output-video';
                        outputVid.src = data.download_url;
                        outputVid.controls = true;
                        outputVid.autoplay = true;
                        outputVid.loop = true;
                        outputVid.style.cssText = 'width:100%; border-radius:4px; margin-top:.5rem;';
                        resContent.appendChild(outputVid);
                    }

                    const statsDisplay = document.createElement('div');
                    statsDisplay.id = 'behavior-stats-display';
                    statsDisplay.style.cssText = 'display:grid; grid-template-columns:repeat(2,1fr); gap:1rem; margin-top:1.5rem;';

                    if (data.behavior_statistics) {
                        const behaviors = [
                            { name: 'Standing',            color: '#4E9468' },
                            { name: 'Walking',             color: '#C47820' },
                            { name: 'Running/Trotting',    color: '#E09830' },
                            { name: 'Lying Down',          color: '#C04040' },
                            { name: 'Eating/Drinking',     color: '#4E9468' },
                            { name: 'Turning',             color: '#A39273' },
                            { name: 'Rearing',             color: '#C04040' },
                            { name: 'Head Shaking',        color: '#9A8A70' },
                            { name: 'Grooming/Scratching', color: '#7A4C12' },
                            { name: 'Kicking',             color: '#C04040' },
                            { name: 'Tail Swishing',       color: '#E09830' }
                        ];
                        behaviors.forEach(b => {
                            const stats = data.behavior_statistics[b.name];
                            if (stats) {
                                statsDisplay.innerHTML += `
                                <div style="background:var(--bg3); border:1px solid rgba(196,120,32,.12); padding:1rem; border-radius:4px;">
                                    <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                                        <span style="font-size:0.6rem; letter-spacing:0.1em; text-transform:uppercase; color:var(--cream-dim);">${b.name}</span>
                                        <span style="color:${b.color}; font-weight:bold; font-size:0.8rem;">${stats.percentage.toFixed(1)}%</span>
                                    </div>
                                    <div style="width:100%; height:4px; background:var(--bg2); border-radius:2px;">
                                        <div style="width:${stats.percentage}%; height:100%; background:${b.color}; border-radius:2px;"></div>
                                    </div>
                                    <div style="font-size:0.55rem; color:var(--cream-faint); margin-top:0.5rem; text-align:right;">${stats.frames} frames</div>
                                </div>`;
                            }
                        });
                    }

                    if (statsDisplay.innerHTML.trim()) resContent.appendChild(statsDisplay);

                } catch (renderErr) {
                    showError('Render error: ' + renderErr.message);
                }
            }, 600);

        } catch (err) {
            showError(err.message);
        } finally {
            runBtn.disabled = false;
        }
    };
});
