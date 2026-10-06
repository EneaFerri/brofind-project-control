function filterRows(){
  const q=(document.getElementById('search')?.value||'').toLowerCase();
  const sales=document.getElementById('filterSales')?.value||'';
  const pm=document.getElementById('filterPm')?.value||'';
  const status=document.getElementById('filterStatus')?.value||'';
  const priority=document.getElementById('filterPriority')?.value||'';
  document.querySelectorAll('#portfolio tbody tr').forEach(r=>{
    const okQ=!q || r.dataset.search.toLowerCase().includes(q);
    const okSales=!sales || r.dataset.sales===sales;
    const okPm=!pm || r.dataset.pm===pm;
    const okStatus=!status || r.dataset.status===status;
    const okPriority=!priority || r.dataset.priority===priority;
    r.style.display=(okQ&&okSales&&okPm&&okStatus&&okPriority)?'':'none';
  });
}
function clearFilters(){
  ['search','filterSales','filterPm','filterStatus','filterPriority'].forEach(id=>{const e=document.getElementById(id);if(e)e.value=''});filterRows();
}
async function postForm(url,data){
  const body=new URLSearchParams(data);
  return fetch(url,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body});
}
async function readResponse(r){
  let data={};
  try{data=await r.json()}catch(_){data={message:'Risposta non leggibile dal server.'}}
  if(!r.ok) throw new Error(data.detail||data.message||`Errore HTTP ${r.status}`);
  return data;
}
function showToast(message,type='success'){
  const t=document.getElementById('toast');
  if(!t){ if(message) alert(message); return; }
  t.textContent=message;
  t.className=`toast visible ${type}`;
  clearTimeout(window.__toastTimer);
  window.__toastTimer=setTimeout(()=>t.classList.remove('visible'),3000);
}
function getProjectCode(){ return document.getElementById('projectHeroSnapshot')?.dataset.projectCode || null; }

async function refreshProjectUI(tab='actions', focus=null){
  const code=getProjectCode();
  if(!code) return;
  const r=await fetch(`/project/${encodeURIComponent(code)}`,{headers:{'X-Requested-With':'ProjectControl'}});
  if(!r.ok) throw new Error(`Non riesco ad aggiornare la schermata (${r.status}).`);
  const html=await r.text();
  const doc=new DOMParser().parseFromString(html,'text/html');
  ['projectHeroSnapshot','executiveSnapshot','projectDetailsSnapshot','workspaceDrawer','contractDrawer'].forEach(id=>{
    const current=document.getElementById(id); const fresh=doc.getElementById(id);
    if(current&&fresh) current.innerHTML=fresh.innerHTML;
  });
  filterVdaRows('relevant');
  if(tab) openWorkspace(tab);
  if(focus){
    setTimeout(()=>{
      let el=null;
      if(focus.type==='alert') el=document.querySelector(`[data-workspace-alert="${focus.id}"]`);
      if(focus.type==='finding') el=document.getElementById(`finding-${focus.id}`);
      if(focus.type==='action') el=document.getElementById(`action-${focus.id}`);
      if(focus.type==='source') el=findSourceElement(focus.ref);
      if(el){ el.scrollIntoView({behavior:'smooth',block:'center'}); el.classList.add('focused'); setTimeout(()=>el.classList.remove('focused'),1800); }
    },60);
  }
}


// --- Drawer leggeri per fonti e revisione AI ---
function closeUtilityDrawers(){
  ['sourceDrawer','aiReviewDrawer'].forEach(id=>{
    const el=document.getElementById(id); if(el){el.classList.remove('open');el.setAttribute('aria-hidden','true');}
  });
  document.getElementById('utilityBackdrop')?.classList.remove('open');
  if(!document.getElementById('workspaceDrawer')?.classList.contains('open') && !document.getElementById('contractDrawer')?.classList.contains('open')) document.body.classList.remove('workspace-open');
}
function openUtilityDrawer(id){
  closeWorkspace(); closeContractDrawer(); closeUtilityDrawers();
  const drawer=document.getElementById(id), backdrop=document.getElementById('utilityBackdrop');
  if(!drawer||!backdrop)return;
  drawer.classList.add('open');drawer.setAttribute('aria-hidden','false');backdrop.classList.add('open');document.body.classList.add('workspace-open');
}
function openSourceDrawer(){openUtilityDrawer('sourceDrawer')}
function closeSourceDrawer(){closeUtilityDrawers()}
function openAiReviewDrawer(){openUtilityDrawer('aiReviewDrawer')}
function closeAiReviewDrawer(){closeUtilityDrawers()}

