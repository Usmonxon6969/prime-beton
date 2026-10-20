/* orders page */
var OM=null,oCopy=null,iPendOrd=null,iCopy=null,IM=null;
function renderMsgEl(sel,m){var e=$(sel);if(!m){e.className='msg';e.textContent='';return}e.className='msg '+(m.err?'bad':'ok');e.textContent=tf(m.key,m)}
/* the "Items" cell: one position per line (three at most), a click on the row opens the whole order */
function ordPos(o){
  var n=o.rows.length;
  return o.rows.slice(0,3).map(function(r,i){
    var more=(i===2&&n>3)?'<span class="pos-more">'+esc(t('pos_more').replace('%n',n-3))+'</span>':'';
    return '<span class="pos-line">'+esc(PRODUCTS[r.p]+' × '+r.q)+more+'</span>';
  }).join('');
}
function renderOrders(){
  closeMenu();
  $('#odq').placeholder=t('p_search');$('#odq').setAttribute('aria-label',t('p_search'));
  var q=($('#odq').value||'').trim().toLowerCase();
  var list=ORD.filter(function(o){return !q||(o.no+' '+CUS[o.cus].n).toLowerCase().indexOf(q)>-1});
  var head='<thead><tr><th>'+t('c_no')+'</th><th>'+t('c_date')+'</th><th>'+t('c_cus')+'</th><th>'+t('c_items')+'</th><th class="num">'+t('c_sum')+'</th><th class="num">'+t('c_adv')+'</th><th class="num">'+t('c_ship')+'</th><th>'+t('c_status')+'</th><th><span class="vh">'+t('m_actions')+'</span></th></tr></thead>';
  var body=list.length?list.map(function(o){
    var st=ordState(o),x=ordShipped(o),s=OSL[st];
    return '<tr class="'+(st==='deleted'?'is-deleted':'ord-open')+'" data-no="'+esc(o.no)+'"><td class="mono">'+o.no+'</td><td class="mono">'+dfmt(o.date)+'</td><td>'+esc(CUS[o.cus].n)+'</td><td class="wrap">'+ordPos(o)+'</td><td class="num">'+money(rsum(o.rows))+'</td><td class="num">'+(o.adv>0?money(o.adv):'–')+'</td><td class="num">'+x[0]+' / '+x[1]+'</td><td>'+pill(s[0],s[1])+'</td><td class="act">'+kebabHtml('od',o.no,o.no)+'</td></tr>';
  }).join(''):'<tr><td class="empty" colspan="9">'+t('em_doc')+'</td></tr>';
  $('#odtbl').innerHTML=head+'<tbody>'+body+'</tbody>';
  renderMsgEl('#odmsg',OM);
}
function renderOdEd(){
  fillLists();
  $('#odtitle').textContent=OS.no?tf('od_edit_h',{s:OS.no}):t('od_new_h');
  renderSRows('od');serr('od',OS.msg&&OS.msg.key,OS.msg&&OS.msg.a);
}
function newOrder(){
  var c=oCopy;oCopy=null;OS.no=null;OS.msg=null;
  OS.rows=c?cpRows(c.rows):blankSR();
  $('#oddate').value=toDay(new Date());$('#oddue').value='';
  $('#odcus').value=c?CUS[c.cus].n:'';$('#odcom').value=c?(c.comment||''):'';
  renderOdEd();
}
function openOrdEdit(no){
  var o=findO(no);if(!o||o.status==='deleted')return;
  OS.no=no;OS.msg=null;OS.rows=cpRows(o.rows);
  $('#oddate').value=toDay(o.date);$('#oddue').value=o.due?toDay(o.due):'';$('#odcus').value=CUS[o.cus].n;$('#odcom').value=o.comment||'';
  renderOdEd();location.hash='order-edit';
}
function saveOrder(){
  var c=cidx($('#odcus').value),dt=pday($('#oddate').value),due=pday($('#oddue').value);
  if(!dt){serr('od','err_date');return}
  if(c<0){serr('od','od_err_cus');return}
  if(!checkRows('od'))return;
  var o=OS.no?findO(OS.no):null;
  var body={date:isoLocal(dt),due_date:due?isoLocal(due):null,customer_id:CUS[c].id,comment:$('#odcom').value,
    rows:OS.rows.map(function(r){return {item_id:PRID[r.p],qty:r.q,price:r.pr}})};
  srv(o?api('PUT','/orders/'+o.id,body):api('POST','/orders',body),function(r){
    OM={key:'od_saved',m:r.number};OS.no=null;Tabs.done();location.hash='orders';
  },function(e){serr('od','api_raw',{m:apiErr(e)})});
}
function delOrd(no){
  var o=findO(no);
  srv(api('DELETE','/orders/'+o.id),function(){OM={key:'od_deleted',m:no};renderOrders()},function(e){OM=apiMsg(e);renderOrders()});
}
function resOrd(no){
  var o=findO(no);
  srv(api('POST','/orders/'+o.id+'/restore'),function(){OM={key:'od_restored',m:no};renderOrders()},function(e){OM=apiMsg(e);renderOrders()});
}
$('#odsave').addEventListener('click',saveOrder);
$('#odq').addEventListener('input',renderOrders);
$('#odtbl').addEventListener('click',function(e){
  if(e.target.closest('.act,.kebab,a,button'))return kebabClick(e);
  var tr=e.target.closest('tr.ord-open');
  if(!tr)return kebabClick(e);
  var sel=window.getSelection&&String(window.getSelection());if(sel)return;      // the user is selecting text: leave it alone
  openOrdEdit(tr.dataset.no);
});
MENUS.od={
  html:function(no){
    var o=findO(no),dead=o.status==='deleted',st=ordState(o);
    return (dead?'':mi('edit',ICO.edit,t('m_edit')))+(dead||st==='shipped'?'':mi('inv',ICO.spec,t('m_invoice')))+mi('copy',ICO.copy,t('m_copy'))+(dead?mi('restore',ICO.restore,t('m_restore')):mi('del',ICO.del,t('m_del'),'del'));
  },
  q:function(){return t('od_del_q')},
  act:function(a,no){
    if(a==='edit')openOrdEdit(no);
    else if(a==='inv'){iPendOrd=no;location.hash='invoice-new'}
    else if(a==='copy'){oCopy=findO(no);location.hash='order-new'}
    else if(a==='confirmdel')delOrd(no);
    else if(a==='restore')resOrd(no);
  }
};

