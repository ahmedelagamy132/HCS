// Authentication & Role Check on Page Load
const authToken = localStorage.getItem('adminToken');
const adminRole  = localStorage.getItem('adminRole') || 'view_only';

if (!authToken && !window.location.pathname.includes('/login')) {
  window.location.href = '/admin/login';
}

// Pages each role is allowed to visit
const roleAccess = {
  super_admin:  ['dashboard', 'clients', 'stables', 'horses', 'admins', 'ai-models', 'dlc-analysis', 'ai-chatbot', 'yolo-analysis', 'vlm-analysis', 'reports', 'settings', 'account', 'horse-stream'],
  staff_admin:  ['dashboard', 'clients', 'stables', 'horses', 'ai-models', 'dlc-analysis', 'ai-chatbot', 'yolo-analysis', 'vlm-analysis', 'reports', 'settings', 'account', 'horse-stream'],
  view_only:    ['dashboard', 'horses', 'dlc-analysis', 'ai-chatbot', 'yolo-analysis', 'vlm-analysis', 'reports', 'account'],
};

// Guard: redirect unauthorised page visits to dashboard
(function enforcePageAccess() {
  const path = window.location.pathname;
  if (path.includes('/login')) return;
  const page = path.split('/').pop().replace('.html', '') || 'dashboard';
  const allowed = roleAccess[adminRole] || roleAccess['view_only'];
  if (!allowed.includes(page)) {
    window.location.href = '/admin/dashboard.html';
  }
})();

// Global Fetch Interceptor to include Authorization Header
const originalFetch = window.fetch;
window.fetch = async function () {
  let [resource, config] = arguments;
  if(typeof resource === 'string' && resource.startsWith('/api') && !resource.includes('/api/auth/login')) {
    config = config || {};
    config.headers = config.headers || {};
    const token = localStorage.getItem('adminToken');
    if(token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
  }
  const response = await originalFetch(resource, config);
  if (response.status === 401 && !resource.includes('/api/auth/login')) {
    localStorage.removeItem('adminToken');
    window.location.href = '/admin/login';
  }
  return response;
};

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

  // Hide nav items the current role cannot access
  document.querySelectorAll('[data-roles]').forEach(el => {
    const allowed = el.getAttribute('data-roles').split(',');
    if (!allowed.includes(adminRole)) {
      el.style.display = 'none';
    }
  });

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
      const res = await fetch('/api/auth/me');
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

  // Inject sign-out button into sidebar footer
  const sbFooter = document.querySelector('.sb-footer');
  if (sbFooter) {
    const btn = document.createElement('button');
    btn.id = 'sb-logout-btn';
    btn.innerHTML = `<svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" style="flex-shrink:0"><path d="M10 8H2M6 4l-4 4 4 4"/><path d="M6 2h6a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H6"/></svg> Sign Out`;
    btn.style.cssText = `
      display:flex;align-items:center;gap:.5rem;width:100%;margin-top:.9rem;
      background:transparent;border:1px solid rgba(192,64,64,.25);color:rgba(192,64,64,.7);
      padding:.5rem .9rem;font-family:'Jost',sans-serif;font-size:.55rem;font-weight:500;
      letter-spacing:.2em;text-transform:uppercase;cursor:pointer;border-radius:5px;
      transition:border-color .2s,color .2s,background .2s;
    `;
    btn.addEventListener('mouseenter', () => {
      btn.style.borderColor = 'rgba(192,64,64,.7)';
      btn.style.color = '#C04040';
      btn.style.background = 'rgba(192,64,64,.06)';
    });
    btn.addEventListener('mouseleave', () => {
      btn.style.borderColor = 'rgba(192,64,64,.25)';
      btn.style.color = 'rgba(192,64,64,.7)';
      btn.style.background = 'transparent';
    });
    btn.addEventListener('click', async () => {
      try {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: { 'Authorization': 'Bearer ' + localStorage.getItem('adminToken') }
        });
      } catch (e) {}
      localStorage.removeItem('adminToken');
      localStorage.removeItem('adminRole');
      window.location.href = '/admin/login';
    });
    sbFooter.appendChild(btn);
  }

  // Check if page needs specific API data loading
  if (typeof initPage === "function") {
    initPage();
  }
});
