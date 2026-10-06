/* Brofind Control Cockpit — interazioni dell'interfaccia V1. */

// ------------------------------------------------------------------ feedback

function showToast(message, type = 'success') {
  const t = document.getElementById('toast');
  if (!t || !message) return;
  t.textContent = message;
  t.className = `toast visible ${type}`;
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => t.classList.remove('visible'), 4200);
}

function flash(message, type = 'success') {
  try { sessionStorage.setItem('cockpitFlash', JSON.stringify({ message, type })); } catch (_) { /* storage non disponibile */ }
}

function reloadWith(message, type = 'success', target = null) {
  flash(message, type);
  if (target) {
    const url = new URL(target, location.href);
    if (url.pathname === location.pathname) { location.hash = url.hash; location.reload(); }
    else location.href = url.href;
  } else {
    location.reload();
  }
}

async function postForm(url, data) {
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams(data),
  });
}

async function readResponse(r) {
  let data = {};
  try { data = await r.json(); } catch (_) { data = { message: 'Risposta non leggibile dal server.' }; }
  if (!r.ok) throw new Error(data.detail || data.message || `Errore HTTP ${r.status}`);
  return data;
}

function projectCode() {
  return document.getElementById('projectHeader')?.dataset.projectCode || null;
}

// ------------------------------------------------------------------- drawer

function openDrawer(name) {
  closeMenus();
  document.querySelectorAll('.drawer.open').forEach(d => { d.classList.remove('open'); d.setAttribute('aria-hidden', 'true'); });
  const drawer = document.getElementById(`drawer-${name}`);
  if (!drawer) return;
  drawer.classList.add('open');
  drawer.setAttribute('aria-hidden', 'false');
  document.getElementById('drawerBackdrop')?.classList.add('open');
}

function closeDrawers() {
  document.querySelectorAll('.drawer.open').forEach(d => { d.classList.remove('open'); d.setAttribute('aria-hidden', 'true'); });
  document.getElementById('drawerBackdrop')?.classList.remove('open');
  if (location.hash.startsWith('#drawer-')) history.replaceState(null, '', location.pathname + location.search);
}

function drawerTab(button) {
  const bar = button.closest('.drawer-tabs');
  const drawer = button.closest('.drawer');
  bar.querySelectorAll('button').forEach(b => b.classList.toggle('active', b === button));
  drawer.querySelectorAll('.drawer-pane').forEach(p => p.classList.toggle('active', p.id === button.dataset.pane));
}

function toggleMenu(id) {
  const menu = document.getElementById(id);
  if (!menu) return;
  const show = menu.style.display === 'none' || !menu.style.display;
  closeMenus();
  menu.style.display = show ? 'block' : 'none';
}

function closeMenus() {
  document.querySelectorAll('#projectMenu').forEach(m => { m.style.display = 'none'; });
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeDrawers(); closeMenus(); } });
document.addEventListener('click', e => {
  if (!e.target.closest('#projectMenu') && !e.target.closest('[onclick*="toggleMenu"]')) closeMenus();
});

// Ancore storiche (#sources-drawer, #ai-review…) e nuove (#drawer-*) aprono il drawer corrispondente.
const HASH_DRAWERS = {
  '#drawer-sources': 'sources', '#sources-drawer': 'sources', '#sources': 'sources',
  '#drawer-ai': 'ai', '#ai-review': 'ai', '#ai-analysis': 'ai',
  '#drawer-contract': 'contract', '#drawer-confidence': 'confidence',
};

// ------------------------------------------------------------------ tabelle

function filterTable(id, query) {
  const q = (query || '').toLowerCase();
  document.querySelectorAll(`#${id} tbody tr`).forEach(r => {
    r.hidden = q && !(r.dataset.search || r.textContent.toLowerCase()).includes(q);
  });
}

function toggleRows(group, trigger) {
  const rows = document.querySelectorAll(`tr[data-group="${group}"]`);
  const open = rows.length && rows[0].classList.contains('hidden');
  rows.forEach(r => r.classList.toggle('hidden', !open));
  trigger?.querySelector('.expander')?.classList.toggle('open', open);
}

// ---------------------------------------------------------------- portfolio

const PORTFOLIO_PAGE_SIZE = 10;
const portfolioState = { page: 1, sort: '', lifecycle: '' };

