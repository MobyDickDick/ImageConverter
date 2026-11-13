'use strict';
const $=id=>document.getElementById(id);
let collection=null, busy=false, lastPayload='';
function node(tag,text,cls){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el;}
async function api(path,body){const response=await fetch(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-ImageConverter':'1'},body:JSON.stringify(body)});const value=await response.json();if(!response.ok)throw new Error(value.error||'Die Anfrage ist fehlgeschlagen.');return value;}
function notice(error){$('notice').textContent=error?.message||'';$('notice').hidden=!error;}
function jobLink(text,id){const a=node('a',text);a.href=`/?job=${encodeURIComponent(id)}`;return a;}
function button(text,action,primary=false){const b=node('button',text,primary?'primary':'secondary');b.type='button';b.disabled=busy;b.onclick=action;return b;}
async function openCase(id,fresh=false){if(busy)return;busy=true;render();notice();try{const job=await api(`/api/collection/${id}/load`,{fresh});window.location.assign(`/?job=${encodeURIComponent(job.id)}`);}catch(error){notice(error);busy=false;render();}}
async function planB(id){if(busy)return;busy=true;render();notice();try{const run=await api(`/api/jobs/${id}/workbench`,{});window.location.assign(`/workbench?run=${encodeURIComponent(run.id)}`);}catch(error){notice(error);busy=false;render();}}
function render(){
  if(!collection)return;
  const s=collection.summary;
  $('coverage').textContent=`${s.categories_with_saved_pass} von ${s.categories} Kategorien mit vorhandenem Rasterpass`;
  const missing=collection.cases.filter(c=>!c.category_saved_passes).map(c=>c.label);
  $('coverage-detail').textContent=`Bestandsbericht vom ${s.quality_snapshot?new Date(s.quality_snapshot).toLocaleString('de-CH'):'unbekannten Zeitpunkt'}. ${missing.length?'Noch ohne Beleg: '+missing.join(', ')+'.':'Für jede Kategorie ist ein gespeicherter Rasterpass vorhanden.'}`;
  $('progress').replaceChildren(node('strong',`${s.fresh_passes}/${s.categories}`),node('span','Beispiele in neuen Versuchen bestanden'),node('strong',`${s.prepared_plan_b}/${s.categories}`),node('span','erweiterte Plan-B-Aufgaben vorbereitet'));
  const filter=$('filter').value, fragment=document.createDocumentFragment();let count=0;
  for(const [index,c] of collection.cases.entries()){
    if((filter==='open'&&c.passed_job)||(filter==='passed'&&!c.passed_job)||(filter==='plan-b'&&!c.plan_b_job))continue;
    count++;
    const card=node('section',undefined,'card case');card.id=c.id;card.append(node('h2',`${String(index+1).padStart(2,'0')} · ${c.label}`),node('div',c.filename,'filename'));
    const pictures=node('div',undefined,'case-images');
    for(const [title,path] of [['Original',c.image],['Gespeichertes SVG',c.saved_svg]]){if(!path)continue;const figure=node('figure'),img=node('img');img.src='/api/catalog/asset?path='+encodeURIComponent(path);img.alt=`${title} ${c.filename}`;img.loading='lazy';figure.append(img,node('figcaption',title));pictures.append(figure);}
    card.append(pictures,node('p',c.observation,'observation'));
    card.append(node('p',`${c.category_saved_passes} von ${c.category_size} Bildern dieser Kategorie haben im Bestandsbericht einen Rasterpass. Gewähltes Beispiel: ${c.selected_saved_pass?'gespeicherter Rasterpass':'noch kein gespeicherter Rasterpass'}.`,'evidence'+(c.category_saved_passes?'':' warning')));
    if(c.selection_note)card.append(node('p',c.selection_note,'hint'));
    const j=c.latest_job;
    const states={ready:'Geladen – noch nicht gestartet',running:'Konvertierung läuft',done:'Abgeschlossen',error:'Ausführungsfehler',timeout:'Zeitlimit erreicht',cancelled:'Abgebrochen',interrupted:'Unterbrochen'};
    card.append(node('p',!j?'Neuer Versuch: noch nicht gestartet.':`Letzter Versuch: ${states[j.status]||j.status}${j.result?' · '+(j.quality==='passed'?'Qualitätsprüfung bestanden':'SVG-Entwurf, Qualitätsprüfung offen'):''}.`,'attempt'));
    if(c.passed_job)card.append(node('p','Ein neuer Versuch dieses Beispiels hat die Qualitätsprüfung bestanden.','hint'));
    if(c.problem)card.append(node('p',c.problem,'evidence warning'));
    const description=node('details');description.append(node('summary','Geladene Bildbeschreibung'),node('p',c.description||'Keine Beschreibung vorhanden. Bitte im Konverter ergänzen.'));card.append(description);
    const actions=node('div',undefined,'actions');
    const load=button(j?'Weiteren Versuch vorbereiten':'Zur Konvertierung laden',()=>openCase(c.id,Boolean(j)),true);load.disabled=busy||!c.available||j?.status==='running';actions.append(load);
    if(j)actions.append(jobLink(j.status==='running'?'Laufenden Versuch öffnen':'Letzten Versuch öffnen',j.id));
    if(c.plan_b_job){const a=node('a','Plan-B-Aufgabe öffnen');a.href=`/workbench?run=${encodeURIComponent(c.plan_b_job.workbench_id)}`;actions.append(a);}
    if(c.passed_job&&!c.passed_job.workbench_id){const b=button('Erweiterte Plan-B-Aufgabe erstellen',()=>planB(c.passed_job.id));b.disabled=busy||!c.available;actions.append(b);}
    card.append(actions);fragment.append(card);
  }
  $('cases').replaceChildren(fragment);$('empty').hidden=count>0;$('refresh').disabled=busy;
}
async function load(force=false){try{const value=await api('/api/collection'),key=JSON.stringify(value);collection=value;notice();if(force||key!==lastPayload){lastPayload=key;render();}}catch(error){notice(error);}}
$('filter').onchange=render;$('refresh').onclick=()=>load(true);
load().then(()=>{const focus=new URLSearchParams(location.search).get('focus');if(focus)document.getElementById(focus)?.scrollIntoView({block:'start'});});
setInterval(()=>{if(!busy&&!document.hidden)load();},5000);
