
// Model Testing Logic

let selectedTestedModel = null;
let uploadedFile = null;

window.openModelTesting = function(cardEl, name, category, version) {
  selectedTestedModel = { name, category, version };
  
  // Show header
  const th = document.getElementById('testing-header');
  if(th) th.style.display = 'block';
  
  const tm = document.getElementById('tested-model-name');
  if(tm) tm.innerText = name;
  
  const tmeta = document.getElementById('tested-model-meta');
  if(tmeta) tmeta.innerHTML = category + ' &middot; ' + version;
  
  // Show tab button and switch to it
  const pt = document.getElementById('pt-testing');
  if(pt) pt.style.display = 'block';
  
  if (typeof switchAITab === 'function') switchAITab('vision');
  
  // Add auto-focus to prompt
  setTimeout(() => {
     const p = document.getElementById('model-prompt');
     if(p) p.focus();
  }, 100);
}

function initVisionTestingPage() {
  window.initDropZone();
  
  // Setup nice focus states for the prompt (Liquid Glass feel)
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

  document.getElementById('file-input').value = '';
  document.getElementById('run-btn').disabled = true;
  window.clearResults();
}

window.clearResults = function() {
  document.getElementById('res-empty').style.display = 'block';
  document.getElementById('res-content').style.display = 'none';
  document.getElementById('res-content').innerHTML = '';
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
  
  pStat.innerText = 'Extracting frames...';
  fill.style.width = '20%';
  
  // Grab a frame from the video element
  const video = document.getElementById('video-el');
  let base64Image = "";
  if (video && video.videoWidth > 0) {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
    base64Image = dataUrl.split(',')[1];
  }
  
  pStat.innerText = 'Encoding visual data and injecting prompt...';
  fill.style.width = '55%';
  
  const pInput = document.getElementById('model-prompt');
  const promptValue = pInput ? (pInput.value || 'Describe the contents of this frame.') : 'Describe this image.';
  const modelName = selectedTestedModel ? selectedTestedModel.name : 'llava';
  // Attempt to use a real Ollama model ID based on the name, fallback to llava
  const ollamaModelId = selectedTestedModel ? selectedTestedModel.name.split(':')[0].toLowerCase() : 'llava';

  pStat.innerText = 'Running inference...';
  fill.style.width = '85%';
  
  let resultText = "";
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: ollamaModelId,
        prompt: promptValue,
        image: base64Image
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Analysis failed");
    }
    const data = await res.json();
    resultText = data.response || "No response generated.";
  } catch (err) {
    console.error("Analysis Error:", err);
    resultText = "Error during analysis: " + err.message;
  }

  fill.style.width = '100%';
  pStat.innerText = 'Done.';
  setTimeout(() => {
    if(pbWrap) pbWrap.style.display = 'none';
    if(pStat) pStat.style.display = 'none';
  }, 400);
  
  document.getElementById('res-empty').style.display = 'none';
  const resContent = document.getElementById('res-content');
  resContent.style.display = 'block';
  
  const clearBtn = document.getElementById('clear-btn');
  if(clearBtn) clearBtn.style.display = 'inline-block';
  btn.disabled = false;

  let txt = "Analysis completed by " + modelName + ".\n\nPrompt:\n\"" + promptValue + "\"\n\nFindings:\n" + resultText.trim();
  
  // Typewriter effect
  resContent.innerHTML = '';
  for (let i = 0; i < txt.length; i++) {
    await new Promise(r => setTimeout(r, Math.random() * 15 + 10)); // Fast typing
    resContent.innerHTML += txt[i];
  }
}

// Call init once the page is fully loaded
if(document.readyState === 'complete') {
  initVisionTestingPage();
} else {
  window.addEventListener('load', initVisionTestingPage);
}