function portfolioRows() {
  return [...document.querySelectorAll('#portfolioTable tbody tr')];
}

function portfolioRender() {
  const tbody = document.querySelector('#portfolioTable tbody');
  if (!tbody) return;
  const q = (document.getElementById('portfolioSearch')?.value || '').toLowerCase();
  const owner = document.getElementById('portfolioOwner')?.value || '';
  const rows = portfolioRows();
  const key = portfolioState.sort;
  rows.sort((a, b) => {
    if (key) {
      const da = Number(a.dataset[`d${key[0].toUpperCase()}${key.slice(1)}`]);
      const db = Number(b.dataset[`d${key[0].toUpperCase()}${key.slice(1)}`]);
      if (da !== db) return da - db;
    }
    return Number(a.dataset.rank) - Number(b.dataset.rank);
  });
  rows.forEach(r => tbody.appendChild(r));
  const visible = rows.filter(r => {
    const okQ = !q || r.dataset.search.includes(q);
    const okOwner = !owner || r.dataset.owners.split('|').includes(owner);
    const okLife = !portfolioState.lifecycle || r.dataset.lifecycle === portfolioState.lifecycle;
    return okQ && okOwner && okLife;
  });
  const pages = Math.max(1, Math.ceil(visible.length / PORTFOLIO_PAGE_SIZE));
  portfolioState.page = Math.min(portfolioState.page, pages);
  const start = (portfolioState.page - 1) * PORTFOLIO_PAGE_SIZE;
  const shown = new Set(visible.slice(start, start + PORTFOLIO_PAGE_SIZE));
  rows.forEach(r => { r.hidden = !shown.has(r); });
  const count = document.getElementById('portfolioCount');
  if (count) count.textContent = `Mostra ${shown.size} di ${visible.length} commesse`;
  const pager = document.getElementById('portfolioPages');
  if (pager) {
    pager.innerHTML = '';
    for (let i = 1; i <= pages; i++) {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = i;
      b.className = i === portfolioState.page ? 'active' : '';
      b.onclick = () => { portfolioState.page = i; portfolioRender(); };
      pager.appendChild(b);
    }
  }
  document.querySelectorAll('#portfolioTable .sort-head').forEach(h => h.classList.toggle('sorted', h.dataset.sort === key));
}

function portfolioSort(key) {
  portfolioState.sort = portfolioState.sort === key ? '' : key;
  portfolioState.page = 1;
  portfolioRender();
}

function initPortfolio() {
  if (!document.getElementById('portfolioTable')) return;
  document.querySelectorAll('#portfolioTable tbody tr[data-href]').forEach(r => {
    r.addEventListener('click', () => { location.href = r.dataset.href; });
  });
  document.querySelectorAll('#lifecycleTabs button').forEach(b => {
    b.addEventListener('click', () => {
      document.querySelectorAll('#lifecycleTabs button').forEach(x => x.classList.toggle('active', x === b));
      portfolioState.lifecycle = b.dataset.lifecycle;
      portfolioState.page = 1;
      portfolioRender();
    });
  });
  portfolioRender();
}

function initActivityFilter() {
  const bar = document.getElementById('activityFilter');
  if (!bar) return;
  bar.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
    bar.querySelectorAll('button').forEach(x => x.classList.toggle('active', x === b));
    document.querySelectorAll('.activity[data-open]').forEach(a => {
      a.hidden = b.dataset.filter === 'open' && a.dataset.open !== 'yes';
    });
  }));
}

// ------------------------------------------------------- segnali → attività

async function createAction(alertId) {
  try {
    const data = await readResponse(await fetch(`/api/alerts/${alertId}/create-action`, { method: 'POST' }));
    reloadWith(data.message || 'Attività creata.', data.existing ? 'info' : 'success', `/project/${encodeURIComponent(projectCode())}/attivita#action-${data.action_id}`);
  } catch (e) { showToast(e.message, 'error'); }
}

async function actionCall(url, data, fallback, anchorId) {
  try {
    const res = await readResponse(await (data ? postForm(url, data) : fetch(url, { method: 'POST' })));
    reloadWith(res.message || fallback, 'success', anchorId ? `#action-${anchorId}` : null);
  } catch (e) { showToast(e.message, 'error'); }
}

