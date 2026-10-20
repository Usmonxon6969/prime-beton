/* customers page */
var cform=null,cmsg=null;
function renderCuMsg(){var e=$('#cumsg');if(!cmsg){e.className='msg';e.textContent='';return}e.className='msg '+(cmsg.err?'bad':'ok');e.textContent=tf(cmsg.key,{m:cmsg.m})}
function renderCuForm(){
  var el=$('#cuform');
  if(!cform){el.hidden=true;el.innerHTML='';return}
  el.hidden=false;
  el.innerHTML='<h2>'+t(cform.i<0?'cu_new_h':'cu_edit_h')+'</h2><div class="fgrid">'+
    '<div class="field"><label for="cun">'+t('cu_name')+'</label><input id="cun" data-k="n" type="text" autocomplete="off" value="'+esc(cform.n)+'"></div>'+
    '<div class="field"><label for="cuph">'+t('cu_phone')+'</label><input id="cuph" data-k="ph" data-phone type="text" autocomplete="off" inputmode="tel" value="'+esc(cform.ph)+'"></div>'+
    '<div class="field"><label for="cuct">'+t('cu_contact')+'</label><input id="cuct" data-k="ct" type="text" autocomplete="off" value="'+esc(cform.ct)+'"></div>'+
    '<div class="field"><label for="cupd">'+t('cu_terms')+'</label><input id="cupd" data-k="pd" type="number" min="0" max="365" step="1" autocomplete="off" value="'+esc(cform.pd)+'"><span class="note">'+t('cu_terms_h')+'</span></div></div>'+
    '<div class="pbtns"><button type="button" class="btn primary sm" id="cusave">'+t('sp_save')+'</button><button type="button" class="btn ghost sm" id="cucancel">'+t('m_cancel')+'</button></div>'+
    '<p class="msg bad" id="cuferr" role="alert">'+(cform.err?t(cform.err).replace('%m',cform.errm||''):'')+'</p>';
}
function renderCus(){
  closeMenu();
  $('#cuq').placeholder=t('p_search');$('#cuq').setAttribute('aria-label',t('p_search'));
  var q=($('#cuq').value||'').trim().toLowerCase();
  var list=[];CUS.forEach(function(c,i){if(!c.gone&&(!q||(c.n+' '+c.ph+' '+c.ct).toLowerCase().indexOf(q)>-1))list.push(i)});
  var head='<thead><tr><th>'+t('cu_name')+'</th><th>'+t('cu_phone')+'</th><th>'+t('cu_contact')+'</th><th class="num">'+t('cu_orders')+'</th><th class="num">'+t('cu_sold')+'</th><th class="num">'+t('cu_debt')+'</th><th><span class="vh">'+t('m_actions')+'</span></th></tr></thead>';
  var body=list.length?list.map(function(i){
    var c=CUS[i],oc=ORD.filter(function(o){return o.cus===i&&o.status!=='deleted'}).length,
        sold=INV.reduce(function(s,v){return s+(v.cus===i&&v.status==='posted'?rsum(v.rows):0)},0),debt=custDebt(i),ag=custAging(i);
    return '<tr><td>'+esc(c.n)+(ag.overdue>0?flameHtml():'')+'</td><td class="mono">'+esc(c.ph||'–')+'</td><td>'+esc(c.ct||'–')+'</td><td class="num">'+oc+'</td><td class="num">'+(sold?money(sold):'–')+'</td><td class="num amt '+(debt>0?'out':debt<0?'in':'')+'">'+(debt===0?'–':(debt<0?'\u2212 ':'')+money(Math.abs(debt)))+'</td><td class="act">'+kebabHtml('cu',i,c.n)+'</td></tr>';
  }).join(''):'<tr><td class="empty" colspan="7">'+t('em_cus')+'</td></tr>';
  $('#cutbl').innerHTML=head+'<tbody>'+body+'</tbody>';
  renderCuForm();renderCuMsg();
}
function openCu(i){cmsg=null;cform=i===undefined?{i:-1,n:'',ph:'',ct:'',pd:0,err:null}:{i:i,n:CUS[i].n,ph:CUS[i].ph||'',ct:CUS[i].ct||'',pd:CUS[i].pd||0,err:null};renderCus();var f=$('#cun');if(f)f.focus()}
function saveCu(){
  var n=cform.n.trim().replace(/\s+/g,' ');
  if(!n){cform.err='mt_err_name';renderCuForm();return}
  var ex=cidx(n);if(ex>-1&&ex!==cform.i){cform.err='cu_err_dup';renderCuForm();return}
  var ph=Phone.out(cform.ph);if(ph===null){cform.err='ph_bad';renderCuForm();return}
  var pd=Math.max(0,Math.min(365,Math.round(+cform.pd)||0)),body={name:n,phone:ph,contact:cform.ct.trim(),pay_days:pd};
  srv(cform.i<0?api('POST','/customers',body):api('PUT','/customers/'+CUS[cform.i].id,body),function(){
    cmsg={key:'cu_saved',m:n};cform=null;$('#cuq').value='';renderCus();
  },function(e){cform.err='api_raw';cform.errm=apiErr(e);renderCuForm()});
}
function delCu(i){
  var n=CUS[i].n;
  srv(api('DELETE','/customers/'+CUS[i].id),function(){cmsg={key:'cu_deleted',m:n};renderCus()},
    function(e){cmsg={key:'api_raw',m:apiErr(e),err:true};renderCus()});
}
$('#cunew').addEventListener('click',function(){openCu()});
$('#cuq').addEventListener('input',renderCus);
$('#cuform').addEventListener('input',function(e){if(cform&&e.target.dataset.k)cform[e.target.dataset.k]=e.target.value});
$('#cuform').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;if(b.id==='cusave')saveCu();else if(b.id==='cucancel'){cform=null;renderCuForm()}});
$('#cutbl').addEventListener('click',kebabClick);
MENUS.cu={
  html:function(){return mi('akt',ICO.spec,t('ak_h'))+mi('edit',ICO.edit,t('m_edit'))+mi('del',ICO.del,t('m_del'),'del')},
  q:function(){return t('cu_del_q')},
  act:function(a,no){if(a==='akt')openAkt(+no);else if(a==='edit')openCu(+no);else if(a==='confirmdel')delCu(+no)}
};

