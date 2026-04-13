// Code for stables.html
async function initPage() {
  try {
    const res = await fetch("/api/stables");
    if (!res.ok) throw new Error("Network error fetching stables");
    const stables = await res.json();
    
    // We would clear the tbody and render
    const tbody = document.querySelector("#tab-stables tbody");
    if (tbody && stables.length) {
      tbody.innerHTML = stables.map(s => `
        <tr>
          <td class="id-c">ST-${s.id.substring(0,4).toUpperCase()}</td>
          <td class="nm-c">${s.name}</td>
          <td>${s.region}</td>
          <td>${s.current_occupancy}/${s.capacity}</td>
          <td><div class="obar"><div class="obar-track"><div class="obar-fill" style="width: ${(s.current_occupancy/s.capacity)*100}%; background: ${(s.current_occupancy/s.capacity) > 0.9 ? 'var(--danger)' : 'var(--amber)'}"></div></div></div></td>
          <td><span class="badge ${s.status}">${s.status}</span></td>
          <td><div class="act-btns"><button class="tbtn">Mang</button></div></td>
        </tr>
      `).join("");
    }
  } catch (error) {
    console.error(error);
  }
}