// --- Workspace operativo ---
function openWorkspace(tab='actions', alertId=null){
  closeUtilityDrawers();
  const drawer=document.getElementById('workspaceDrawer');
  const backdrop=document.getElementById('workspaceBackdrop');
  if(!drawer||!backdrop)return;
  drawer.classList.add('open'); backdrop.classList.add('open'); drawer.setAttribute('aria-hidden','false');
  document.body.classList.add('workspace-open');
  switchWorkspaceTab(tab);
  if(alertId){
    setTimeout(()=>{
      const el=document.querySelector(`[data-workspace-alert="${alertId}"]`);
      if(el){el.scrollIntoView({behavior:'smooth',block:'center'});el.classList.add('focused');setTimeout(()=>el.classList.remove('focused'),1800)}
    },80);
  }
}
function closeWorkspace(){
  document.getElementById('workspaceDrawer')?.classList.remove('open');
  document.getElementById('workspaceBackdrop')?.classList.remove('open');
  document.getElementById('workspaceDrawer')?.setAttribute('aria-hidden','true');
  document.body.classList.remove('workspace-open');
}
function openContractDrawer(){
  closeUtilityDrawers();
  document.getElementById('contractDrawer')?.classList.add('open');
  document.getElementById('contractBackdrop')?.classList.add('open');
  document.getElementById('contractDrawer')?.setAttribute('aria-hidden','false');
  document.body.classList.add('workspace-open');
}
function closeContractDrawer(){
  document.getElementById('contractDrawer')?.classList.remove('open');
  document.getElementById('contractBackdrop')?.classList.remove('open');
  document.getElementById('contractDrawer')?.setAttribute('aria-hidden','true');
  if(!document.getElementById('workspaceDrawer')?.classList.contains('open')) document.body.classList.remove('workspace-open');
}
function switchWorkspaceTab(tab){
  document.querySelectorAll('.workspace-tabs button').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));
  document.querySelectorAll('.workspace-pane').forEach(p=>p.classList.toggle('active',p.dataset.pane===tab));
}
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeWorkspace();closeContractDrawer();closeUtilityDrawers();}});

function findSourceElement(ref){
  return [...document.querySelectorAll('[data-source-ref]')].find(el=>el.dataset.sourceRef===ref) || null;
}
function openEvidence(ref){
  closeContractDrawer();
  openWorkspace('evidence');
  setTimeout(()=>{
    const el=findSourceElement(ref);
    if(el){el.scrollIntoView({behavior:'smooth',block:'center'});el.classList.add('focused');setTimeout(()=>el.classList.remove('focused'),2200)}
    else showToast('La fonte è registrata ma non è ancora rappresentata in questa demo.','info');
  },80);
}
function focusAction(id){
  openWorkspace('actions');
  setTimeout(()=>{
    const el=document.getElementById(`action-${id}`);
    if(el){el.scrollIntoView({behavior:'smooth',block:'center'});el.classList.add('focused');setTimeout(()=>el.classList.remove('focused'),1800)}
  },80);
}

