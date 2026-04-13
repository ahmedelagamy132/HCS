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
  document.querySelectorAll(".nav-item").forEach(item => {
    item.classList.remove("active");
    const href = item.getAttribute("href");
    if (href && path.endsWith(href.split("/").pop())) {
      item.classList.add("active");
      // Update breadcrumb
      const bc = document.getElementById("bc-cur");
      if (bc) bc.textContent = item.textContent.trim().replace(/\s+/g, " ").split(" ")[0] +
        (item.textContent.trim().includes(" ") ? " " + item.textContent.trim().split(/\s+/).slice(1).join(" ") : "");
    }
  });

  // Check if page needs specific API data loading
  if (typeof initPage === "function") {
    initPage();
  }
});
