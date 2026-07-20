/* ── Helpers ──────────────────────────────────────────────── */
const esc = (s) => String(s ?? "")
  .replace(/&/g,"&amp;").replace(/</g,"&lt;")
  .replace(/>/g,"&gt;").replace(/"/g,"&quot;");

const fmtCr = (v) => {
  if (v == null) return null;
  const cr = Number(v) / 100;
  if (Math.abs(cr) >= 1e5) return `₹${(cr/1e5).toFixed(2)} L Cr`;
  if (Math.abs(cr) >= 1e3) return `₹${(cr/1e3).toFixed(2)}K Cr`;
  return `₹${cr.toLocaleString("en-IN", {maximumFractionDigits:2})} Cr`;
};

const fmtDate = (v) => {
  if (!v) return "—";
  const d = new Date(v + "T00:00:00");
  return isNaN(d) ? v : d.toLocaleDateString("en-IN", {day:"2-digit",month:"short",year:"numeric"});
};

const fmtDateShort = (v) => {
  if (!v) return "—";
  const d = new Date(v + "T00:00:00");
  return isNaN(d) ? v : d.toLocaleDateString("en-IN", {day:"2-digit",month:"short"});
};

const initials = (name) => {
  if (!name) return "?";
  const w = name.trim().split(/\s+/);
  return w.length === 1 ? w[0].slice(0,2).toUpperCase() : (w[0][0]+w[1][0]).toUpperCase();
};

const quarterLabel = (qEnd) => {
  if (!qEnd) return "";
  const d = new Date(qEnd + "T00:00:00");
  const m = d.getMonth() + 1, y = d.getFullYear();
  const fy = m >= 4 ? y : y-1;
  const q  = m <= 3 ? 4 : m <= 6 ? 1 : m <= 9 ? 2 : 3;
  return `Q${q} FY${String(fy).slice(-2)}`;
};

const currentFY = () => {
  const now = new Date();
  const yr  = now.getMonth() >= 3 ? now.getFullYear() : now.getFullYear()-1;
  const q   = [4,1,1,1,2,2,2,3,3,3,4,4][now.getMonth()];
  return `Q${q} FY${String(yr).slice(-2)}`;
};

/* ── Page navigation ──────────────────────────────────────── */
function showPage(id) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.getElementById(id).classList.add("active");
  window.scrollTo(0, 0);

  // Sync top nav active state
  document.querySelectorAll(".top-nav-link").forEach(l => l.classList.remove("active"));
  if (id === "page-home")     document.getElementById("top-nav-home")?.classList.add("active");
  if (id === "page-calendar") document.getElementById("top-nav-calendar")?.classList.add("active");
}

/* ── State ────────────────────────────────────────────────── */
let selectedSymbol = null;

/* ── Boot ─────────────────────────────────────────────────── */
document.getElementById("season-label").textContent = currentFY();

/* ── Tab switching ────────────────────────────────────────── */
function switchTab(tab) {
  const isDesktop = window.innerWidth >= 768;
  if (isDesktop) {
    document.getElementById("list-released").style.display = "block";
    document.getElementById("list-upcoming").style.display  = "block";
  } else {
    document.getElementById("list-released").style.display = tab === "released" ? "block" : "none";
    document.getElementById("list-upcoming").style.display  = tab === "upcoming"  ? "block" : "none";
  }
  document.getElementById("tab-released").classList.toggle("active", tab === "released");
  document.getElementById("tab-upcoming").classList.toggle("active",  tab === "upcoming");
}