function setActionStatus(id, status) { return actionCall(`/api/actions/${id}/status`, { status }, 'Stato attività aggiornato.', id); }

function reassignAction(id) {
  const owner = document.getElementById(`owner-${id}`)?.value;
  if (!owner) { showToast('Seleziona prima un responsabile.', 'error'); return; }
  return actionCall(`/api/actions/${id}/assign`, { owner }, 'Attività riassegnata.', id);
}

async function suggestActionMessage(id) {
  try {
    const data = await readResponse(await fetch(`/api/actions/${id}/suggest-message`));
    const area = document.getElementById(`message-${id}`);
    if (area) { area.value = data.text; area.focus(); }
    showToast(data.message, 'info');
  } catch (e) { showToast(e.message, 'error'); }
}

function messageText(id, emptyMessage) {
  const body = document.getElementById(`message-${id}`)?.value || '';
  if (!body.trim()) { showToast(emptyMessage, 'error'); return null; }
  return body;
}

function addActionMessage(id) {
  const body = messageText(id, 'Scrivi un messaggio oppure usa “Suggerisci un testo”.');
  if (body) return actionCall(`/api/actions/${id}/messages`, { body }, 'Messaggio aggiunto.', id);
}

async function registerOutboundMessage(id) {
  const body = messageText(id, 'Scrivi o prepara prima il testo da inviare.');
  if (!body) return;
  try {
    const data = await readResponse(await postForm(`/api/actions/${id}/outbound`, { body }));
    try { await navigator.clipboard.writeText(body); } catch (_) { /* appunti non disponibili */ }
    reloadWith(`${data.message} Testo copiato negli appunti quando consentito.`, 'success', `#action-${id}`);
  } catch (e) { showToast(e.message, 'error'); }
}

function submitActionResponse(id) {
  const body = messageText(id, 'Inserisci la risposta prima di sottoporla al richiedente.');
  if (body) return actionCall(`/api/actions/${id}/response`, { body }, 'Risposta registrata.', id);
}

function validateActionResponse(id) { return actionCall(`/api/actions/${id}/validate`, null, 'Attività chiusa.', null); }
function requestActionClarification(id) { return actionCall(`/api/actions/${id}/clarify`, null, 'Chiarimento richiesto.', id); }

// --------------------------------------------------------------- proposte AI

async function setFindingStatus(id, status) {
  try {
    const data = await readResponse(await postForm(`/api/findings/${id}/status`, { status }));
    reloadWith(data.message || 'Segnale aggiornato.', 'success', '#drawer-ai');
  } catch (e) { showToast(e.message, 'error'); }
}

async function applyFinding(id) {
  if (!confirm('Confermi di recepire questa informazione nel cockpit? Verrà applicata soltanto la conseguenza operativa descritta; le fonti ufficiali restano in sola lettura.')) return;
  try {
    const data = await readResponse(await fetch(`/api/findings/${id}/apply`, { method: 'POST' }));
    reloadWith(data.summary || 'Informazione recepita nel cockpit.', 'success', '#drawer-ai');
  } catch (e) { showToast(e.message, 'error'); }
}

async function runIntelligence(code) {
  try {
    const data = await readResponse(await fetch(`/api/projects/${encodeURIComponent(code)}/intelligence/analyze`, { method: 'POST' }));
    const msg = data.created > 0
      ? `${data.created} nuovi segnali trovati. ${data.updated} già conosciuti aggiornati.`
      : `Nessun nuovo segnale. ${data.updated} segnali già conosciuti ricontrollati.`;
    reloadWith(msg, data.created > 0 ? 'success' : 'info', '#drawer-ai');
  } catch (e) { showToast(e.message, 'error'); }
}

async function submitMailLab(event, code) {
  event.preventDefault();
  try {
    const r = await fetch(`/api/projects/${encodeURIComponent(code)}/communications/analyze`, { method: 'POST', body: new FormData(event.currentTarget) });
    const data = await readResponse(r);
    reloadWith(data.created > 0 ? `Mail analizzata: ${data.created} nuovi segnali da verificare.` : 'Mail analizzata: nessun nuovo segnale rilevato.', data.created > 0 ? 'success' : 'info', '#drawer-ai');
  } catch (e) { showToast(e.message, 'error'); }
}

