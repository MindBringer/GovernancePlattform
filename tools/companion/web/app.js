let runtime=null;
const output=document.getElementById('output');
const projectRenderers=new Map();
const loadedAssets=new Set();
const refreshTimers=new Map();
const viewMeta={
  dashboard:{title:'Dashboard',description:'Überblick über Entwicklungsstand, Runtimes, Release-Bereitschaft und den genau nächsten Arbeitsschritt.'},
  actions:{title:'Entwicklung',description:'Geprüfte Aktionen für Build, Qualität, Projektpflege und Release. Jede Ausgabe landet nachvollziehbar in der Konsole.'},
  console:{title:'Konsole',description:'Live-Status und vollständige Ausgabe laufender Aktionen. Ein Release bleibt serverseitig aktiv, auch wenn die Ansicht neu geladen wird.'}
};
const statusHelp={
  Projektversion:'Version, die der aktuelle Entwicklungsstand vorbereitet.',
  Framework:'Version des Project Engineering Frameworks.',
  Git:'Clean bedeutet: keine ungesicherten Änderungen im Arbeitsverzeichnis.',
  'Known Issues':'Dokumentierte, bewusst offene Einschränkungen.',
  Altlasten:'Erkannte Compatibility- und technische Schulden; Blocker verhindern den Release.',
  'Release-Gates':'Ergebnis der zuletzt gespeicherten Release-Prüfungen.',
  'Letzter Release':'Zuletzt veröffentlichte Produktversion und ihr Status.',
  'Release-Tag':'Tag, den der nächste vollständige Release erzeugt.',
  Produktruntime:'Erreichbare lokale Produktprozesse im Verhältnis zu allen registrierten Runtimes.'
};

function esc(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));}
function levelClass(level){return ['good','warn','danger','info'].includes(String(level||''))?String(level):'';}
function formatValue(value){if(value===null||value===undefined)return '–';if(typeof value==='object')return JSON.stringify(value);return String(value);}
function allViews(){return [...document.querySelectorAll('.view')];}
function viewElement(key){if(key==='dashboard')return document.getElementById('dashboard');if(key==='actions')return document.getElementById('actionsView');if(key==='console')return document.getElementById('consoleView');if(key.startsWith('project:'))return document.getElementById(`project-view-${key.slice(8)}`);return null;}

function show(view,title,description=''){allViews().forEach(v=>v.classList.remove('active'));const target=viewElement(view);if(target)target.classList.add('active');const meta=viewMeta[view]||{};document.getElementById('pageTitle').textContent=title||meta.title||view;document.getElementById('pageDescription').textContent=description||meta.description||'Projektbezogene Detailansicht.';document.querySelectorAll('.nav-btn').forEach(b=>b.classList.toggle('active',b.dataset.view===view));}
function badge(text,cls=''){return `<span class="badge ${esc(cls)}">${esc(text)}</span>`;}

window.ProjectCompanion={
  registerRenderer(id,renderer){if(typeof renderer!=='function')throw new Error(`Renderer ${id} muss eine Funktion sein`);projectRenderers.set(String(id),renderer);},
  runAction:(id)=>runAction(id),
  runRelease:null,
  showView:(view,title,description)=>show(view,title,description),
  escape:esc,
  getRuntime:()=>runtime
};

function projectViews(){return Array.isArray(runtime?.projectUI?.views)?runtime.projectUI.views:[];}

function ensureProjectViewContainers(){
  const host=document.getElementById('projectViews');
  const ids=new Set(projectViews().map(v=>v.id));
  [...host.children].forEach(child=>{const id=child.dataset.projectView;if(id&&!ids.has(id))child.remove();});
  projectViews().forEach(view=>{
    let section=document.getElementById(`project-view-${view.id}`);
    if(!section){section=document.createElement('section');section.id=`project-view-${view.id}`;section.className='view project-view';section.dataset.projectView=view.id;section.innerHTML='<div class="project-view-root"></div>';host.appendChild(section);}
  });
}