/* ── Build card ───────────────────────────────────────────── */
function buildCard(item, type) {
  const card = document.createElement("div");
  card.className = "company-card";
  card.dataset.isRevision = item.is_revision == 1 ? "true" : "false";
  if (type === "released") {
    const pat = item.pat != null ? Number(item.pat) / 100 : null;
    const inc = item.total_income != null ? Number(item.total_income) / 100 : null;
    let badge = "";
    if (item.no_data) {
      badge = `<div class="profit-badge fetch-hint">Tap to fetch</div>`;
    } else if (pat != null && inc != null && inc !== 0) {
      const pct = ((pat / inc) * 100).toFixed(1);
      const up  = pat >= 0;
      if (up) {
        badge = `<div class="profit-badge up">PROFIT ↑ +${pct}%</div>`;
      } else {
        badge = `<div class="profit-badge down">LOSS ↓</div>`;
      }
    } 
    card.innerHTML = `
      <div class="card-avatar">${esc(initials(item.company_name))}</div>
      <div class="card-body">
        <div class="card-name">${esc(item.company_name)}</div>
        <div class="card-sector">
          ${esc(item.consolidated||"")}
          ${item.is_revision == 1 ? `<span class="rev-badge">Revised</span>` : `<span class="rev-badge original">Original</span>`}
        </div>
      </div>
      <div class="card-right">${badge}</div>
      <svg class="chevron" width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>`;
  } else {
    card.innerHTML = `
      <div class="card-avatar">${esc(initials(item.company_name))}</div>
      <div class="card-body">
        <div class="card-name">${esc(item.company_name)}</div>
        <div class="card-sector">${esc(item.purpose||"Financial Results")}</div>
      </div>
      <div class="card-right" style="flex-direction:row; align-items:center; gap:6px; flex-shrink:0;">
        <div class="card-time">${fmtDateShort(item.meeting_date)}</div>
        <div class="card-est">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/>
            <path d="M12 7v5l3 3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg> EST.
        </div>
        <svg class="chevron" width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>`;
  }

  card.addEventListener("click", () => openDetail(item.symbol, item.company_name));
  return card;
}


/* ── Toggle Filter Function ─────────────────────────────────────────── */
let activeFilter = 'all';
function setFilter(filter) {
  activeFilter = filter;
  document.querySelectorAll('.filter-chip').forEach(btn => btn.classList.remove('active'));
  document.getElementById(`filter-${filter}`).classList.add('active');

  document.querySelectorAll('#list-released .company-card').forEach(card => {
    const isRevision = card.dataset.isRevision === 'true';
    if (filter === 'all') {
      card.style.display = '';
    } else if (filter === 'original') {
      card.style.display = isRevision ? 'none' : '';
    } else if (filter === 'revised') {
      card.style.display = isRevision ? '' : 'none';
    }
  });
}

/* ── Render lists ─────────────────────────────────────────── */
function renderList(rows, listId, emptyId, type, groupKey) {
  const list  = document.getElementById(listId);
  const empty = document.getElementById(emptyId);
  list.innerHTML = "";

  if (!rows.length) {
    empty.style.display = "block";
    return;
  }
  empty.style.display = "none";

  const groups = {};
  rows.forEach(r => {
    const key = r[groupKey] || "—";
    if (!groups[key]) groups[key] = [];
    groups[key].push(r);
  });

  Object.entries(groups).forEach(([date, items]) => {
    const label = document.createElement("div");
    label.className = "date-group-label";
    label.textContent = fmtDate(date).toUpperCase();
    list.appendChild(label);
    items.forEach(item => list.appendChild(buildCard(item, type)));
  });
}

/* ── Open detail page ─────────────────────────────────────── */
async function openDetail(symbol, companyName) {
  selectedSymbol = symbol;
  document.getElementById("detail-symbol").textContent = symbol;
  document.getElementById("detail-body").innerHTML =
    `<div style="padding:60px 20px;text-align:center;color:var(--text-3)">Loading…</div>`;
  document.getElementById("detail-fetch-bar").style.display = "none";

  showPage("page-detail");

  const res      = await fetch(`/api/symbol/${encodeURIComponent(symbol)}`);
  const existing = await res.json();

  if (existing && existing.length) {
    renderDetail(existing);
    document.getElementById("detail-fetch-bar").style.display = "block";
  } else {
    await triggerFetch();
  }
}

function closeDetail() {
  showPage("page-home");
  selectedSymbol = null;
}