// --- Criticità -> attività ---
async function createAction(id){
  try{
    const data=await readResponse(await fetch(`/api/alerts/${id}/create-action`,{method:'POST'}));
    await refreshProjectUI('actions',{type:'action',id:data.action_id});
    showToast(data.message||'Attività creata.',data.existing?'info':'success');
  }catch(e){showToast(e.message,'error')}
}
async function setActionStatus(id,status){
  try{
    const data=await readResponse(await postForm(`/api/actions/${id}/status`,{status}));
    await refreshProjectUI('actions',{type:'action',id});
    showToast(data.message||'Stato attività aggiornato.','success');
  }catch(e){showToast(e.message,'error')}
}
async function reassignAction(id){
  const owner=document.getElementById(`owner-${id}`)?.value;
  if(!owner){showToast('Seleziona prima un responsabile.','error');return;}
  try{
    const data=await readResponse(await postForm(`/api/actions/${id}/assign`,{owner}));
    await refreshProjectUI('actions',{type:'action',id});
    showToast(data.message,'success');
  }catch(e){showToast(e.message,'error')}
}
async function suggestActionMessage(id){
  try{
    const data=await readResponse(await fetch(`/api/actions/${id}/suggest-message`));
    const area=document.getElementById(`message-${id}`);
    if(area){area.value=data.text;area.focus();}
    showToast(data.message,'info');
  }catch(e){showToast(e.message,'error')}
}
async function addActionMessage(id){
  const area=document.getElementById(`message-${id}`);
  const body=area?.value||'';
  if(!body.trim()){showToast('Scrivi un messaggio oppure usa “Suggerisci un testo”.','error');return;}
  try{
    const data=await readResponse(await postForm(`/api/actions/${id}/messages`,{body}));
    await refreshProjectUI('actions',{type:'action',id});
    showToast(data.message,'success');
  }catch(e){showToast(e.message,'error')}
}
async function registerOutboundMessage(id){
  const area=document.getElementById(`message-${id}`);
  const body=area?.value||'';
  if(!body.trim()){showToast('Scrivi o prepara prima il testo da inviare.','error');return;}
  try{
    const data=await readResponse(await postForm(`/api/actions/${id}/outbound`,{body}));
    try{await navigator.clipboard.writeText(body);}catch(_){/* clipboard non disponibile: il testo resta registrato */}
    await refreshProjectUI('actions',{type:'action',id});
    showToast((data.message||'Uscita manuale registrata.')+' Testo copiato negli appunti quando consentito.','success');
  }catch(e){showToast(e.message,'error')}
}

async function submitActionResponse(id){
  const area=document.getElementById(`message-${id}`);
  const body=area?.value||'';
  if(!body.trim()){showToast('Inserisci la risposta ricevuta prima di sottoporla a validazione.','error');return;}
  try{
    const data=await readResponse(await postForm(`/api/actions/${id}/response`,{body}));
    await refreshProjectUI('actions',{type:'action',id});
    showToast(data.message,'success');
  }catch(e){showToast(e.message,'error')}
}
async function validateActionResponse(id){
  try{
    const data=await readResponse(await fetch(`/api/actions/${id}/validate`,{method:'POST'}));
    await refreshProjectUI('actions');
    showToast(data.message,'success');
  }catch(e){showToast(e.message,'error')}
}
async function requestActionClarification(id){
  try{
    const data=await readResponse(await fetch(`/api/actions/${id}/clarify`,{method:'POST'}));
    await refreshProjectUI('actions',{type:'action',id});
    showToast(data.message,'info');
  }catch(e){showToast(e.message,'error')}
}

// Kept for API compatibility; deterministic alerts are not manually closed in the UI.
async function setAlertStatus(id,status){
  try{
    const data=await readResponse(await postForm(`/api/alerts/${id}/status`,{status}));
    await refreshProjectUI('actions',{type:'alert',id});
    showToast(data.message||'Criticità aggiornata.','success');
  }catch(e){showToast(e.message,'error')}
}

