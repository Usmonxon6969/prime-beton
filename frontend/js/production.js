/* production */
var PRODUCTS=[],NORMS=[],PGONE=[],MATS=[];
function pidx(n){n=String(n).trim();var i=PRODUCTS.indexOf(n);if(i<0||PGONE[i])i=PRODUCTS.indexOf(n.replace(/\./g,','));return i>-1&&!PGONE[i]?i:-1}
function mname(j){var m=MATS[j];return m.names?m.names[lang]:m.name}
function activeMats(){var a=[];MATS.forEach(function(m,j){if(!m.deleted)a.push(j)});return a}
var psite=0,mats=null,pmsg=null,pdone=null,justPosted=false,pcount=0,prevH='',editNo=null,pendingCopy=null,menuBtn=null,menuNo=null;
function blankRows(){return [{p:-1,q:0,s:0,t:''}]}
var WORKERS=[],pcrew=[];
var rows=blankRows();
function pad2(n){return String(n).padStart(2,'0')}
function dtf(d){return pad2(d.getDate())+'.'+pad2(d.getMonth()+1)+'.'+d.getFullYear()+' '+pad2(d.getHours())+':'+pad2(d.getMinutes())}
function toLocal(d){return d.getFullYear()+'-'+pad2(d.getMonth()+1)+'-'+pad2(d.getDate())+'T'+pad2(d.getHours())+':'+pad2(d.getMinutes())}
var plog=[];
function docItems(d){return d.rows.map(function(r){return PRODUCTS[r.p]+' × '+r.q+(r.s>0?' (+'+r.s+' '+t('p_scrap').toLowerCase()+')':'')}).join(', ')}
/* the "Items" cell of the log: one position per line, three lines at most; a click on the row opens the full table under it */
var PX={pos_more:['+%n more','+ещё %n','+yana %n'],pos_open:['Show all positions','Показать все позиции','Barcha pozitsiyalarni ko‘rsatish'],pos_scrap:['Scrap','Брак','Brak']};
Object.keys(PX).forEach(function(k){T.en[k]=PX[k][0];T.ru[k]=PX[k][1];T.uz[k]=PX[k][2]});
var pexp={};                                  // document numbers whose table is open
function posText(r){return PRODUCTS[r.p]+' × '+r.q+(r.s>0?' (+'+r.s+' '+t('pos_scrap').toLowerCase()+')':'')}
function docPos(d){
  var n=d.rows.length;
  var lines=d.rows.slice(0,3).map(function(r,i){
    var more=(i===2&&n>3)?'<span class="pos-more">'+esc(t('pos_more').replace('%n',n-3))+'</span>':'';
    return '<span class="pos-line">'+esc(posText(r))+more+'</span>';
  }).join('');
  return '<button type="button" class="pos-btn" data-pos="'+esc(d.no)+'" aria-expanded="'+(pexp[d.no]?'true':'false')+'" title="'+esc(t('pos_open'))+'">'+lines+'</button>';
}
function posTable(d){
  var q=0,s=0,rows=d.rows.map(function(r,i){q+=r.q;s+=r.s||0;return '<div role="row"><span role="cell" class="mono">'+(i+1)+'</span><span role="cell">'+esc(PRODUCTS[r.p])+'</span><span role="cell" class="num">'+fmt(r.q)+'</span><span role="cell" class="num">'+(r.s>0?fmt(r.s):'')+'</span></div>'}).join('');
  return '<div class="pos-table" role="table" aria-label="'+esc(t('c_items'))+'"><div role="row" class="ph"><span role="columnheader">№</span><span role="columnheader">'+t('c_items')+'</span><span role="columnheader" class="num">'+t('p_qty')+'</span><span role="columnheader" class="num">'+t('pos_scrap')+'</span></div>'+rows+
    '<div role="row" class="pt"><span role="cell"></span><span role="cell">'+t('c_total')+'</span><span role="cell" class="num">'+fmt(q)+'</span><span role="cell" class="num">'+(s?fmt(s):'')+'</span></div></div>';
}
function docTotal(d){return d.rows.reduce(function(s,r){return s+r.q},0)}
function findDoc(no){for(var i=0;i<plog.length;i++){if(plog[i].no===no)return plog[i]}return null}
function calcMats(rr){var m=MATS.map(function(){return 0});rr.forEach(function(r){if(r.q>0&&r.p>=0)NORMS[r.p].forEach(function(n,j){if(n)m[j]+=n*r.q})});return m}
var ICO={
  dots:'<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="3" r="1.5" fill="currentColor"/><circle cx="8" cy="8" r="1.5" fill="currentColor"/><circle cx="8" cy="13" r="1.5" fill="currentColor"/></svg>',
  edit:'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M10.8 2.7l2.5 2.5-7.9 7.9-3 .6.6-3z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>',
  copy:'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="5.5" y="5.5" width="8" height="8" rx="1.5" stroke="currentColor" stroke-width="1.4"/><path d="M10.5 3.5V3a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>',
  del:'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3 4.5h10M6.5 4.5V3a.8.8 0 0 1 .8-.8h1.4a.8.8 0 0 1 .8.8v1.5M4.5 4.5l.6 8.2a1 1 0 0 0 1 .9h3.8a1 1 0 0 0 1-.9l.6-8.2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
};
ICO.restore='<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3 8a5 5 0 1 0 1.7-3.8M3 2.5v3h3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';
function totalQty(){return rows.reduce(function(s,r){return s+((r.q>0||r.s>0)&&r.p>=0?(r.q||0)+(r.s||0):0)},0)}
function renderCrew(){
  var el=$('#pcrew');if(!el)return;
  el.innerHTML=WORKERS.length?WORKERS.map(function(w){return '<label class="chk"><input type="checkbox" data-w="'+w.id+'"'+(pcrew.indexOf(w.id)>-1?' checked':'')+'> '+esc(w.name)+'</label>'}).join(''):'<p class="note">'+t('p_crew_none')+'</p>';
}
function renderSteps(){
  var hasQty=rows.some(function(r){return r.q>0&&r.p>=0});
  var st=justPosted?[true,true,true,true]:[true,hasQty,mats!==null,false];
  $('#psteps').innerHTML=st.map(function(d,i){return '<span class="pst'+(d?' done':'')+'"><span class="ic">'+icon(d?'posted':'draft')+'</span>'+t('st'+(i+1))+'</span>'}).join('');
}
function renderKv(){
  $('#pkv').innerHTML='<div class="kv"><span>'+t('p_sub')+'</span><b>'+SITES[psite]+'</b></div><div class="kv"><span>'+t('p_wh')+'</span><b>'+SITES[psite]+'</b></div>';
}
function renderRows(){
  $('#prows').innerHTML=rows.map(function(r,i){
    return '<div class="prow"><input id="pr'+i+'" data-i="'+i+'" data-k="p" type="text" data-pick="prod" role="combobox" aria-autocomplete="list" autocomplete="off" spellcheck="false" placeholder="'+t('p_search')+'" aria-label="'+t('p_products')+'" value="'+(r.p>=0?PRODUCTS[r.p]:(r.t||'')).replace(/"/g,'&quot;').replace(/</g,'&lt;')+'">'+
      '<input id="pq'+i+'" data-i="'+i+'" data-k="q" type="number" min="0" step="1" inputmode="numeric" placeholder="'+t('p_qty')+'" aria-label="'+t('p_qty')+'" value="'+(r.q>0?r.q:'')+'">'+
      '<input id="ps'+i+'" data-i="'+i+'" data-k="s" type="number" min="0" step="1" inputmode="numeric" placeholder="'+t('p_scrap')+'" aria-label="'+t('p_scrap')+'" value="'+(r.s>0?r.s:'')+'">'+
      (rows.length>1?'<button type="button" class="link" data-rm="'+i+'" aria-label="'+t('p_rm')+'">×</button>':'<span></span>')+'</div>';
  }).join('');
}
function renderTotal(){$('#ptotal').textContent=t('p_total')+': '+fmt(totalQty())+' '+t('unit')}
function renderMats(){
  var el=$('#pmats');
  if(!mats){el.innerHTML='<p class="empty">'+t('p_empty_m')+'</p>';return}
  if(!mats.some(function(v){return v>0})){el.innerHTML='<p class="note">'+t('p_no_spec')+'</p>';return}
  var names=MATS.map(function(m,j){return mname(j)}),from=SITES[psite]+' / '+SITES[psite];
  el.innerHTML='<table><thead><tr><th>'+t('p_mat')+'</th><th>'+t('p_from')+'</th><th class="num">'+t('p_qty')+'</th></tr></thead><tbody>'+
    mats.map(function(v,j){return v>0?'<tr><td>'+names[j]+'</td><td>'+from+'</td><td class="num">'+fmt(v)+' '+matUnit(j)+'</td></tr>':''}).join('')+'</tbody></table><p class="note">'+t('p_norm_note')+'</p>';
}
function renderLog(){
  closeMenu();
  $('#plog').innerHTML='<thead><tr><th>'+t('c_no')+'</th><th>'+t('c_dt')+'</th><th>'+t('p_sub')+'</th><th>'+t('c_items')+'</th><th class="num">'+t('c_total')+'</th><th>'+t('c_status')+'</th><th><span class="vh">'+t('m_actions')+'</span></th></tr></thead><tbody>'+
    plog.map(function(x){return '<tr class="'+(x.status==='deleted'?'is-deleted':'')+(pexp[x.no]?' is-open':'')+'" data-no="'+esc(x.no)+'"><td class="mono">'+x.no+'</td><td class="mono">'+dtf(x.date)+'</td><td>'+SITES[x.site]+'</td><td class="wrap">'+docPos(x)+'</td><td class="num">'+fmt(docTotal(x))+'</td><td>'+pill(x.status)+'</td><td class="act"><button type="button" class="kebab" data-no="'+x.no+'" aria-haspopup="menu" aria-expanded="false" aria-label="'+t('m_actions')+' '+x.no+'">'+ICO.dots+'</button></td></tr>'+(pexp[x.no]?'<tr class="pos-detail"><td colspan="7">'+posTable(x)+'</td></tr>':'')}).join('')+'</tbody>';
}
$('#plog').addEventListener('click',function(e){           // a click anywhere on a row (not its menu) opens or closes its table of positions
  var tr=e.target.closest('tr[data-no]');
  if(!tr||e.target.closest('.act,.kebab,a'))return;
  var sel=window.getSelection&&String(window.getSelection());if(sel)return;       // the user is selecting text: leave it alone
  var no=tr.dataset.no,viaBtn=!!e.target.closest('.pos-btn');
  if(pexp[no])delete pexp[no];else pexp[no]=true;
  renderLog();
  if(viaBtn){var b=$('#plog [data-pos="'+no+'"]');if(b)b.focus()}
});
function renderMsg(){
  var e=$('#pmsg');
  if(pmsg){e.className='msg bad';e.textContent=t(pmsg.key).replace('%m',pmsg.m||'').replace('%w',pmsg.w||'')}else{e.className='msg';e.textContent=''}
  var pd=$('#pdone');
  if(pdone){pd.className='msg '+(pdone.err?'bad':'ok');pd.textContent=t(pdone.key).replace('%s',pdone.no||'').replace('%m',pdone.m||'').replace('%w',pdone.w||'')}else{pd.className='msg ok';pd.textContent=''}
}
function renderProd(){
  var s=$('#psite');
  if(!s.options.length)s.innerHTML=SITES.map(function(n,i){return '<option value="'+i+'">'+n+'</option>'}).join('');
  s.value=String(psite);
  var dl=$('#plist');dl.innerHTML=PRODUCTS.filter(function(n,i){return !PGONE[i]}).map(function(n){return '<option value="'+n+'"></option>'}).join('');
  if(!$('#pdt').value)$('#pdt').value=toLocal(new Date());
  $('#ptitle').textContent=editNo?t('p_edit_h').replace('%s',editNo):t('pdoc_h');
  renderSteps();renderKv();renderRows();renderCrew();renderTotal();renderMats();renderLog();renderMsg();
}
function newDoc(){
  editNo=null;pmsg=null;pdone=null;justPosted=false;
  var c=pendingCopy;pendingCopy=null;
  if(c){rows=c.rows.map(function(r){return {p:r.p,q:r.q,s:r.s||0,t:''}});pcrew=(c.crew||[]).slice();psite=c.site;$('#pcom').value=c.comment||'';mats=calcMats(rows)}
  else{rows=blankRows();pcrew=[];mats=null;$('#pcom').value=''}
  $('#pdt').value=toLocal(new Date());
  renderProd();
}
function openEdit(no){
  var d=findDoc(no);if(!d||d.status==='deleted')return;
  editNo=no;pmsg=null;pdone=null;justPosted=false;
  rows=d.rows.map(function(r){return {p:r.p,q:r.q,s:r.s||0,t:''}});pcrew=(d.crew||[]).slice();psite=d.site;
  $('#pcom').value=d.comment||'';$('#pdt').value=toLocal(d.date);mats=calcMats(rows);
  renderProd();
  location.hash='production-edit';
}
function copyDoc(no){var d=findDoc(no);if(!d)return;pendingCopy=d;location.hash='production-new'}
function touch(){justPosted=false;mats=null;pmsg=null;renderSteps();renderMats();renderMsg();renderTotal()}
function fillMats(){
  if(rows.some(function(r){return r.p<0})){pmsg={key:'err_prod'};renderMsg();return}
  if(!totalQty()){pmsg={key:'err_qty'};renderMsg();return}
  mats=calcMats(rows);justPosted=false;pmsg=null;renderSteps();renderMats();renderMsg();
}
function postDoc(){
  var dt=new Date($('#pdt').value);
  if(isNaN(dt.getTime())){pmsg={key:'err_date'};renderMsg();return}
  if(rows.some(function(r){return r.p<0})){pmsg={key:'err_prod'};renderMsg();return}
  if(!rows.every(function(r){return r.q>0||r.s>0})){pmsg={key:'err_qty'};renderMsg();return}
  if(!mats)mats=calcMats(rows);   // calculating materials is a preview, not a required step; products without a specification simply use no materials
  var body={date:isoLocal(dt),comment:$('#pcom').value,warehouse_id:WHID[psite],rows:rows.map(function(r){return {item_id:PRID[r.p],qty:r.q||0,scrap:r.s||0}}),worker_ids:pcrew.slice()};
  var d=editNo?findDoc(editNo):null,upd=d&&d.status==='posted';
  srv(upd?api('PUT','/production/'+d.id,body):api('POST','/production',body),function(r){
    pdone={key:upd?'saved_msg':'posted_msg',no:r.number};
    pmsg=null;mats=null;rows=blankRows();pcrew=[];justPosted=true;editNo=null;
    renderProd();
    Tabs.done();location.hash=takeRet('production');
  },function(e){pmsg=apiMsg(e);renderMsg()});
}
var menuKind='doc';
ICO.spec='<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M4 2.5h6l2.5 2.5v8.5H4z M6 8h4.5M6 10.5h4.5M6 5.5h2" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round"/></svg>';