/* ── Render detail ────────────────────────────────────────── */
/* ── Render detail ────────────────────────────────────────── */
function renderDetail(rows) {
  const body = document.getElementById("detail-body");
  body.innerHTML = "";
  const first = rows[0];

  const hero = document.createElement("div");
  hero.className = "hero-card";
  hero.innerHTML = `
    <div class="hero-top">
      <div class="hero-avatar">${esc(initials(first.company_name))}</div>
      <div>
        <div class="hero-name">${esc(first.company_name)}</div>
        <div class="hero-exchange">NSE: ${esc(first.symbol)}</div>
      </div>
    </div>
    <div class="hero-tags">
      <span class="tag">${esc(first.consolidated||"Consolidated")}</span>
      ${first.filing_date && first.filing_date !== "revised" ? `<span class="tag">Filed ${fmtDate(first.filing_date)}</span>` : ""}
    </div>`;
  body.appendChild(hero);

  const METRICS = [
    { key:"total_income",  label:"Total Revenue",     cr:true  },
    { key:"total_expense", label:"Total Expenses",    cr:true  },
    { key:"pbt",           label:"Profit Before Tax", cr:true  },
    { key:"pat",           label:"Profit After Tax",  cr:true  },
    { key:"eps",           label:"EPS (Basic)",       cr:false },
  ];

  const byType = {};
  rows.forEach(r => { byType[r.row_type] = r; });

  const currRow = byType["current_quarter"];
  const prevRow = byType["previous_quarter"];
  const yearRow = byType["full_year"];

  const isMobile = window.innerWidth < 768;

  if (isMobile) {
    // ── MOBILE: 3 separate cards ──

    
    const buildSimpleCard = (row, title, compareRow) => {
      const card = document.createElement("div");
      card.className = "quarter-card";
      const metricRows = METRICS.map(m => {
        const raw  = row[m.key];
        const prev = compareRow ? compareRow[m.key] : null;
        let val, cls = "";
        if (raw == null)       { val = "—"; cls = "na"; }
        else if (!m.cr)        { val = `₹${Number(raw).toFixed(2)}`; cls = Number(raw) < 0 ? "negative" : ""; }
        else                   { val = fmtCr(raw); cls = Number(raw) < 0 ? "negative" : ""; }
        
        
        let qoq = "";
        if (raw != null && prev != null && prev !== 0) {
          const pct = ((raw - prev) / Math.abs(prev)) * 100;
          const up  = pct >= 0;
          if (raw >= 0) {
            qoq = `<span class="qoq-badge ${up?"up":"down"}">${up?"▲":"▼"} ${Math.abs(pct).toFixed(1)}%</span>`;
          } else {
            qoq = `<span class="qoq-badge down">▼</span>`;
          }
        }

        return `<div class="metric-row">
          <div class="metric-label">${m.label}</div>
          <div class="metric-value ${cls}">${val}${qoq}</div>
        </div>`;
      }).join("");
      card.innerHTML = `
        <div class="quarter-header">
          <div class="quarter-title">${title}</div>
          <div class="quarter-period">${quarterLabel(row.quarter_end)}</div>
        </div>${metricRows}`;
      return card;
    };

    if (currRow) body.appendChild(buildSimpleCard(currRow, "Current Quarter", prevRow));
    if (prevRow) body.appendChild(buildSimpleCard(prevRow, "Previous Quarter"));
    if (yearRow) body.appendChild(buildSimpleCard(yearRow, "Annual"));

  } else {
    // ── DESKTOP: combined card + full year ──

    if (currRow || prevRow) {
      const card = document.createElement("div");
      card.className = "quarter-card";
      const currLabel = currRow ? quarterLabel(currRow.quarter_end) : "—";
      const prevLabel = prevRow ? quarterLabel(prevRow.quarter_end) : "—";

      const metricRows = METRICS.map(m => {
        const currRaw = currRow ? currRow[m.key] : null;
        const prevRaw = prevRow ? prevRow[m.key] : null;

        const fmtVal = (raw) => {
          if (raw == null) return { val: "—", cls: "na" };
          if (!m.cr) return { val: `₹${Number(raw).toFixed(2)}`, cls: Number(raw) < 0 ? "negative" : "" };
          return { val: fmtCr(raw), cls: Number(raw) < 0 ? "negative" : "" };
        };

        const curr = fmtVal(currRaw);
        const prev = fmtVal(prevRaw);

        let qoq = "";
        if (currRaw != null && prevRaw != null && prevRaw !== 0) {
          const pct = ((currRaw - prevRaw) / Math.abs(prevRaw)) * 100;
          const up  = pct >= 0;
          qoq = `<span class="qoq-badge ${up?"up":"down"}">${up?"▲":"▼"} ${Math.abs(pct).toFixed(1)}%</span>`;
        }

        return `<div class="metric-row">
          <div class="metric-label">${m.label}</div>
          <div class="metric-right">
            <div class="metric-value ${prev.cls} prev-value">${prev.val}</div>
            <div class="metric-value ${curr.cls}">${curr.val}${qoq}</div>
          </div>
        </div>`;
      }).join("");

      card.innerHTML = `
        <div class="quarter-header">
          <div class="quarter-title">Quarterly</div>
          <div class="quarter-col-labels">
            <span class="col-label-prev">${prevLabel}</span>
            <span class="col-label-curr">${currLabel}</span>
          </div>
        </div>${metricRows}`;
      body.appendChild(card);
    }

    if (yearRow) {
      const card = document.createElement("div");
      card.className = "quarter-card";
      const metricRows = METRICS.map(m => {
        const raw = yearRow[m.key];
        let val, cls = "";
        if (raw == null)  { val = "—"; cls = "na"; }
        else if (!m.cr)   { val = `₹${Number(raw).toFixed(2)}`; cls = Number(raw) < 0 ? "negative" : ""; }
        else              { val = fmtCr(raw); cls = Number(raw) < 0 ? "negative" : ""; }
        return `<div class="metric-row">
          <div class="metric-label">${m.label}</div>
          <div class="metric-right">
            <div class="metric-value ${cls}">${val}</div>
          </div>
        </div>`;
      }).join("");
      card.innerHTML = `
        <div class="quarter-header">
          <div class="quarter-title">Trailing 12 Months</div>
          <div class="quarter-period">${quarterLabel(yearRow.quarter_end)}</div>
        </div>${metricRows}`;
      body.appendChild(card);
    }
  }

  document.querySelector(".fetch-btn-label").textContent = "Refresh Data";
}