function renderNav(){
  const nav=document.getElementById('nav');
  const base=['dashboard','actions','console'];
  const baseHtml=base.map(id=>`<button class="nav-btn ${id==='dashboard'?'active':''}" data-view="${id}" title="${esc(viewMeta[id].description)}">${esc(viewMeta[id].title)}</button>`).join('');
  const project=projectViews();
  const projectHtml=project.length?`<div class="nav-section-label">Projekt</div>${project.map(v=>`<button class="nav-btn" data-view="project:${esc(v.id)}" title="${esc(v.description||v.title||v.label)}">${esc(v.label)}</button>`).join('')}`:'';
  nav.innerHTML=baseHtml+projectHtml;
  nav.querySelectorAll('button').forEach(b=>b.onclick=()=>{
    const key=b.dataset.view;
    if(key?.startsWith('project:')){const id=key.slice(8);const spec=projectViews().find(v=>v.id===id);show(key,spec?.title||spec?.label||id,spec?.description||'Projektbezogene Betriebs- und Statusansicht.');renderProjectView(id,'full');return;}
    show(key,viewMeta[key]?.title||b.textContent,viewMeta[key]?.description||'');
  });
}

function renderStatus(){
  const r=runtime.repository||{},s=runtime.state||{},p=runtime.project||{},debt=s.technicalDebt||{},verify=s.verification?.releaseGates||{},last=s.lastRelease||{},projectRuntimes=runtime.projectRuntimes?.runtimes||[];
  document.getElementById('projectName').textContent=p.name||'Projekt';document.getElementById('tagline').textContent=runtime.ui?.tagline||p.description||'';document.getElementById('frameworkBadge').textContent=`Framework ${runtime.frameworkVersion}`;document.getElementById('currentStage').textContent=s.currentStage||'Nicht dokumentiert';const next=typeof s.nextStep==='object'?s.nextStep?.description:s.nextStep;document.getElementById('nextStep').textContent=`Nächster Schritt: ${next||'nicht dokumentiert'}`;
  document.getElementById('repoBadges').innerHTML=[badge(r.branch||'kein Branch'),badge(`v${p.version||'?'}`),badge(r.dirty?'lokale Änderungen':'sauber',r.dirty?'warn':'good'),badge(r.ghAuthenticated?'gh auth ✓':'gh auth –',r.ghAuthenticated?'good':'')].join('');
  const cards=[['Projektversion',p.version||'?'],['Framework',runtime.frameworkVersion||'?'],['Git',r.dirty?'dirty':'clean'],['Known Issues',s.knownIssues??'?'],['Altlasten',debt.status?`${debt.status} · ${debt.findings??0}`:'nicht geprüft'],['Release-Gates',verify.status||'pending'],['Letzter Release',last.status?`${last.version||''} · ${last.status}`:'–'],['Release-Tag',runtime.release?.tag||'–']];
  if(projectRuntimes.length)cards.push(['Produktruntime',`${projectRuntimes.filter(x=>x.healthy).length}/${projectRuntimes.length} healthy`]);
  document.getElementById('statusCards').innerHTML=cards.map(([k,v])=>`<div class="card metric" title="${esc(statusHelp[k]||'Statusinformation aus dem Projektgedächtnis.')}"><span>${esc(k)}</span><strong>${esc(v)}</strong><small>${esc(statusHelp[k]||'Statusinformation aus dem Projektgedächtnis.')}</small></div>`).join('');
  const runtimeLinks=document.getElementById('projectRuntimeLinks');runtimeLinks.hidden=!projectRuntimes.length;runtimeLinks.innerHTML=projectRuntimes.map(x=>`<a class="runtime-link ${x.healthy?'good':'warn'}" href="${esc(x.url)}" target="_blank" rel="noreferrer"><strong>${esc(x.label)}</strong><span>${esc(x.healthy?'bereit':x.error||'nicht bereit')}</span></a>`).join('');
  const wizard=document.getElementById('firstRunCard');if(wizard)wizard.hidden=!(p.key==='project-template'&&runtime.ui?.firstRunWizard!==false);
}

