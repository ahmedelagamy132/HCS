// Code for clients.html
async function initPage() {
  try {
    const res = await fetch("/api/clients");
    if (!res.ok) throw new Error("Network error fetching clients");
    const clients = await res.json();
    
    // We would clear the tbody and render
    const tbody = document.querySelector("#tab-clients tbody");
    if (tbody && clients.length) {
      tbody.innerHTML = clients.map(c => `
        <tr>
          <td class="id-c">CL-${c.id.substring(0,4).toUpperCase()}</td>
          <td class="nm-c">${c.user_name || c.farm_name}</td>
          <td><span class="badge ${c.status === 'active' ? 'active' : 'inactive'}">${c.status || 'Active'}</span></td>
          <td>${c.total_horses || 0}</td>
          <td>${c.subscription_status || 'Trial'}</td>
          <td><div class="act-btns"><button class="tbtn">Edit</button></div></td>
        </tr>
      `).join("");
    }
  } catch (error) {
    console.error(error);
  }
}