function focusDimension(dim){
  setTimeout(()=>{
    const rows=[...document.querySelectorAll('#principal-alerts .alert')];
    rows.forEach(x=>x.classList.remove('focused'));
    let targets=rows.filter(x=>x.dataset.dimension===dim);
    if(dim==='TECHNICAL')targets=rows.filter(x=>['TECHNICAL','PROJECT','COMMUNICATION'].includes(x.dataset.dimension));
    if(dim==='CONTRACT')targets=rows.filter(x=>['CONTRACT','COMMERCIAL'].includes(x.dataset.dimension));
    if(targets[0]){
      targets[0].scrollIntoView({behavior:'smooth',block:'center'});targets.forEach(x=>x.classList.add('focused'));setTimeout(()=>targets.forEach(x=>x.classList.remove('focused')),1800);
    }else showToast('Nessuna criticità aperta in quest’area.','info');
  },50)
}

// --- Segnali dalle comunicazioni ---
async function setFindingStatus(id,status){
  try{
    const data=await readResponse(await postForm(`/api/findings/${id}/status`,{status}));
    await refreshProjectUI('intelligence',{type:'finding',id});
    showToast(data.message||'Segnale aggiornato.','success');
  }catch(e){showToast(e.message,'error')}
}
async function applyFinding(id){
  if(!confirm('Confermi di recepire questa informazione nel cockpit? Verrà applicata soltanto la conseguenza operativa descritta; le fonti ufficiali restano in sola lettura.')) return;
  try{
    const data=await readResponse(await fetch(`/api/findings/${id}/apply`,{method:'POST'}));
    await refreshProjectUI('intelligence',{type:'finding',id});
    showToast((data.summary||'Informazione recepita nel cockpit.')+' Il riepilogo operativo è stato aggiornato.','success');
  }catch(e){showToast(e.message,'error')}
}
async function runIntelligence(code){
  try{
    const data=await readResponse(await fetch(`/api/projects/${code}/intelligence/analyze`,{method:'POST'}));
    await refreshProjectUI('intelligence');
    const msg=data.created>0 ? `${data.created} nuovi segnali trovati. ${data.updated} già conosciuti aggiornati.` : `Nessun nuovo segnale. ${data.updated} segnali già conosciuti sono stati ricontrollati.`;
    showToast(msg,data.created>0?'success':'info');
  }catch(e){showToast(e.message,'error')}
}
async function submitMailLab(event,code){
  event.preventDefault();
  const form=event.currentTarget;
  try{
    const r=await fetch(`/api/projects/${code}/communications/analyze`,{method:'POST',body:new FormData(form)});
    const data=await readResponse(r);
    document.getElementById('mailLab')?.close();
    await refreshProjectUI('intelligence');
    showToast(data.created>0 ? `Mail analizzata: ${data.created} nuovi segnali da verificare.` : 'Mail analizzata: nessun nuovo segnale rilevato.',data.created>0?'success':'info');
  }catch(e){showToast(e.message,'error')}
}

async function setVdaSaving(code,vda,confirmed){
  try{
    const data=await readResponse(await postForm(`/api/projects/${encodeURIComponent(code)}/vda/${encodeURIComponent(vda)}/saving`,{confirmed:String(confirmed)}));
    await refreshProjectUI(null);
    showToast(data.message,'success');
  }catch(e){showToast(e.message,'error')}
}

// --- V0.3.8: UX semplificata + procurement + saving operativo ---
function filterVdaRows(mode='relevant', trigger=null){
  const rows=[...document.querySelectorAll('#vdaControlTable tbody tr')];
  if(!rows.length) return;
  let visible=0;
  rows.forEach(r=>{
    const economic=r.dataset.economic||'neutral';
    const procurement=r.dataset.procurement||'unknown';
    const procurementRisk=r.dataset.procurementRisk||'none';
    const scope=r.dataset.scope==='yes';
    const usage=parseFloat(r.dataset.usage||'0');
    const zero=r.dataset.zero==='yes';
    const procurementWatch=['high','medium'].includes(procurementRisk) || ['not_started','open','in_progress_unknown'].includes(procurement);
    let show=true;
    if(mode==='relevant') show=!zero && (economic==='red' || economic==='amber' || scope || procurementWatch || procurement==='closed' || usage>=80);
    if(mode==='issues') show=economic==='red' || economic==='amber';
    if(mode==='open') show=procurementWatch;
    if(mode==='closed') show=procurement==='closed';
    if(mode==='scope') show=scope;
    if(mode==='all') show=true;
    r.hidden=!show;
    if(show) visible++;
  });
  document.querySelectorAll('.vda-filter').forEach(b=>b.classList.toggle('active',b.dataset.vdaFilter===mode));
  const count=document.getElementById('vdaFilterCount');
  if(count) count.textContent=`${visible} di ${rows.length} VdA`;
}

