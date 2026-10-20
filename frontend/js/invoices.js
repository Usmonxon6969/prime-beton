/* delivery notes page */
function renderInvs(){
  closeMenu();
  $('#ivq').placeholder=t('p_search');$('#ivq').setAttribute('aria-label',t('p_search'));
  var q=($('#ivq').value||'').trim().toLowerCase();
  var list=INV.filter(function(v){return !q||(v.no+' '+CUS[v.cus].n+' '+v.ord).toLowerCase().indexOf(q)>-1});
  var head='<thead><tr><th>'+t('c_no')+'</th><th>'+t('c_dt')+'</th><th>'+t('c_cus')+'</th><th>'+t('c_order')+'</th><th>'+t('c_wh')+'</th><th class="num">'+t('c_sum')+'</th><th>'+t('c_status')+'</th><th><span class="vh">'+t('m_actions')+'</span></th></tr></thead>';
  var body=list.length?list.map(function(v){
    return '<tr class="'+(v.status==='deleted'?'is-deleted':'')+'"><td class="mono">'+v.no+'</td><td class="mono">'+dtf(v.date)+'</td><td>'+esc(CUS[v.cus].n)+'</td><td class="mono">'+(v.ord||'–')+'</td><td>'+esc(WH[v.site])+'</td><td class="num">'+money(rsum(v.rows))+'</td><td>'+pill(v.status)+'</td><td class="act">'+kebabHtml('iv',v.no,v.no)+'</td></tr>';
  }).join(''):'<tr><td class="empty" colspan="8">'+t('em_doc')+'</td></tr>';
  $('#ivtbl').innerHTML=head+'<tbody>'+body+'</tbody>';
  renderMsgEl('#ivmsg',IM);
  if(IM&&IM.pid&&!IM.err){var m=$('#ivmsg');m.insertAdjacentHTML('beforeend',' <button type="button" class="btn primary sm" id="ivmprint" style="margin-left:8px">'+t('iv_print')+'</button>')}
}
function printWaybill(id,no){openBlob('/reports/print/waybill/'+id+'.pdf',no+'.pdf')}
function fillIvTrans(){
  var d=[],v=[],sd={},sv={};
  INV.forEach(function(x){if(x.driver&&!sd[x.driver]){sd[x.driver]=1;d.push(x.driver)}if(x.vehicle&&!sv[x.vehicle]){sv[x.vehicle]=1;v.push(x.vehicle)}});
  $('#ivdrvl').innerHTML=d.slice(0,40).map(function(x){return '<option value="'+esc(x)+'">'}).join('');
  $('#ivvehl').innerHTML=v.slice(0,40).map(function(x){return '<option value="'+esc(x)+'">'}).join('');
}
function fillIvOrd(){
  var c=cidx($('#ivcus').value),h='<option value="">'+t('iv_none')+'</option>';
  ORD.forEach(function(o){
    var st=ordState(o);if(st==='deleted')return;
    if(o.no!==IS.ord&&(st==='shipped'||(c>-1&&o.cus!==c)))return;
    h+='<option value="'+o.no+'">'+o.no+' · '+esc(CUS[o.cus].n)+' · '+money(rsum(o.rows))+'</option>';
  });
  var s=$('#ivord');s.innerHTML=h;s.value=IS.ord||'';
}
function rowsFromOrder(o,except){
  var rem=ordRemain(o,except),rows=[];
  o.rows.forEach(function(r){if(rem[r.p]>0){rows.push({p:r.p,q:rem[r.p],pr:r.pr,t:''});delete rem[r.p]}});
  return rows.length?rows:blankSR();
}
function bestSite(rows){var a=whIdx();for(var k=0;k<a.length;k++){if(!invShort(a[k],rows))return a[k]}return a[0]||0}
function renderIvEd(){
  fillLists();fillIvOrd();fillIvTrans();
  var sel=$('#ivsite');sel.innerHTML=whIdx().map(function(i){return '<option value="'+i+'">'+esc(WH[i])+'</option>'}).join('');
  sel.value=String(IS.site);
  $('#ivtitle').textContent=IS.no?tf('iv_edit_h',{s:IS.no}):t('iv_new_h');
  renderSRows('iv');serr('iv',IS.msg&&IS.msg.key,IS.msg&&IS.msg.a);
}
function newInv(){
  var c=iCopy,po=iPendOrd;iCopy=null;iPendOrd=null;
  IS.no=null;IS.msg=null;IS.ord='';IS.site=0;IS.rows=blankSR();
  var cus='',cm='';
  if(c){IS.rows=cpRows(c.rows);IS.site=c.site;cus=CUS[c.cus].n;cm=c.comment||''}
  $('#ivdrv').value=c?(c.driver||''):'';$('#ivveh').value=c?(c.vehicle||''):'';
  try{$('#ivprint').checked=localStorage.getItem('daybook-iv-print')!=='0'}catch(e){}
  var o=po?findO(po):null;
  if(o&&o.status!=='deleted'){IS.ord=o.no;cus=CUS[o.cus].n;IS.rows=rowsFromOrder(o);IS.site=bestSite(IS.rows)}
  $('#ivdate').value=toLocal(new Date());$('#ivcus').value=cus;$('#ivcom').value=cm;$('#ivpay').value='';
  renderIvEd();
}
function openInvEdit(no){
  var v=findI(no);if(!v||v.status==='deleted')return;
  IS.no=no;IS.msg=null;IS.ord=v.ord;IS.site=v.site;IS.rows=cpRows(v.rows);
  $('#ivdate').value=toLocal(v.date);$('#ivcus').value=CUS[v.cus].n;$('#ivcom').value=v.comment||'';$('#ivpay').value=v.pay?toLocal(v.pay).slice(0,10):'';
  $('#ivdrv').value=v.driver||'';$('#ivveh').value=v.vehicle||'';
  renderIvEd();location.hash='invoice-edit';
}
function postInv(){
  var dt=new Date($('#ivdate').value),c=cidx($('#ivcus').value);
  if(isNaN(dt.getTime())){serr('iv','err_date');return}
  if(c<0){serr('iv','od_err_cus');return}
  if(!checkRows('iv'))return;
  var v=IS.no?findI(IS.no):null,o=IS.ord?findO(IS.ord):null;
  if(IS.ord&&(!o||o.status==='deleted')){serr('iv','iv_err_ordgone');return}
  var body={date:isoLocal(dt),customer_id:CUS[c].id,warehouse_id:WHID[IS.site],order_id:o?o.id:null,pay_due:$('#ivpay').value?$('#ivpay').value+'T00:00:00':null,comment:$('#ivcom').value,driver:$('#ivdrv').value.trim(),vehicle:$('#ivveh').value.trim(),
    rows:IS.rows.map(function(r){return {item_id:PRID[r.p],qty:r.q,price:r.pr}})};
  srv(v?api('PUT','/invoices/'+v.id,body):api('POST','/invoices',body),function(r){
    var pr=$('#ivprint').checked;try{localStorage.setItem('daybook-iv-print',pr?'1':'0')}catch(e){}
    IM={key:v?'iv_saved':'iv_posted',m:r.number,pid:r.id};IS.no=null;Tabs.done();location.hash=takeRet('invoices');
    if(pr)printWaybill(r.id,r.number);
  },function(e){serr('iv','api_raw',{m:apiErr(e)})});
}
function delInv(no){
  var v=findI(no);if(v.status!=='posted')return;
  srv(api('DELETE','/invoices/'+v.id),function(){IM={key:'iv_deleted',m:no};renderInvs()},function(e){IM=apiMsg(e);renderInvs()});
}
function resInv(no){
  var v=findI(no);if(v.status!=='deleted')return;
  srv(api('POST','/invoices/'+v.id+'/restore'),function(){IM={key:'iv_restored',m:no};renderInvs()},function(e){IM=apiMsg(e);renderInvs()});
}
function renderInvView(){
  var v=findI(IS.view);if(!v)return;
  var tot=rsum(v.rows),qty=rqty(v.rows);
  $('#ivvtitle').textContent=tf('iv_form',{s:v.no,d:dtf(v.date)});
  $('#ivvedit').hidden=v.status==='deleted';
  $('#ivdoc').innerHTML=
    (v.status==='deleted'?'<p>'+pill('deleted')+'</p>':'')+
    '<div class="kv"><span>'+t('c_wh')+'</span><b>'+esc(WH[v.site])+'</b></div>'+
    (v.driver?'<div class="kv"><span>'+t('iv_drv')+'</span><b>'+esc(v.driver)+'</b></div>':'')+(v.vehicle?'<div class="kv"><span>'+t('iv_veh')+'</span><b>'+esc(v.vehicle)+'</b></div>':'')+
    '<div class="kv"><span>'+t('iv_to')+'</span><b>'+esc(CUS[v.cus].n)+'</b></div>'+
    '<div class="kv"><span>'+t('c_order')+'</span><b>'+(v.ord||'–')+'</b></div>'+(v.pay?'<div class="kv"><span>'+t('iv_pay')+'</span><b>'+dfmt(v.pay)+'</b></div>':'')+
    '<div class="scroll"><table><thead><tr><th>№</th><th>'+t('c_prod')+'</th><th class="num">'+t('p_qty')+'</th><th class="num">'+t('c_price')+'</th><th class="num">'+t('c_sum')+'</th></tr></thead><tbody>'+
    v.rows.map(function(r,i){return '<tr><td>'+(i+1)+'</td><td>'+esc(PRODUCTS[r.p])+'</td><td class="num">'+fmt(r.q)+'</td><td class="num">'+money(r.pr)+'</td><td class="num">'+money(r.q*r.pr)+'</td></tr>'}).join('')+
    '<tr><td></td><td><b>'+t('c_total')+'</b></td><td class="num"><b>'+fmt(qty)+'</b></td><td></td><td class="num"><b>'+money(tot)+'</b></td></tr></tbody></table></div>'+
    (v.comment?'<p class="note">'+esc(v.comment)+'</p>':'')+
    '<div class="sig"><div>'+t('iv_gave')+'</div><div>'+t('iv_took')+'</div></div>';
}
$('#ivsave').addEventListener('click',postInv);
$('#ivq').addEventListener('input',renderInvs);
$('#ivtbl').addEventListener('click',kebabClick);
$('#ivcus').addEventListener('input',function(){fillIvOrd();if(IS.ord&&!$('#ivord').value)IS.ord=''});
$('#ivsite').addEventListener('change',function(){IS.site=+this.value;renderSRows('iv')});
$('#ivord').addEventListener('change',function(){
  IS.ord=this.value;serr('iv',null);
  if(IS.ord){var o=findO(IS.ord);$('#ivcus').value=CUS[o.cus].n;IS.rows=rowsFromOrder(o,IS.no);renderSRows('iv');fillIvOrd()}
});
$('#ivvedit').addEventListener('click',function(){openInvEdit(IS.view)});
$('#ivvwb').addEventListener('click',function(){var v=findI(IS.view);if(v)printWaybill(v.id,v.no)});
$('#ivmsg').addEventListener('click',function(e){if(e.target.id==='ivmprint'&&IM&&IM.pid)printWaybill(IM.pid,IM.m)});
MENUS.iv={
  html:function(no){
    var v=findI(no),dead=v.status==='deleted';
    return mi('view',ICO.spec,t('iv_view'))+mi('print',ICO.spec,t('iv_print'))+(dead?'':mi('edit',ICO.edit,t('m_edit')))+mi('copy',ICO.copy,t('m_copy'))+(dead?mi('restore',ICO.restore,t('m_restore')):mi('del',ICO.del,t('m_del'),'del'));
  },
  q:function(){return t('iv_del_q')},
  act:function(a,no){
    if(a==='view'){IS.view=no;location.hash='invoice-view'}
    else if(a==='print')printWaybill(findI(no).id,no);
    else if(a==='edit')openInvEdit(no);
    else if(a==='copy'){iCopy=findI(no);location.hash='invoice-new'}
    else if(a==='confirmdel')delInv(no);
    else if(a==='restore')resInv(no);
  }
};