function actionButton(a){const help=a.description||`${a.label||a.id} ausführen; die vollständige Ausgabe erscheint in der Konsole.`;return `<button data-action="${esc(a.id)}" class="${a.danger?'danger':''}" title="${esc(help)}" aria-label="${esc(`${a.label||a.id}: ${help}`)}">${esc(a.label)}</button>`;}
function renderActions(){
  const groups={};(runtime.actions||[]).forEach(a=>(groups[a.category]??=[]).push(a));
  document.getElementById('actionGroups').innerHTML=Object.entries(groups).map(([category,actions])=>`<div class="group"><section class="card"><div class="section-head"><div><p class="eyebrow">Capability</p><h2>${esc(category)}</h2></div></div><div class="action-grid">${actions.map(a=>`<div class="action-tile"><h3>${esc(a.label)}</h3><p>${esc(a.description||'')}</p>${actionButton(a)}</div>`).join('')}</div></section></div>`).join('');
  document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>runAction(b.dataset.action));
  const quickIds=['status','engineering-contract','build','technical-debt-review','project-memory-contract','release-artifacts','pp-build','provision-dryrun'];const quick=(runtime.actions||[]).filter(a=>quickIds.includes(a.id)).slice(0,8);if(runtime.release?.enabled)quick.push({id:'release',label:'Vollständiger Release',description:'Prüft alle Gates, überwacht PR und CI, merged nach main und veröffentlicht Tag sowie GitHub Release.',danger:true,requiresConfirmation:true});document.getElementById('quickActions').innerHTML=quick.map(actionButton).join('');document.querySelectorAll('#quickActions [data-action]').forEach(b=>b.onclick=()=>runAction(b.dataset.action));
}

function storedTheme(){try{return localStorage.getItem('companion-theme');}catch(_error){return null;}}
function resolvedTheme(preference){if(preference==='light'||preference==='dark')return preference;return window.matchMedia?.('(prefers-color-scheme: dark)').matches?'dark':'light';}
function applyTheme(preference=storedTheme()||'system'){
  const resolved=resolvedTheme(preference);document.documentElement.dataset.theme=resolved;document.documentElement.dataset.themePreference=preference;
  const button=document.getElementById('themeToggle');if(button){const next=resolved==='dark'?'Hellmodus':'Dunkelmodus';button.textContent=resolved==='dark'?'☀ Hell':'☾ Dunkel';button.title=`Aktiv: ${resolved==='dark'?'Dunkelmodus':'Hellmodus'}. Zu ${next} wechseln.`;button.setAttribute('aria-label',button.title);}
}
function toggleTheme(){const next=resolvedTheme(document.documentElement.dataset.themePreference)==='dark'?'light':'dark';try{localStorage.setItem('companion-theme',next);}catch(_error){}applyTheme(next);}

function renderProjectActions(ids){
  if(!Array.isArray(ids)||!ids.length)return '';
  const actions=ids.map(id=>(runtime.actions||[]).find(a=>a.id===id)).filter(Boolean);
  if(!actions.length)return '';
  return `<div class="project-actions">${actions.map(actionButton).join('')}</div>`;
}

function genericSection(section){
  const kind=String(section?.kind||'text');const title=section?.title?`<h3>${esc(section.title)}</h3>`:'';const description=section?.description?`<p class="muted">${esc(section.description)}</p>`:'';
  if(kind==='table'){
    const columns=Array.isArray(section.columns)?section.columns:[];const rows=Array.isArray(section.rows)?section.rows:[];
    return `<section class="project-section">${title}${description}<div class="table-wrap"><table><thead><tr>${columns.map(c=>`<th>${esc(c.label||c.key||'')}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${columns.map(c=>`<td>${esc(formatValue(row?.[c.key]))}</td>`).join('')}</tr>`).join('')}</tbody></table></div></section>`;
  }
  if(kind==='list'){
    const items=Array.isArray(section.items)?section.items:[];
    return `<section class="project-section">${title}${description}<div class="project-list">${items.map(item=>`<div class="project-list-row"><div><strong>${esc(item.label||'')}</strong>${item.detail?`<span>${esc(item.detail)}</span>`:''}</div><div>${item.level?badge(formatValue(item.value),levelClass(item.level)):`<strong>${esc(formatValue(item.value))}</strong>`}</div></div>`).join('')}</div></section>`;
  }
  return `<section class="project-section">${title}${description}<p>${esc(section?.text||'')}</p></section>`;
}