/* ── Fetch ────────────────────────────────────────────────── */
async function triggerFetch() {
  if (!selectedSymbol) return;
  const sym = selectedSymbol;
  const btn = document.getElementById("fetch-btn");
  const lbl = document.querySelector(".fetch-btn-label");
  const spn = document.querySelector(".fetch-btn-spinner");
  btn.disabled = true;
  lbl.style.display = "none";
  spn.style.display = "inline-flex";
  document.getElementById("detail-fetch-bar").style.display = "block";

  try {
    const res  = await fetch(`/api/fetch/${encodeURIComponent(sym)}`, {method:"POST"});
    const data = await res.json();
    if (data.ok) {
      const r2   = await fetch(`/api/symbol/${encodeURIComponent(sym)}`);
      const rows = await r2.json();
      if (rows && rows.length) {
        renderDetail(rows);
        document.getElementById("detail-fetch-bar").style.display = "block";
      }
      loadReleased();
    } else {
      alert(data.error || "Fetch failed.");
    }
  } catch (e) {
    alert("Network error: " + e.message);
  } finally {
    btn.disabled = false;
    lbl.style.display = "inline";
    spn.style.display = "none";
  }
}

/* ── Autocomplete ─────────────────────────────────────────── */
let acTimer = null;
const searchInput = document.getElementById("company-search");
const acList      = document.getElementById("autocomplete-list");

searchInput.addEventListener("input", () => {
  const q = searchInput.value.trim();
  if (!q) { acList.hidden = true; return; }
  clearTimeout(acTimer);
  acTimer = setTimeout(async () => {
    const res   = await fetch(`/api/companies/search?q=${encodeURIComponent(q)}`);
    const items = await res.json();
    if (!items.length) { acList.hidden = true; return; }
    acList.innerHTML = items.map(c => `
      <li data-symbol="${esc(c.symbol)}" data-name="${esc(c.company_name)}">
        <div class="ac-avatar">${esc(initials(c.company_name))}</div>
        <div>
          <div class="ac-symbol">${esc(c.symbol)}</div>
          <div class="ac-name">${esc(c.company_name)}</div>
        </div>
      </li>`).join("");
    acList.hidden = false;
  }, 220);
});

acList.addEventListener("click", e => {
  const li = e.target.closest("li");
  if (!li) return;
  searchInput.value = "";
  acList.hidden = true;
  openDetail(li.dataset.symbol, li.dataset.name);
});

document.addEventListener("click", e => {
  if (!e.target.closest(".search-wrap")) acList.hidden = true;
});

// Top nav search (desktop)
const searchInputTop = document.getElementById("company-search-top");
const acListTop      = document.getElementById("autocomplete-list-top");