// ------------------------------------------------- decisioni operative cockpit

async function setVdaSaving(code, vda, confirmed) {
  try {
    const data = await readResponse(await postForm(`/api/projects/${encodeURIComponent(code)}/vda/${encodeURIComponent(vda)}/saving`, { confirmed: String(confirmed) }));
    reloadWith(data.message);
  } catch (e) { showToast(e.message, 'error'); }
}

async function createConfidencePlan(code) {
  try {
    const data = await readResponse(await fetch(`/api/projects/${encodeURIComponent(code)}/confidence-plan`, { method: 'POST' }));
    reloadWith(data.message, 'success', `/project/${encodeURIComponent(code)}/attivita`);
  } catch (e) { showToast(e.message, 'error'); }
}

function openContractConditionDialog(key, title, value, note, source) {
  const dlg = document.getElementById('contractConditionDialog');
  if (!dlg) return;
  document.getElementById('contractConditionKey').value = key || '';
  document.getElementById('contractConditionTitle').textContent = title || 'Chiarisci condizione';
  document.getElementById('contractConditionValue').value = (value || '').startsWith('Da ') ? '' : (value || '');
  document.getElementById('contractConditionNote').value = note || '';
  document.getElementById('contractConditionSource').value = source || '';
  dlg.showModal();
}

async function saveContractCondition(event) {
  event.preventDefault();
  const code = projectCode();
  const key = document.getElementById('contractConditionKey').value;
  const payload = {
    value: document.getElementById('contractConditionValue').value,
    note: document.getElementById('contractConditionNote').value,
    source_ref: document.getElementById('contractConditionSource').value,
    freeze: 'true',
  };
  try {
    const data = await readResponse(await postForm(`/api/projects/${encodeURIComponent(code)}/contract-condition/${encodeURIComponent(key)}`, payload));
    reloadWith(data.message, 'success', '#drawer-contract');
  } catch (e) { showToast(e.message, 'error'); }
}

async function reopenContractCondition(code, key) {
  const reason = prompt('Perché vuoi riaprire questo chiarimento?');
  if (!reason?.trim()) return;
  try {
    const data = await readResponse(await postForm(`/api/projects/${encodeURIComponent(code)}/contract-condition/${encodeURIComponent(key)}/reopen`, { reason }));
    reloadWith(data.message, 'info', '#drawer-contract');
  } catch (e) { showToast(e.message, 'error'); }
}

async function createCommercialReview(code, requirementId) {
  try {
    const data = await readResponse(await fetch(`/api/projects/${encodeURIComponent(code)}/requirements/${requirementId}/create-commercial-review`, { method: 'POST' }));
    reloadWith(data.message, data.existing ? 'info' : 'success', `/project/${encodeURIComponent(code)}/attivita#action-${data.action_id}`);
  } catch (e) { showToast(e.message, 'error'); }
}

async function dismissPotentialFinding(code, requirementId) {
  if (!confirm('Scartare questo finding? La fonte resta invariata e il finding non produrrà effetti operativi.')) return;
  try {
    const data = await readResponse(await postForm(`/api/projects/${encodeURIComponent(code)}/requirements/${requirementId}/disposition`, { disposition: 'DISMISSED' }));
    reloadWith(data.message || 'Finding scartato.', 'success', '#drawer-contract');
  } catch (e) { showToast(e.message, 'error'); }
}

// --------------------------------------------------------------------- avvio

document.addEventListener('DOMContentLoaded', () => {
  initPortfolio();
  initActivityFilter();
  try {
    const pending = JSON.parse(sessionStorage.getItem('cockpitFlash') || 'null');
    if (pending) { sessionStorage.removeItem('cockpitFlash'); showToast(pending.message, pending.type); }
  } catch (_) { /* storage non disponibile */ }
  const drawer = HASH_DRAWERS[location.hash];
  if (drawer) openDrawer(drawer);
  if (location.hash.startsWith('#action-')) {
    const el = document.getElementById(location.hash.slice(1));
    if (el) { el.hidden = false; el.classList.add('focused'); el.scrollIntoView({ block: 'center' }); setTimeout(() => el.classList.remove('focused'), 2200); }
  }
});
