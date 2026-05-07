// Code for horses.html
async function initPage() {
  try {
    const res = await fetch("/api/horses");
    if (!res.ok) throw new Error("Network error fetching horses");
    const horses = await res.json();
    
    const tbody = document.querySelector("#horses-tbody");
    
    // Update stats if possible
    const totalHorses = horses.length;
    const criticalHorses = horses.filter(h => h.health_status === 'critical' || h.health_status === 'poor').length;
    const observationHorses = horses.filter(h => h.health_status === 'fair').length;
    const healthyHorses = horses.filter(h => h.health_status === 'good' || h.health_status === 'excellent').length;
    
    const statCells = document.querySelectorAll(".stat-row .stat-n");
    if (statCells.length >= 4) {
      statCells[0].innerText = totalHorses;
      statCells[1].innerText = healthyHorses;
      statCells[2].innerText = observationHorses;
      statCells[3].innerText = criticalHorses;
    }

window.currentData = horses;
    if (typeof renderTable === 'function') renderTable();
  } catch (error) {
    console.error(error);
  }
}

function renderTable() {
    const tbody = document.querySelector("#horses-tbody");
    if (!tbody) return;

    let filtered = window.currentData || [];
    
    const searchInput = document.querySelector(".tbl-search");
    if (searchInput && searchInput.value) {
        const query = searchInput.value.toLowerCase();
        filtered = filtered.filter(h => 
            (h.name && h.name.toLowerCase().includes(query)) ||
            (h.breed && h.breed.toLowerCase().includes(query)) ||
            (h.owner_name && h.owner_name.toLowerCase().includes(query)) ||
            (h.horse_code && h.horse_code.toLowerCase().includes(query)) ||
            (h.stable_name && h.stable_name.toLowerCase().includes(query))
        );
    }
    
    const selects = document.querySelectorAll(".tbl-select");
    if (selects.length >= 2) {
      const stableFilter = selects[0].value.toLowerCase();
      if (!stableFilter.includes('all')) {
        filtered = filtered.filter(h => {
          const sName = (h.stable_name || '').toLowerCase();
          return sName.includes(stableFilter) || stableFilter.includes(sName);
        });
      }
      const healthFilter = selects[1].value.toLowerCase();
      if (!healthFilter.includes('all')) {
        filtered = filtered.filter(h => (h.health_status || 'ok').toLowerCase() === healthFilter);
      }
    }

    tbody.innerHTML = filtered.map(h => {
      const lastDate = h.last_check_at ? new Date(h.last_check_at).toLocaleDateString('en-US', {month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'}) : 'No checks';

      let badgeClass = 'active';
      let healthColorClass = 'excellent';

      if (h.health_status === 'critical' || h.health_status === 'poor') {     
        badgeClass = 'critical';
        healthColorClass = 'critical';
      } else if (h.health_status === 'fair') {
        badgeClass = 'warning';
        healthColorClass = 'fair';
      }

      return `
      <tr>
        <td class="id-c">${h.horse_code || ('HR-' + h.id.substring(0,4).toUpperCase())}</td>
        <td class="nm-c" style="cursor: pointer; text-decoration: underline; color: var(--amber-lit);" onclick="window.location.href='/admin/horse-stream.html?id=${h.id}'">${h.name || 'Unnamed'}</td>
        <td>${h.breed || '-'}</td>
        <td>${h.age_years !== null ? h.age_years + ' yrs' : '-'}</td>
        <td>${h.owner_name || 'N/A'}</td>
        <td>${h.stable_name || "Unassigned"}</td>
                <td>${lastDate}</td>
        <td>
          <div class="act-btns">
            <button class="tbtn stream-btn" onclick="window.location.href='/admin/horse-stream.html?id=${h.id}'">Live View</button>
            <button class="tbtn edit-btn">View / Edit</button>
          </div>
        </td>
      </tr>
      `;
    }).join("");

    // Attach edit events
    tbody.querySelectorAll(".edit-btn").forEach((btn, idx) => {
        btn.addEventListener("click", () => {
            const item = filtered[idx];
            const modal = document.getElementById("add-horse-modal");
            const form = document.getElementById("add-horse-form");
            if (modal && form) {
                // Populate
                Object.keys(item).forEach(k => {
                    if (form.elements[k]) form.elements[k].value = item[k];
                });
                modal.classList.add("active");
                const mtitle = modal.querySelector(".modal-header");
                if (mtitle) mtitle.innerText = "Edit Horse";
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
            a.download = 'horses_export.csv';
            a.click();
            window.URL.revokeObjectURL(url);
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    attachFilters();
    const modal = document.getElementById("add-horse-modal");
    const form = document.getElementById("add-horse-form");
    
    // Find the add button
    const addBtn = document.querySelector(".ph-actions .btn-p");
    if (addBtn) {
        addBtn.addEventListener("click", () => {
            modal.classList.add("active");
        });
    }

    // Attach global close helper
    window.closeHorseModal = () => {
        if(modal) modal.classList.remove("active");
        if(form) form.reset();
    };

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            try {
                const res = await fetch("/api/horses", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data)
                });
                
                if (!res.ok) throw new Error("Error saving horse");
                
                closeHorseModal();
                if (typeof initPage === 'function') initPage(); // reload table
            } catch (err) {
                console.error(err);
                alert("Failed to add horse.");
            }
        });
    }
});