if (searchInputTop) {
  searchInputTop.addEventListener("input", () => {
    const q = searchInputTop.value.trim();
    if (!q) { acListTop.hidden = true; return; }
    clearTimeout(acTimer);
    acTimer = setTimeout(async () => {
      const res   = await fetch(`/api/companies/search?q=${encodeURIComponent(q)}`);
      const items = await res.json();
      if (!items.length) { acListTop.hidden = true; return; }
      acListTop.innerHTML = items.map(c => `
        <li data-symbol="${esc(c.symbol)}" data-name="${esc(c.company_name)}">
          <div class="ac-avatar">${esc(initials(c.company_name))}</div>
          <div>
            <div class="ac-symbol">${esc(c.symbol)}</div>
            <div class="ac-name">${esc(c.company_name)}</div>
          </div>
        </li>`).join("");
      acListTop.hidden = false;
    }, 220);
  });

  acListTop.addEventListener("click", e => {
    const li = e.target.closest("li");
    if (!li) return;
    searchInputTop.value = "";
    acListTop.hidden = true;
    openDetail(li.dataset.symbol, li.dataset.name);
  });

  document.addEventListener("click", e => {
    if (!e.target.closest(".top-nav-search")) acListTop.hidden = true;
  });
}

/* ── Data loading ─────────────────────────────────────────── */
async function loadReleased() {
  const res  = await fetch("/api/released");
  const rows = await res.json();
  renderList(rows, "list-released", "empty-released", "released", "filing_date");
}

async function loadUpcoming() {
  const res  = await fetch("/api/upcoming");
  const rows = await res.json();
  renderList(rows, "list-upcoming", "empty-upcoming", "upcoming", "meeting_date");
}

async function init() {
  await Promise.all([loadReleased(), loadUpcoming()]);
  switchTab("upcoming");
}

/* ── Calendar ─────────────────────────────────────────────── */
let calYear  = null;
let calMonth = null;

function openCalendar() {
  const now = new Date();
  calYear  = calYear  || now.getFullYear();
  calMonth = calMonth || now.getMonth() + 1;
  showPage("page-calendar");
  renderCalendar(calYear, calMonth);
}

async function renderCalendar(year, month) {
  const MONTHS = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"];
  document.getElementById("cal-month-label").textContent = `${MONTHS[month-1]} ${year}`;

  const grid = document.getElementById("cal-grid");
  grid.innerHTML = `<div style="padding:40px 20px;text-align:center;color:var(--text-3)">Loading…</div>`;

  const res  = await fetch(`/api/calendar?year=${year}&month=${month}`);
  const data = await res.json();

  const today    = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;

  const firstDay    = new Date(year, month-1, 1).getDay();
  const daysInMonth = new Date(year, month, 0).getDate();
  const prevDays    = new Date(year, month-1, 0).getDate();

  let cells = [];
  for(let i = 0; i < firstDay; i++)
    cells.push({ day: prevDays - firstDay + 1 + i, other: true });
  for(let i = 1; i <= daysInMonth; i++)
    cells.push({ day: i, other: false });
  while(cells.length % 7 !== 0)
    cells.push({ day: cells.length - firstDay - daysInMonth + 1, other: true });

  grid.innerHTML = "";

  grid.innerHTML = "";

  cells.forEach(c => {
    const cell = document.createElement("div");
    const pad  = n => String(n).padStart(2, "0");
    const dateKey = `${year}-${pad(month)}-${pad(c.day)}`;
    const isToday  = !c.other && dateKey === todayStr;
    const isFuture = !c.other && dateKey > todayStr;

    cell.className = "cal-cell" + (c.other ? " cal-other" : "") + (isToday ? " cal-today" : "");

    const numEl = document.createElement("div");
    numEl.className = "cal-day-num";
    numEl.textContent = c.day;
    cell.appendChild(numEl);

    if (!c.other) {
      const ev = data[dateKey];
      if (ev) {
        const released = !isFuture ? (ev.released || []) : [];
        const upcoming = isFuture || isToday ? (ev.upcoming || []) : [];
        const all = [
          ...released.map(r => ({ ...r, kind: "released" })),
          ...upcoming.map(u => ({ ...u, kind: "upcoming" })),
        ];

        if (all.length > 0) {
          // ── Dots ──────────────────────────────────────────
          const dotsEl = document.createElement("div");
          dotsEl.className = "cal-dots";

          const relDots = released.map(r => {
            const cls = r.pat == null ? "cal-dot-yellow"
                      : r.pat >= 0   ? "cal-dot-green"
                      :                "cal-dot-red";
            return cls;
          });
          const upDots = upcoming.map(() => "cal-dot-blue");

          const buildDots = (dotClasses, container) => {
            const show = dotClasses.slice(0, 3);
            const more = dotClasses.length - show.length;
            const wrap = document.createElement("div");
            wrap.className = "cal-dot-group";
            show.forEach(cls => {
              const d = document.createElement("span");
              d.className = `cal-dot ${cls}`;
              wrap.appendChild(d);
            });
            if (more > 0) {
              const n = document.createElement("span");
              n.className = "cal-dot-more";
              n.textContent = `+${more}`;
              wrap.appendChild(n);
            }
            container.appendChild(wrap);
          };

          if (relDots.length) buildDots(relDots, dotsEl);
          if (upDots.length)  buildDots(upDots,  dotsEl);

          cell.appendChild(dotsEl);

          // ── Popup ─────────────────────────────────────────
          cell.addEventListener("click", () => openCalendarPopup(dateKey, released, upcoming, month, year));
        }
      }
    }

    grid.appendChild(cell);
  });
}