function renderGenericProjectView(root,spec,payload,mode){
  const status=payload?.status&&typeof payload.status==='object'?payload.status:null;
  const metrics=Array.isArray(payload?.metrics)?payload.metrics:[];
  const sections=Array.isArray(payload?.sections)?payload.sections:[];
  root.innerHTML=`<div class="project-view-head"><div><p class="eyebrow">Project Cockpit</p><h2>${esc(spec.title||spec.label)}</h2>${spec.description?`<p class="muted">${esc(spec.description)}</p>`:''}</div>${status?badge(status.label||'Status',levelClass(status.level)):''}</div>${status?.detail?`<p class="project-status-detail">${esc(status.detail)}</p>`:''}${metrics.length?`<div class="project-metric-grid">${metrics.map(m=>`<div class="card metric"><span>${esc(m.label||'')}</span><strong>${esc(formatValue(m.value))}</strong>${m.detail?`<small>${esc(m.detail)}</small>`:''}</div>`).join('')}</div>`:''}${renderProjectActions(payload?.actions)}${sections.map(genericSection).join('')}`;
  root.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>runAction(b.dataset.action));
  if(mode==='dashboard')root.classList.add('dashboard-extension');else root.classList.remove('dashboard-extension');
}

async function fetchProjectViewData(id){
  const response=await fetch(`/api/project-view/${encodeURIComponent(id)}`,{cache:'no-store'});const body=await response.json();if(!response.ok||!body.ok)throw new Error(body.error||`Project View ${id} konnte nicht geladen werden`);return body.data||{};
}

async function renderProjectView(id,mode='full'){
  const spec=projectViews().find(v=>v.id===id);if(!spec)return;
  const root=mode==='dashboard'?document.querySelector(`[data-dashboard-project-view="${CSS.escape(id)}"] .project-view-root`):document.querySelector(`#project-view-${CSS.escape(id)} .project-view-root`);
  if(!root)return;root.innerHTML='<div class="card muted">Lade Project View …</div>';
  try{
    const payload=await fetchProjectViewData(id);const renderer=spec.renderer==='custom'?projectRenderers.get(id):null;
    if(spec.renderer==='custom'&&!renderer)throw new Error(`Custom Renderer ${id} wurde nicht registriert`);
    if(renderer)await renderer(root,payload,{mode,spec,runtime,escape:esc,runAction:(actionId)=>runAction(actionId),refresh:()=>renderProjectView(id,mode)});else renderGenericProjectView(root,spec,payload,mode);
  }catch(error){root.innerHTML=`<div class="card project-error"><strong>Project View nicht verfügbar</strong><p>${esc(error)}</p></div>`;}
}

async function loadAsset(url,kind){
  if(!url||loadedAssets.has(url))return;loadedAssets.add(url);
  await new Promise((resolve,reject)=>{const el=document.createElement(kind==='css'?'link':'script');if(kind==='css'){el.rel='stylesheet';el.href=url;}else{el.src=url;el.defer=true;}el.onload=resolve;el.onerror=()=>reject(new Error(`Asset konnte nicht geladen werden: ${url}`));document.head.appendChild(el);});
}

async function loadProjectAssets(){
  for(const view of projectViews())if(view.stylesheet)await loadAsset(view.stylesheet,'css');
  for(const view of projectViews())if(view.script)await loadAsset(view.script,'js');
}

async function renderDashboardExtensions(){
  const host=document.getElementById('projectDashboardExtensions');const dashboardViews=projectViews().filter(v=>v.dashboard);host.innerHTML='';host.hidden=!dashboardViews.length;
  for(const view of dashboardViews){const section=document.createElement('section');section.className='card project-dashboard-card';section.dataset.dashboardProjectView=view.id;section.innerHTML='<div class="project-view-root"></div>';host.appendChild(section);await renderProjectView(view.id,'dashboard');}
}

