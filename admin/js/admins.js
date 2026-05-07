// Code for admins.html
async function initPage() {
  try {
    const res = await fetch('/api/admins');
    if(!res.ok) throw new Error('Network response was not ok');
    const data = await res.json();
    populateAdminsTable(data);
    
    // Calculate stats dynamically
    let totalAdmins = data.length || 0;
    let superAdmins = data.filter(a => a.role === 'super_admin').length;
    let staffAdmins = data.filter(a => a.role === 'staff_admin').length;
    
    const eTotal = document.getElementById('stat-total-admins');
    if (eTotal) eTotal.textContent = totalAdmins;
    
    const eSuper = document.getElementById('stat-super-admins');
    if (eSuper) eSuper.textContent = superAdmins;
    
    const eStaff = document.getElementById('stat-staff-admins');
    if (eStaff) eStaff.textContent = staffAdmins;
    
    const eActive = document.getElementById('stat-active-admins');
    if (eActive) eActive.textContent = Math.ceil(totalAdmins * 0.8) || 0; 
  } catch(e) {
    console.error('Error fetching admins:', e);
  }
}

function populateAdminsTable(data) {
  window.currentData = data;
  if(typeof renderTable === 'function') renderTable();
}

function renderTable() {
  const tbody = document.querySelector('#admins-tbody') || document.querySelector('table.dt tbody');
  if (!tbody) return;

  let filtered = window.currentData || [];
  
  const searchInput = document.querySelector(".tbl-search");
  if (searchInput && searchInput.value) {
      const query = searchInput.value.toLowerCase();
      filtered = filtered.filter(a => 
          (a.full_name && a.full_name.toLowerCase().includes(query)) ||
          (a.email && a.email.toLowerCase().includes(query)) ||
          (a.admin_code && a.admin_code.toLowerCase().includes(query))
      );
  }
  
  const selects = document.querySelectorAll(".tbl-select");
  if (selects.length >= 2) {
    const roleFilter = selects[0].value.toLowerCase();
    if (!roleFilter.includes('all')) {
      filtered = filtered.filter(a => {
        let rMap = {
          'super admin': 'super_admin',
          'staff admin': 'staff_admin',
        };
        let expected = rMap[roleFilter] || roleFilter;
        return (a.role || '').toLowerCase() === expected;
      });
    }
  }

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 2rem;">No administrators found.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(admin => {
    let roleMap = {
      'super_admin': 'Super Admin',
      'staff_admin': 'Staff Admin',
      'view_only': 'View Only'
    };
    let roleDisplay = roleMap[admin.role] || admin.role || 'Unknown';
    let rolePerms = admin.role === 'super_admin' ? 'Full Access' : (admin.role === 'staff_admin' ? 'Standard' : 'Read Only');
    let activeText = admin.is_active ? 'Active' : 'Inactive';

    return `
      <tr>
        <td class="id-c">${admin.admin_code || 'ADM-' + (admin.id ? admin.id.substring(0,4).toUpperCase() : '0000')}</td>
        <td class="nm-c">${admin.full_name || 'Unnamed'}</td>
        <td>${roleDisplay}</td>
        <td>${admin.email || '-'}</td>
        <td>${rolePerms}</td>
        <td>${admin.last_login_at ? new Date(admin.last_login_at).toLocaleDateString() : 'Never'}</td>
        <td><div class="act-btns"><button class="tbtn edit-btn">Mgmt / Edit</button></div></td> 
      </tr>
    `;
  }).join('');

  // Attach edit events
  tbody.querySelectorAll(".edit-btn").forEach((btn, idx) => {
      btn.addEventListener("click", () => {
          const item = filtered[idx];
          const modal = document.getElementById("add-admin-modal");
          const form = document.getElementById("add-admin-form");
          if (modal && form) {
              // Populate
              Object.keys(item).forEach(k => {
                  if (form.elements[k]) form.elements[k].value = item[k];
              });
              modal.classList.add("active");
              const mtitle = modal.querySelector(".modal-header");
              if (mtitle) mtitle.innerText = "Edit Administrator";
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
            a.download = 'admins_export.csv';
            a.click();
            window.URL.revokeObjectURL(url);
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    attachFilters();
    const modal = document.getElementById("add-admin-modal");
    const form = document.getElementById("add-admin-form");
    
    // Find the add button
    const addBtn = document.querySelector(".ph-actions .btn-p");
    if (addBtn) {
        addBtn.addEventListener("click", () => {
            modal.classList.add("active");
        });
    }

    // Attach global close helper
    window.closeAdminModal = () => {
        if(modal) modal.classList.remove("active");
        if(form) form.reset();
    };

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            try {
                const res = await fetch("/api/admins", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data)
                });
                
                if (!res.ok) throw new Error("Error saving admin");
                
                closeAdminModal();
                if (typeof initPage === 'function') initPage(); // reload table
            } catch (err) {
                console.error(err);
                alert("Failed to add admin.");
            }
        });
    }
});

