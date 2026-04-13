async function initPage() {
  try {
    const res = await fetch("/api/kpis");
    if (!res.ok) throw new Error("Network response was not ok");
    const data = await res.json();

    // Populate KPI cards
    document.querySelector('[data-target="284"]').textContent = data.total_clients || '284';
    document.querySelector('[data-target="47"]').textContent = data.active_stables || '47';
    document.querySelector('[data-target="1203"]').textContent = data.registered_horses || '1203';
    document.querySelector('[data-target="1847"]').textContent = data.ai_analyses_today || '1847';
    document.querySelector('[data-target="12"]').textContent = data.critical_alerts || '12';
    
  } catch (error) {
    console.error("Error fetching KPIs:", error);
  }
}