function openCalendarPopup(dateKey, released, upcoming, month, year) {
  // Remove any existing popup
  const existing = document.getElementById("cal-popup");
  if (existing) existing.remove();

  const MONTHS = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"];
  const day = parseInt(dateKey.split("-")[2]);

  const overlay = document.createElement("div");
  overlay.id = "cal-popup-overlay";
  overlay.addEventListener("click", e => {
    if (e.target === overlay) overlay.remove();
  });

  const popup = document.createElement("div");
  popup.id = "cal-popup";

  let html = `
    <div class="cal-popup-header">
      <div class="cal-popup-title">${day} ${MONTHS[month-1]} ${year}</div>
      <button class="cal-popup-close" onclick="document.getElementById('cal-popup-overlay').remove()">✕</button>
    </div>`;

  if (released.length) {
    html += `<div class="cal-popup-section">Results Out</div>`;
    released.forEach(r => {
      const cls   = r.pat == null ? "cal-dot-yellow" : r.pat >= 0 ? "cal-dot-green" : "cal-dot-red";
      const label = r.pat == null ? "No Data" : r.pat >= 0 ? "Profit" : "Loss";
      const color = r.pat == null ? "#B59A00" : r.pat >= 0 ? "#0F6E56" : "#A32D2D";
      html += `
        <div class="cal-popup-row" onclick="document.getElementById('cal-popup-overlay').remove(); openDetail('${esc(r.symbol)}', '${esc(r.company_name)}')">
          <span class="cal-dot ${cls}"></span>
          <div class="cal-popup-info">
            <div class="cal-popup-symbol">${esc(r.symbol)}</div>
            <div class="cal-popup-name">${esc(r.company_name)}</div>
          </div>
          <span class="cal-popup-label" style="color:${color}">${label}</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>`;
    });
  }

  if (upcoming.length) {
    html += `<div class="cal-popup-section">Upcoming</div>`;
    upcoming.forEach(u => {
      html += `
        <div class="cal-popup-row" onclick="document.getElementById('cal-popup-overlay').remove(); openDetail('${esc(u.symbol)}', '${esc(u.company_name)}')">
          <span class="cal-dot cal-dot-blue"></span>
          <div class="cal-popup-info">
            <div class="cal-popup-symbol">${esc(u.symbol)}</div>
            <div class="cal-popup-name">${esc(u.company_name)}</div>
          </div>
          <span class="cal-popup-label" style="color:#185FA5">Upcoming</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>`;
    });
  }

  popup.innerHTML = html;
  overlay.appendChild(popup);
  document.body.appendChild(overlay);
}

document.getElementById("cal-prev").addEventListener("click", () => {
  calMonth--;
  if (calMonth < 1) { calMonth = 12; calYear--; }
  renderCalendar(calYear, calMonth);
});

document.getElementById("cal-next").addEventListener("click", () => {
  calMonth++;
  if (calMonth > 12) { calMonth = 1; calYear++; }
  renderCalendar(calYear, calMonth);
});

init();