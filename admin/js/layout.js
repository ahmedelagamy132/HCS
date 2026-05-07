async function loadComponent(id, url) {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Component fetch failed");
    const html = await res.text();
    document.getElementById(id).innerHTML = html;
  } catch (err) {
    console.error(`Failed to load ${url} into #${id}`, err);
  }
}

// Load shared components
document.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([
    loadComponent("sidebar-container", "/admin/components/sidebar.html"),
    loadComponent("header-container", "/admin/components/header.html")
  ]);

  // Update active state in sidebar based on current pathname
  const path = window.location.pathname;
  let foundActive = false;
  document.querySelectorAll(".nav-item").forEach(item => {
    item.classList.remove("active");
    const href = item.getAttribute("href");
    if (href && path.endsWith(href.split("/").pop())) {
      item.classList.add("active");
      foundActive = true;
      // Update breadcrumb
      const bc = document.getElementById("bc-cur");
      if (bc) bc.textContent = item.textContent.trim().replace(/\s+/g, " ").split(" ")[0] +
        (item.textContent.trim().includes(" ") ? " " + item.textContent.trim().split(/\s+/).slice(1).join(" ") : "");
    }
  });

  if (!foundActive) {
    const bc = document.getElementById("bc-cur");
    if (bc) {
      if (document.title.includes("—")) {
        bc.textContent = document.title.split("—")[0].trim();
      } else {
        bc.textContent = document.title;
      }
    }
  }

  const updateTopDate = () => {
    const el = document.getElementById('tb-date');
    if (!el) return;
    const now = new Date();
    const ops = { weekday: 'short', month: 'short', day: 'numeric' };
    el.innerHTML = now.toLocaleDateString('en-US', ops) + ' &middot; ' + now.getFullYear() + ' &nbsp; ' + now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  };
  updateTopDate();
  setInterval(updateTopDate, 60000); // 1 minute

  const loadBadges = async () => {
    try {
      const [kpiRes, modelsRes] = await Promise.all([
        fetch('/api/kpis').catch(() => null),
        fetch('/api/models').catch(() => null)
      ]);

      if (kpiRes && kpiRes.ok) {
        const kpis = await kpiRes.json();
        const clientsBadge = document.getElementById('badge-clients');
        const stablesBadge = document.getElementById('badge-stables');
        const horsesBadge = document.getElementById('badge-horses');
        if (clientsBadge) clientsBadge.textContent = Number(kpis.active_clients || 0) + Number(kpis.pending_clients || 0);
        if (stablesBadge) stablesBadge.textContent = kpis.active_stables || '0';
        if (horsesBadge) horsesBadge.textContent = kpis.total_horses || '0';
      }

      if (modelsRes && modelsRes.ok) {
        const models = await modelsRes.json();
        const modelsBadge = document.getElementById('badge-aimodels');
        if (modelsBadge) modelsBadge.textContent = Array.isArray(models) ? models.length : '0';
      }
    } catch (e) {
      console.error(e);
    }
  };
  loadBadges();

  // Load User Data for Sidebar
  window.loadUserSidebar = async () => {
    try {
      const res = await fetch('/api/account');
      if (res.ok) {
        const data = await res.json();
        const nameEl = document.getElementById('sb-user-name');
        const roleEl = document.getElementById('sb-user-role');
        const avatarEl = document.getElementById('sb-user-avatar');
        if (nameEl) nameEl.textContent = data.full_name || 'Admin';
        if (roleEl) roleEl.textContent = (data.role || 'Admin').replace('_', ' ').toUpperCase();
        if (avatarEl && data.full_name) {
          avatarEl.textContent = data.full_name.charAt(0).toUpperCase();
        }
      }
    } catch (e) {
      console.error("Failed to load user info for sidebar:", e);
    }
  };
  window.loadUserSidebar();

  // Check if page needs specific API data loading
  if (typeof initPage === "function") {
    initPage();
  }
});
