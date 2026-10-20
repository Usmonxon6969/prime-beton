/* receipts page */
var RS={no:null,rows:[{m:-1,p:-1,q:0,pr:0,t:''}],site:0,msg:null},RM=null,rCopy=null;
function blankMR(){return [{m:-1,p:-1,q:0,pr:0,t:''}]}
function cpMR(rows){return rows.map(function(r){return {m:r.m,p:r.p>=0?r.p:-1,q:r.q,pr:r.pr,t:''}})}
function resolveItem(name){var j=midx(name);if(j>-1)return {m:j,p:-1};var p=pidx(name);return p>-1?{m:-1,p:p}:{m:-1,p:-1}}
function mrHint(r){
  var h=[],it=rowItem(r);
  if(r.m>=0||r.p>=0)h.push(tf('sv_avail',{n:fmt(it?it.st[RS.site]:0)})+' '+rowUnit(r));
  if(r.q>0&&r.pr>0)h.push(fmt(r.q)+' '+rowUnit(r)+' × '+money(r.pr)+' = '+money(r.q*r.pr)+' '+t('cur'));
  return h.join(' · ');
}
function mrowsHtml(){
  return RS.rows.map(function(r,i){
    return '<div class="srow"><input id="rcm'+i+'" data-i="'+i+'" data-k="m" type="text" data-pick="item" role="combobox" aria-autocomplete="list" autocomplete="off" spellcheck="false" placeholder="'+t('rc_item_ph')+'" aria-label="'+t('rc_items')+'" value="'+esc((r.m>=0||r.p>=0)?rowName(r):(r.t||''))+'">'+
     '<input id="rcq'+i+'" data-i="'+i+'" data-k="q" type="number" min="1" step="1" inputmode="numeric" placeholder="'+t('p_qty')+'" aria-label="'+t('p_qty')+'" value="'+(r.q>0?r.q:'')+'">'+
     '<input id="rcr'+i+'" data-i="'+i+'" data-k="pr" type="text" inputmode="decimal" autocomplete="off" placeholder="0,00" aria-label="'+t('c_price')+'" value="'+(r.pr>0?money(r.pr):'')+'">'+
     (RS.rows.length>1?'<button type="button" class="link" data-rm="'+i+'" aria-label="'+t('p_rm')+'">×</button>':'<span></span>')+
     '<span class="hint">'+mrHint(r)+'</span></div>';
  }).join('');
}
function rcUnitSuffix(rows){var s={};rows.forEach(function(r){if(r.m>=0||r.p>=0)s[rowUnit(r)]=1});var k=Object.keys(s);return k.length===1?' '+k[0]:''}
function updRcTotal(){$('#rctotal').textContent=t('p_total')+': '+fmt(rqty(RS.rows))+rcUnitSuffix(RS.rows)+' · '+money(rsum(RS.rows))+' '+t('cur')}
function renderMRows(){$('#rcrows').innerHTML=mrowsHtml();updRcTotal()}
function rerr(key,a){RS.msg=key?{key:key,a:a}:null;$('#rcerr').textContent=key?tf(key,a):''}
$('#rcrows').addEventListener('input',function(e){
  var el=e.target,kk=el.dataset.k;if(!kk)return;
  var i=+el.dataset.i,r=RS.rows[i];
  if(kk==='m'){var x=resolveItem(el.value);r.m=x.m;r.p=x.p;r.t=el.value}
  else if(kk==='pr'){moneyType(el);r.pr=parseMoney(el.value)}
  else{var v=parseFloat(el.value);v=v>0?v:0;r.q=Math.floor(v)}
  var h=$('#rcrows').children[i].querySelector('.hint');if(h)h.textContent=mrHint(r);
  updRcTotal();rerr(null);
});
$('#rcrows').addEventListener('click',function(e){
  var b=e.target.closest('[data-rm]');if(!b)return;
  if(RS.rows.length>1){RS.rows.splice(+b.dataset.rm,1);renderMRows()}
});
$('#rcadd').addEventListener('click',function(){RS.rows.push({m:-1,p:-1,q:0,pr:0,t:''});renderMRows();var l=$('#rcm'+(RS.rows.length-1));if(l)l.focus()});
function renderRecs(){
  closeMenu();
  $('#rcq').placeholder=t('p_search');$('#rcq').setAttribute('aria-label',t('p_search'));
  var q=($('#rcq').value||'').trim().toLowerCase();
  var list=REC.filter(function(v){return !q||(v.no+' '+SUP[v.sup].n+' '+v.rows.map(rowName).join(' ')).toLowerCase().indexOf(q)>-1});
  var head='<thead><tr><th>'+t('c_no')+'</th><th>'+t('c_dt')+'</th><th>'+t('c_sup')+'</th><th>'+t('rc_items')+'</th><th>'+t('c_wh')+'</th><th class="num">'+t('c_sum')+'</th><th>'+t('c_status')+'</th><th><span class="vh">'+t('m_actions')+'</span></th></tr></thead>';
  var body=list.length?list.map(function(v){
    return '<tr class="'+(v.status==='deleted'?'is-deleted':'')+'"><td class="mono">'+v.no+'</td><td class="mono">'+dtf(v.date)+'</td><td>'+esc(SUP[v.sup].n)+'</td><td class="wrap">'+esc(v.rows.map(function(r){return rowName(r)+' × '+fmt(r.q)}).join(', '))+'</td><td>'+esc(WH[v.site])+'</td><td class="num">'+money(rsum(v.rows))+'</td><td>'+pill(v.status)+'</td><td class="act">'+kebabHtml('rc',v.no,v.no)+'</td></tr>';
  }).join(''):'<tr><td class="empty" colspan="8">'+t('em_doc')+'</td></tr>';
  $('#rctbl').innerHTML=head+'<tbody>'+body+'</tbody>';
  renderMsgEl('#rcmsg',RM);
}
function renderRcEd(){
  var sel=$('#rcsite');
  sel.innerHTML=whIdx().map(function(i){return '<option value="'+i+'">'+esc(WH[i])+'</option>'}).join('');
  if(WHGONE[RS.site])RS.site=whIdx()[0]||0;
  sel.value=String(RS.site);
  $('#rctitle').textContent=RS.no?tf('rc_edit_h',{s:RS.no}):t('rc_new_h');
  renderMRows();rerr(RS.msg&&RS.msg.key,RS.msg&&RS.msg.a);
}
function newRec(){
  var c=rCopy;rCopy=null;RS.no=null;RS.msg=null;
  RS.rows=c?cpMR(c.rows):blankMR();RS.site=c&&!WHGONE[c.site]?c.site:(whIdx()[0]||0);
  $('#rcdate').value=toLocal(new Date());$('#rcsup').value=c?SUP[c.sup].n:'';$('#rccom').value=c?(c.comment||''):'';
  renderRcEd();
}
function openRecEdit(no){
  var v=findR(no);if(!v||v.status==='deleted')return;
  RS.no=no;RS.msg=null;RS.rows=cpMR(v.rows);RS.site=v.site;
  $('#rcdate').value=toLocal(v.date);$('#rcsup').value=SUP[v.sup].n;$('#rccom').value=v.comment||'';
  renderRcEd();location.hash='receipt-edit';
}
function postRec(){
  var dt=new Date($('#rcdate').value),s=sidx($('#rcsup').value);
  if(isNaN(dt.getTime())){rerr('err_date');return}
  if(s<0){rerr('rc_err_sup');return}
  if(RS.rows.some(function(r){return r.m<0&&r.p<0})){rerr('rc_err_mat');return}
  if(!RS.rows.every(function(r){return r.q>0})){rerr('err_qty');return}
  if(!RS.rows.every(function(r){return r.pr>0})){rerr('err_price');return}
  var v=RS.no?findR(RS.no):null;
  var body={date:isoLocal(dt),supplier_id:SUP[s].id,warehouse_id:WHID[RS.site],comment:$('#rccom').value,
    rows:RS.rows.map(function(r){return {item_id:r.m>=0?MATID[r.m]:PRID[r.p],qty:r.q,price:r.pr}})};
  srv(v?api('PUT','/receipts/'+v.id,body):api('POST','/receipts',body),function(r){
    RM={key:v?'rc_saved':'rc_posted',m:r.number};RS.no=null;Tabs.done();location.hash=takeRet('receipts');
  },function(e){rerr('api_raw',{m:apiErr(e)})});
}
function delRec(no){
  var v=findR(no);if(v.status!=='posted')return;
  srv(api('DELETE','/receipts/'+v.id),function(){RM={key:'rc_deleted',m:no};renderRecs()},function(e){RM=apiMsg(e);renderRecs()});
}
function resRec(no){
  var v=findR(no);if(v.status!=='deleted')return;
  srv(api('POST','/receipts/'+v.id+'/restore'),function(){RM={key:'rc_restored',m:no};renderRecs()},function(e){RM=apiMsg(e);renderRecs()});
}
$('#rcsave').addEventListener('click',postRec);
$('#rcq').addEventListener('input',renderRecs);
$('#rctbl').addEventListener('click',kebabClick);
$('#rcsite').addEventListener('change',function(){RS.site=+this.value;renderMRows()});
MENUS.rc={
  html:function(no){
    var v=findR(no),dead=v.status==='deleted';
    return (dead?'':mi('edit',ICO.edit,t('m_edit')))+mi('copy',ICO.copy,t('m_copy'))+(dead?mi('restore',ICO.restore,t('m_restore')):mi('del',ICO.del,t('m_del'),'del'));
  },
  q:function(){return t('rc_del_q')},
  act:function(a,no){
    if(a==='edit')openRecEdit(no);
    else if(a==='copy'){rCopy=findR(no);location.hash='receipt-new'}
    else if(a==='confirmdel')delRec(no);
    else if(a==='restore')resRec(no);
  }
};
function renderPur(){renderSup();renderRecs();renderRcEd()}
$('#rcsup').setAttribute('data-pick','sup');