async function createConfidencePlan(code){
  try{
    const data=await readResponse(await fetch(`/api/projects/${encodeURIComponent(code)}/confidence-plan`,{method:'POST'}));
    await refreshProjectUI('confidence');
    showToast(data.message,'success');
  }catch(e){showToast(e.message,'error')}
}

function openContractConditionDialog(key,title,value,note,source){
  const dlg=document.getElementById('contractConditionDialog');
  if(!dlg) return;
  document.getElementById('contractConditionKey').value=key||'';
  document.getElementById('contractConditionTitle').textContent=title||'Chiarisci condizione';
  document.getElementById('contractConditionValue').value=(value||'').startsWith('Da ') ? '' : (value||'');
  document.getElementById('contractConditionNote').value=note||'';
  document.getElementById('contractConditionSource').value=source||'';
  dlg.showModal();
}
async function saveContractCondition(event){
  event.preventDefault();
  const code=getProjectCode();
  const key=document.getElementById('contractConditionKey').value;
  const value=document.getElementById('contractConditionValue').value;
  const note=document.getElementById('contractConditionNote').value;
  const source_ref=document.getElementById('contractConditionSource').value;
  try{
    const data=await readResponse(await postForm(`/api/projects/${encodeURIComponent(code)}/contract-condition/${encodeURIComponent(key)}`,{value,note,source_ref,freeze:'true'}));
    document.getElementById('contractConditionDialog')?.close();
    await refreshProjectUI(null);
    openContractDrawer();
    showToast(data.message,'success');
  }catch(e){showToast(e.message,'error')}
}
async function reopenContractCondition(code,key){
  const reason=prompt('Perché vuoi riaprire questo chiarimento?');
  if(!reason?.trim()) return;
  try{
    const data=await readResponse(await postForm(`/api/projects/${encodeURIComponent(code)}/contract-condition/${encodeURIComponent(key)}/reopen`,{reason}));
    await refreshProjectUI(null); openContractDrawer(); showToast(data.message,'info');
  }catch(e){showToast(e.message,'error')}
}
function focusFirstContractClarification(){
  const el=document.querySelector('#contractDrawer .contract-condition.to_clarify');
  if(el){el.scrollIntoView({behavior:'smooth',block:'center'});el.classList.add('focused');setTimeout(()=>el.classList.remove('focused'),1600);}
}
async function createCommercialReview(code,requirementId){
  try{
    const data=await readResponse(await fetch(`/api/projects/${encodeURIComponent(code)}/requirements/${requirementId}/create-commercial-review`,{method:'POST'}));
    closeContractDrawer();
    await refreshProjectUI('actions',{type:'action',id:data.action_id});
    showToast(data.message,data.existing?'info':'success');
  }catch(e){showToast(e.message,'error')}
}
async function dismissPotentialFinding(code,requirementId){
  if(!confirm('Scartare questo finding AI? La fonte resta invariata e il finding non produrrà effetti operativi.')) return;
  try{
    const data=await readResponse(await postForm(`/api/projects/${encodeURIComponent(code)}/requirements/${requirementId}/disposition`,{disposition:'DISMISSED'}));
    await refreshProjectUI(null); openContractDrawer(); showToast(data.message||'Finding scartato.','success');
  }catch(e){showToast(e.message,'error')}
}

document.addEventListener('DOMContentLoaded',()=>filterVdaRows('relevant'));


document.addEventListener('DOMContentLoaded',()=>{
  if(location.hash==='#sources-drawer') setTimeout(openSourceDrawer,40);
  if(location.hash==='#ai-review') setTimeout(openAiReviewDrawer,40);
});
