async function initPage() {
  try {
    const res = await fetch("/api/models");
    if (!res.ok) throw new Error("Network response was not ok");
    const models = await res.json();

    const grid = document.getElementById("model-grid");
    
    // We will use a generic icon for dynamically loaded models
    const ICONS = [
      '<path d="M2 2h12v12H2z" /><circle cx="8" cy="8" r="3" />',
      '<path d="M14 6L8 1 2 6v8h12V6z" /><path d="M6 14v-4h4v4" />',
      '<circle cx="8" cy="8" r="5" /><path d="M12 4l3-3M4 12l-3 3M12 12l3 3M4 4L1 1" />',
      '<path d="M4 4h8v8H4z" /><path d="M8 1v14M1 8h14" />',
      '<path d="M2 14V2h12v12l-6-3-6 3z" />',
      '<circle cx="8" cy="8" r="4"/><path d="M1 1l3 3M15 15l-3-3M1 15l3-3M15 1l-3 3"/>'
    ];

    if (grid && models.length) {
      grid.innerHTML = models.map((m, i) => `
        <div class="model-card">
          <div class="model-icon-wrap">
            <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4">${ICONS[i % ICONS.length]}</svg>
          </div>
          <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:.4rem">
            <div class="model-name">${m.name}</div>
            <span class="badge ${m.status === 'Running' ? 'active' : 'inactive'}" style="margin-top:.2rem">${m.status}</span>
          </div>
          <div class="model-desc">
            Category: <strong>${m.category}</strong><br/>
            Version: ${m.version}<br/>
            Size: ${m.size}
          </div>
          <div class="acc-label">
            <span>Readiness</span>
            <span>100%</span>
          </div>
          <div class="acc-track">
            <div class="acc-fill" style="width: 100%"></div>
          </div>
          <div class="model-stats-row">
            <div><div class="msi-n">${m.category.includes('Vision') ? 'VL' : 'TXT'}</div><div class="msi-l">Capabilities</div></div>
            <div><div class="msi-n">${m.id}</div><div class="msi-l">Model ID</div></div>
          </div>
        </div>
      `).join("");
    } else if (grid) {
      grid.innerHTML = '<div style="color:var(--cream-dim)">No models found or Ollama is not running.</div>';
    }
  } catch (error) {
    console.error("Error fetching models:", error);
    const grid = document.getElementById("model-grid");
    if(grid) {
       grid.innerHTML = '<div style="color:var(--danger)">Failed to fetch models. Is Ollama running on port 11434?</div>';
    }
  }
}
