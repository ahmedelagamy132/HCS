// Code for stables.html
async function initPage() {
  try {
    const res = await fetch("/api/stables");
    if (!res.ok) throw new Error("Network error fetching stables");
    const stables = await res.json();
    
    const tbody = document.querySelector("#stables-tbody");
    
    // Update stats if we can
    const totalStables = stables.length;
    const fullStables = stables.filter(s => s.status === 'full').length;
    const maintenance = stables.filter(s => s.status === 'maintenance').length;
    const activeStables = totalStables - maintenance;
    
    const statCells = document.querySelectorAll(".stat-row .stat-n");
    if (statCells.length >= 4) {
      statCells[0].innerText = totalStables;
      statCells[1].innerText = activeStables;
      statCells[2].innerText = fullStables;
      statCells[3].innerText = maintenance;
    }

    window.currentData = stables;
    if (typeof renderTable === 'function') renderTable();
  } catch (error) {
    console.error(error);
  }
}

function renderTable() {
    const tbody = document.querySelector("#stables-tbody");
    if (!tbody) return;

    let filtered = window.currentData || [];
    
    const searchInput = document.querySelector(".tbl-search");
    if (searchInput && searchInput.value) {
        const query = searchInput.value.toLowerCase();
        filtered = filtered.filter(s => 
            (s.name && s.name.toLowerCase().includes(query)) ||
            (s.city && s.city.toLowerCase().includes(query)) ||
            (s.region && s.region.toLowerCase().includes(query)) ||
            (s.owner_name && s.owner_name.toLowerCase().includes(query)) ||
            (s.stable_code && s.stable_code.toLowerCase().includes(query))
        );
    }
    
    const selects = document.querySelectorAll(".tbl-select");
    if (selects.length >= 1) {
      const statusFilter = selects[0].value.toLowerCase();
      if (!statusFilter.includes('all')) {
        filtered = filtered.filter(s => (s.status || 'active').toLowerCase() === statusFilter);
      }
    }

    tbody.innerHTML = filtered.map(s => {
      const occPct = s.occupancy_pct || 0;
      const occColor = occPct > 90 ? 'var(--danger)' : (occPct > 70 ? 'var(--amber)' : 'var(--green)');

      return `
      <tr>
        <td class="id-c">${s.stable_code || ('ST-' + s.id.substring(0,4).toUpperCase())}</td>
        <td class="nm-c">${s.name || 'Unnamed'}</td>
        <td>${s.city || '-'}, ${s.region || '-'}</td>
        <td>${s.capacity || 0}</td>
        <td>${s.occupied || 0}</td>
        <td>
          <div class="obar" title="${occPct}%">
            <div class="obar-track">
              <div class="obar-fill" style="width: ${occPct}%; background: ${occColor};"></div>
            </div>
          </div>
        </td>
        <td>${s.owner_name || 'N/A'}</td>
        <td><div class="act-btns"><button class="tbtn edit-btn">Mgmt / Edit</button></div></td>
      </tr>
      `;
    }).join("");

    // Attach edit events
    tbody.querySelectorAll(".edit-btn").forEach((btn, idx) => {
        btn.addEventListener("click", () => {
            const item = filtered[idx];
            const modal = document.getElementById("add-stable-modal");
            const form = document.getElementById("add-stable-form");
            if (modal && form) {
                // Populate
                Object.keys(item).forEach(k => {
                    if (form.elements[k]) form.elements[k].value = item[k];
                });
                modal.classList.add("active");
                const mtitle = modal.querySelector(".modal-header");
                if (mtitle) mtitle.innerText = "Edit Stable";
            }
        });
    });
}

function attachFilters() {
    const searchInput = document.querySelector(".tbl-search");
    if (searchInput) searchInput.addEventListener("input", renderTable);
    
    document.querySelectorAll(".tbl-select").forEach(sel => {
        sel.addEventListener("change", renderTable);
    });

    const exportBtn = document.querySelector(".btn-g");
    if (exportBtn) {
        exportBtn.addEventListener("click", () => {
            const data = window.currentData || [];
            if (!data.length) return;
            const headers = Object.keys(data[0]).join(",");
            const rows = data.map(item => Object.values(item).map(v => `"${String(v||'').replace(/"/g, '""')}"`).join(","));
            const csv = [headers, ...rows].join("\\n");
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'stables_export.csv';
            a.click();
            window.URL.revokeObjectURL(url);
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    attachFilters();
    const modal = document.getElementById("add-stable-modal");
    const form = document.getElementById("add-stable-form");
    
    // Find the add button
    const addBtn = document.querySelector(".ph-actions .btn-p");
    if (addBtn) {
        addBtn.addEventListener("click", () => {
            modal.classList.add("active");
        });
    }

    // Attach global close helper
    window.closeStableModal = () => {
        if(modal) modal.classList.remove("active");
        if(form) form.reset();
    };

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            try {
                const res = await fetch("/api/stables", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data)
                });
                
                if (!res.ok) throw new Error("Error saving stable");
                
                closeStableModal();
                if (typeof initPage === 'function') initPage(); // reload table
            } catch (err) {
                console.error(err);
                alert("Failed to add stable.");
            }
        });
    }
});
