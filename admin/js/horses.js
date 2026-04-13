// Code for horses.html
async function initPage() {
  try {
    const res = await fetch("/api/horses");
    if (!res.ok) throw new Error("Network error fetching horses");
    const horses = await res.json();
    
    const tbody = document.querySelector("#tab-horses tbody");
    if (tbody && horses.length) {
      tbody.innerHTML = horses.map(h => `
        <tr>
          <td class="id-c">HR-${h.id.substring(0,4).toUpperCase()}</td>
          <td class="nm-c">${h.name}</td>
          <td>${h.breed}</td>
          <td>${h.stable_name || "Unassigned"}</td>
          <td><div class="hbar"><div class="hbar-track"><div class="hbar-fill ${h.health_status}"></div></div></div></td>
          <td><span class="badge ${h.health_status === 'critical' ? 'critical' : h.health_status === 'watch' ? 'warning' : 'active'}">${h.health_status}</span></td>
          <td><div class="act-btns"><button class="tbtn">View</button></div></td>
        </tr>
      `).join("");
    }
  } catch (error) {
    console.error(error);
  }
}
