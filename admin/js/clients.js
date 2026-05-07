// Code for clients.html
async function initPage() {
  try {
    const res = await fetch("/api/clients");
    if (!res.ok) throw new Error("Network error fetching clients");
    const clients = await res.json();
    
    // We would clear the tbody and render
    const tbody = document.querySelector("#clients-tbody");
    
    // Update stats if we can
    const totalClients = clients.length;
    const activeClients = clients.filter(c => c.status === 'active').length;
    
    // Very basic 'new this month' check based on created_at
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();
    const newThisMonth = clients.filter(c => {
      const d = new Date(c.created_at);
      return d.getMonth() === currentMonth && d.getFullYear() === currentYear;
    }).length;
    const pendingClients = clients.filter(c => c.status === 'pending').length;
    
    const statCells = document.querySelectorAll(".stat-row .stat-n");
    if (statCells.length >= 4) {
      statCells[0].innerText = totalClients;
      statCells[1].innerText = activeClients;
      statCells[2].innerText = newThisMonth;
      statCells[3].innerText = pendingClients;
    }

window.currentData = clients;
    if (typeof renderTable === 'function') {
      renderTable();
    }
  } catch (error) {
    console.error(error);
  }
}

function renderTable() {
    const tbody = document.querySelector("#clients-tbody");
    if (!tbody) return;

    let filtered = window.currentData || [];
    
    const searchInput = document.querySelector(".tbl-search");
    if (searchInput && searchInput.value) {
        const query = searchInput.value.toLowerCase();
        filtered = filtered.filter(c => 
            (c.full_name && c.full_name.toLowerCase().includes(query)) ||
            (c.email && c.email.toLowerCase().includes(query)) ||
            (c.client_code && c.client_code.toLowerCase().includes(query)) ||
            (c.region && c.region.toLowerCase().includes(query))
        );
    }
    
    const selects = document.querySelectorAll(".tbl-select");
    if (selects.length >= 2) {
      const statusFilter = selects[0].value.toLowerCase();
      if (!statusFilter.includes('all')) {
        filtered = filtered.filter(c => (c.status || 'active').toLowerCase() === statusFilter);
      }
      const regionFilter = selects[1].value.toLowerCase();
      if (!regionFilter.includes('all')) {
        filtered = filtered.filter(c => (c.region || '').toLowerCase() === regionFilter);
      }
    }

    tbody.innerHTML = filtered.map(c => {
      const sinceDate = c.created_at ? new Date(c.created_at).toLocaleDateString('en-US', {year: 'numeric', month: 'short'}) : '-';

      return `
      <tr>
        <td class="id-c">${c.client_code || ('CL-' + c.id.substring(0,4).toUpperCase())}</td>
        <td class="nm-c">${c.full_name || 'N/A'}</td>
        <td>${c.email || '-'}</td>
        <td>${c.phone || '-'}</td>
        <td>${c.stable_count || 0}</td>
        <td>${c.horse_count || 0}</td>
        <td>${c.region || '-'}</td>
        <td>${sinceDate}</td>
        <td><div class="act-btns"><button class="tbtn edit-btn" data-id="${c.id}">Edit</button></div></td>
      </tr>
      `;
    }).join("");

    // Attach edit events
    tbody.querySelectorAll(".edit-btn").forEach((btn, idx) => {
        btn.addEventListener("click", () => {
            const item = filtered[idx];
            const modal = document.getElementById("add-client-modal");
            const form = document.getElementById("add-client-form");
            if (modal && form) {
                // Populate
                Object.keys(item).forEach(k => {
                    if (form.elements[k]) form.elements[k].value = item[k];
                });
                modal.classList.add("active");
                const mtitle = modal.querySelector(".modal-header");
                if(mtitle) mtitle.innerText = "Edit Client";
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
            a.download = 'clients_export.csv';
            a.click();
            window.URL.revokeObjectURL(url);
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    attachFilters();
    const modal = document.getElementById("add-client-modal");
    const form = document.getElementById("add-client-form");
    
    // Find the add button
    const addBtn = document.querySelector(".ph-actions .btn-p");
    if (addBtn) {
        addBtn.addEventListener("click", () => {
            modal.classList.add("active");
        });
    }

    // Attach global close helper
    window.closeClientModal = () => {
        if(modal) modal.classList.remove("active");
        if(form) form.reset();
    };

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            try {
                const res = await fetch("/api/clients", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data)
                });
                
                if (!res.ok) throw new Error("Error saving client");
                
                closeClientModal();
                if (typeof initPage === 'function') initPage(); // reload table
            } catch (err) {
                console.error(err);
                alert("Failed to add client.");
            }
        });
    }
});