function scheduleProjectRefresh(){
  refreshTimers.forEach(timer=>clearInterval(timer));refreshTimers.clear();
  projectViews().forEach(view=>{const seconds=Number(view.refreshSeconds||0);if(seconds<5)return;const timer=setInterval(()=>{if(view.dashboard)renderProjectView(view.id,'dashboard');const full=document.getElementById(`project-view-${view.id}`);if(full?.classList.contains('active'))renderProjectView(view.id,'full');},seconds*1000);refreshTimers.set(view.id,timer);});
}

async function setupProjectUI(){ensureProjectViewContainers();renderNav();await loadProjectAssets();await renderDashboardExtensions();scheduleProjectRefresh();}

async function runAction(id){
  if(id==='release'){
    const releaseHandler=window.ProjectCompanion?.runRelease;
    if(typeof releaseHandler==='function')return releaseHandler();
    show('console','Konsole');
    output.textContent='Release-Monitor wird noch geladen. Bitte in einem Moment erneut versuchen.';
    return;
  }
  const action=(runtime.actions||[]).find(x=>x.id===id);if(!action)return;let confirmation=null;if(action.requiresConfirmation){confirmation=prompt('Bestätigung erforderlich.\nBestätigungstext eingeben:');if(!confirmation)return;}
  show('console','Konsole');document.querySelectorAll('button').forEach(b=>b.disabled=true);output.textContent=`Starte ${action.label||id} …`;
  try{const res=await fetch(`/api/action/${id}`,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':runtime.csrf},body:JSON.stringify({confirmation})});const data=await res.json();output.textContent=`${data.ok?'OK':'FEHLER'} · Exit ${data.exitCode}\n${data.command||''}\n\n${data.output||''}`;}catch(e){output.textContent=`FEHLER\n${e}`;}finally{document.querySelectorAll('button').forEach(b=>b.disabled=false);await loadRuntime(false);}
}

async function initializeProject(event){event.preventDefault();const payload={name:document.getElementById('initName').value.trim(),key:document.getElementById('initKey').value.trim(),description:document.getElementById('initDescription').value.trim(),version:document.getElementById('initVersion').value.trim(),port:Number(document.getElementById('initPort').value),powerPlatform:document.getElementById('initPowerPlatform').checked,provisioning:document.getElementById('initProvisioning').checked};document.querySelectorAll('button').forEach(b=>b.disabled=true);show('console','Konsole');output.textContent='Initialisiere neues Projekt …';try{const res=await fetch('/api/init',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':runtime.csrf},body:JSON.stringify(payload)});const data=await res.json();output.textContent=`${data.ok?'OK':'FEHLER'} · Exit ${data.exitCode??(data.ok?0:1)}\n\n${data.output||data.error||''}`;if(data.ok)await loadRuntime(true);}catch(e){output.textContent=`FEHLER\n${e}`;}finally{document.querySelectorAll('button').forEach(b=>b.disabled=false);}}
async function loadMemory(){const r=await fetch('/api/project-memory',{cache:'no-store'});const d=await r.json();document.getElementById('memoryPreview').textContent=d.content||'Nicht verfügbar.';}
async function loadRuntime(full=true){const r=await fetch('/api/project',{cache:'no-store'});runtime=await r.json();renderStatus();renderActions();if(full){ensureProjectViewContainers();await setupProjectUI();document.title=`${runtime.project?.name||'Projekt'} Engineering Companion`;}else{renderNav();await renderDashboardExtensions();}}

applyTheme();
window.matchMedia?.('(prefers-color-scheme: dark)').addEventListener?.('change',()=>{if((storedTheme()||'system')==='system')applyTheme('system');});
document.getElementById('themeToggle').onclick=toggleTheme;document.getElementById('refresh').onclick=()=>loadRuntime(false);document.getElementById('loadMemory').onclick=loadMemory;document.getElementById('clearConsole').onclick=()=>output.textContent='Bereit.';document.getElementById('firstRunForm').onsubmit=initializeProject;loadRuntime(true).catch(e=>{output.textContent=`Initialisierung fehlgeschlagen:\n${e}`;show('console','Konsole');});
