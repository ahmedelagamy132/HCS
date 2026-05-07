async function initPage() {
  try {
    const res = await fetch("/api/kpis");
    if (!res.ok) throw new Error("Network response was not ok");
    const data = await res.json();

    // Populate KPI cards
    const setKPI = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };
    
    setKPI('kpi-clients', data.active_clients || '0');
    setKPI('kpi-stables', data.active_stables || '0');
    setKPI('kpi-horses', data.total_horses || '0');
    setKPI('kpi-analyses', data.analyses_today || '0');
    setKPI('kpi-alerts', data.critical_alerts || '0');

    // Setup Export Report functionality
    const btnExport = document.getElementById('btn-export-report');
    if (btnExport) {
      btnExport.addEventListener('click', () => {
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Metric,Value\n";
        csvContent += `Total Clients,${data.active_clients || 0}\n`;
        csvContent += `Active Stables,${data.active_stables || 0}\n`;
        csvContent += `Registered Horses,${data.total_horses || 0}\n`;
        csvContent += `AI Analyses Today,${data.analyses_today || 0}\n`;
        csvContent += `Health Alerts,${data.critical_alerts || 0}\n`;

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `HCS_Report_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      });
    }

  } catch (error) {
    console.error("Error fetching KPIs:", error);
  }

  try {
    const resActs = await fetch("/api/recent-activity");
    if (resActs.ok) {
      const activities = await resActs.json();
      const af = document.getElementById("activity-feed");
      if (af && activities.length) {
        af.innerHTML = activities.map(act => {
          let dotColor = 'd';
          if(act.action.includes('alert') || act.action.includes('critical') || act.action.includes('failed')) dotColor = 'r';
          else if(act.action.includes('warning') || act.action.includes('issue')) dotColor = 'a';
          else if(act.action.includes('registration') || act.action.includes('success') || act.action.includes('completed')) dotColor = 'g';
          
          return `
            <div class="activity-item">
              <div class="act-dot ${dotColor}"></div>
              <div class="act-text">
                ${act.description || (act.actor_label + ' ' + act.action + ' ' + act.entity_label)}
              </div>
              <div class="act-time">${new Date(act.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
            </div>
          `;
        }).join('');
      } else if (af) {
        af.innerHTML = '<div style="color:var(--cream-dim);font-size:0.65rem;">No recent activities.</div>';
      }
    }
  } catch (err) {
    console.error("Error fetching recent activity:", err);
  }

  try {
    const resOps = await fetch('/api/dashboard/charts');
    if (resOps.ok) {
      const dbCharts = await resOps.json();

      const buildRegChart = (regData) => {
        const data = regData.map(r => Number(r.count));
        const months = regData.map(r => r.month);
        const W = 560, H = 150, pad = { t: 10, b: 10, l: 8, r: 8 };

        const minVal = Math.min(...data), maxVal = Math.max(...data);
        const min = 0, max = maxVal > 0 ? maxVal * 1.2 : 10;
        
        const xStep = data.length > 1 ? (W - pad.l - pad.r) / (data.length - 1) : 0;
        const yRange = H - pad.t - pad.b;

        const pts = data.map((v, i) => {
          const x = pad.l + i * xStep;
          const y = pad.t + yRange - ((v - min) / (max - min)) * yRange;
          return [x, y];
        });

        const lineStr = pts.map((p, i) => (i === 0 ? 'M' : 'L') + p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ');
        const areaStr = lineStr + ` L${pts[pts.length-1][0]},${H} L${pts[0][0]},${H} Z`;

        const svg = document.getElementById('reg-chart');
        if (svg) {
          svg.innerHTML = `
            <defs>
              <linearGradient id="area-grad" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#C47820" stop-opacity=".25"/>
                <stop offset="100%" stop-color="#C47820" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <path d="${areaStr}" fill="url(#area-grad)"/>
            <path d="${lineStr}" fill="none" stroke="var(--amber-lit)" stroke-width="1.5"/>
            ${pts.map((p, i) => i % 3 === 0 ? `<circle cx="${p[0]}" cy="${p[1]}" r="2.5" fill="var(--amber-lit)"/>` : '').join('')}
            ${pts.map((p, i) => `<line x1="${p[0]}" y1="${H}" x2="${p[0]}" y2="${H-4}" stroke="rgba(196,120,32,.2)" stroke-width="1"/>`).join('')}
          `;
        }

        const lblCont = document.getElementById('month-labels');
        if (lblCont) {
          lblCont.innerHTML = months.map(m => `<span>${m}</span>`).join('');
        }
      };

      const missingCounts = dbCharts.bar || {};

      const buildBarChart = () => {
        const items = [
          {label:'Health',value:Number(missingCounts.heatlh_count) || 0,color:'var(--amber-lit)'},
          {label:'Gait',value:Number(missingCounts.gait_count) || 0,color:'var(--amber)'},
          {label:'Behavior',value:Number(missingCounts.behavior_count) || 0,color:'rgba(196,120,32,.7)'},
          {label:'Diet',value:Number(missingCounts.diet_count) || 0,color:'rgba(196,120,32,.55)'},
          {label:'Disease',value:Number(missingCounts.disease_count) || 0,color:'var(--green)'},
        ].filter(item => item.value > 0);
        const maxVal = Math.max(...items.map(i => i.value), 10);
        const container = document.getElementById('bar-chart');
        if (container) {
          container.innerHTML = items.map(item => {
            const pct = (item.value / maxVal * 100).toFixed(1);
            return `<div style="display:flex;align-items:center;gap:.8rem;margin-bottom:.65rem;">
              <span style="font-size:.5rem;letter-spacing:.1em;text-transform:uppercase;color:var(--cream-dim);width:58px;text-align:right;flex-shrink:0">${item.label}</span>
              <div style="flex:1;height:6px;background:rgba(196,120,32,.1);position:relative;">
                <div style="height:100%;width:${pct}%;background:${item.color};transition:width 1s ease"></div>
              </div>
              <span style="font-family:'Cormorant Garamond',serif;font-size:.85rem;color:var(--cream);width:36px;text-align:right;flex-shrink:0">${item.value}</span>
            </div>`;
          }).join('');
        }
      };

      const buildAlerts = (alertData) => {
        const panel = document.getElementById('alerts-panel');
        if (!alertData || alertData.length === 0) {
          if (panel) panel.innerHTML = '<div style="color:var(--cream-dim);font-size:0.65rem;">No active alerts.</div>';
          return;
        }
        
        const typeMap = { 'critical': 'r', 'warning': 'a', 'info': 'g' };
        const iconMap = { 'critical': '??', 'warning': '?', 'info': '?' };

        const ALERTS = alertData.map(a => ({
          type: typeMap[a.type] || 'a',
          title: a.title,
          detail: a.detail,
          icon: iconMap[a.type] || '?'
        }));
        
        if (panel) {
          panel.innerHTML = ALERTS.map(a =>
            `<div class="alert-item ${a.type}">
              <div class="alert-icon">${a.icon}</div>
              <div><div class="alert-ttl">${a.title}</div><div class="alert-dtl">${a.detail}</div></div>
            </div>`
          ).join('');
        }
      };

      buildRegChart(dbCharts.reg);
      buildBarChart();
      buildAlerts(dbCharts.alerts);
    }
  } catch (err) {
    console.error("Error fetching dashboard charts:", err);
  }
}
