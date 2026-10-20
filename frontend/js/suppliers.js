/* suppliers and purchases */
var PX={
 nav_sup:['Suppliers','Поставщики','Yetkazib beruvchilar'],
 nav_rec:['Purchase receipts','Поступления','Kirim nakladnoylari'],
 su_h:['Suppliers','Поставщики','Yetkazib beruvchilar'],
 su_note:['Companies that supply your materials. Receipts and payments are linked to them.','Компании, поставляющие вам материалы. Поступления и оплаты привязываются к ним.','Material yetkazib beruvchi kompaniyalar. Kirim va to‘lovlar ularga bog‘lanadi.'],
 su_new_h:['New supplier','Новый поставщик','Yangi yetkazib beruvchi'],
 su_edit_h:['Edit supplier','Изменить поставщика','Yetkazib beruvchini tahrirlash'],
 su_recs:['Receipts','Поступления','Kirimlar'],
 su_recd:['Received, UZS','Получено, сум','Olingan, so‘m'],
 su_debt:['We owe (+) / advance (−), UZS','Наш долг (+) / аванс (−), сум','Bizning qarz (+) / avans (−), so‘m'],
 su_del_q:['Delete this supplier?','Удалить этого поставщика?','Bu yetkazib beruvchi o‘chirilsinmi?'],
 su_err_dup:['A supplier with this name already exists.','Поставщик с таким названием уже есть.','Bunday nomli yetkazib beruvchi allaqachon bor.'],
 su_err_used:['%m has receipts or payments and cannot be deleted.','У %m есть поступления или оплаты, удалить нельзя.','%m uchun kirim yoki to‘lov bor, o‘chirib bo‘lmaydi.'],
 su_saved:['Supplier %m saved.','Поставщик %m сохранён.','%m yetkazib beruvchisi saqlandi.'],
 su_deleted:['Supplier %m deleted.','Поставщик %m удалён.','%m yetkazib beruvchisi o‘chirildi.'],
 c_sup:['Supplier','Поставщик','Yetkazib beruvchi'],
 rc_h:['Purchase receipts','Поступления материалов','Kirim nakladnoylari'],
 rc_note:['Materials received from suppliers. Posting a receipt increases the warehouse stock and what we owe the supplier.','Материалы от поставщиков. При проведении остаток склада и наш долг поставщику увеличиваются.','Yetkazib beruvchidan materiallar kirimi. O‘tkazilganda ombor qoldig‘i va yetkazib beruvchi oldidagi qarzimiz oshadi.'],
 rc_new_h:['New purchase receipt','Новое поступление','Yangi kirim nakladnoyi'],
 rc_edit_h:['Edit receipt %s','Редактирование поступления %s','%s kirim nakladnoyini tahrirlash'],
 rc_post:['Post','Провести','O‘tkazish'],
 rc_mat_ph:['Choose a material','Выберите материал','Materialni tanlang'],
 rc_posted:['Receipt %m posted. Stock updated.','Поступление %m проведено. Остаток обновлён.','%m kirimi o‘tkazildi. Qoldiq yangilandi.'],
 rc_saved:['Receipt %m saved. Stock updated.','Поступление %m сохранено. Остаток обновлён.','%m kirimi saqlandi. Qoldiq yangilandi.'],
 rc_deleted:['Receipt %m deleted. The stock was reduced.','Поступление %m удалено. Остаток уменьшен.','%m kirimi o‘chirildi. Qoldiq kamaytirildi.'],
 rc_restored:['Receipt %m restored. Stock updated.','Поступление %m восстановлено. Остаток обновлён.','%m kirimi tiklandi. Qoldiq yangilandi.'],
 rc_err_sup:['Choose a supplier from the list.','Выберите поставщика из списка.','Yetkazib beruvchini ro‘yxatdan tanlang.'],
 rc_err_mat:['Choose a material from the list.','Выберите материал из списка.','Materialni ro‘yxatdan tanlang.'],
 rc_err_stock:['%m was already used: only %n kg left in %w, the receipt cannot be reduced.','%m уже израсходован: на складе %w осталось %n кг, поступление уменьшить нельзя.','%m allaqachon ishlatilgan: %w omborida %n kg qoldi, kirimni kamaytirib bo‘lmaydi.'],
 rc_del_q:['Delete this receipt? It stays in the journal as Deleted and the stock is reduced.','Удалить поступление? Оно останется в журнале со статусом Удалён, остаток уменьшится.','Kirim o‘chirilsinmi? U jurnalda “o‘chirilgan” holatida qoladi, qoldiq kamayadi.'],
 f_sup:['Supplier','Поставщик','Yetkazib beruvchi'],
 ak_back_sup:['Back to suppliers','К поставщикам','Yetkazib beruvchilarga qaytish'],
 ak_sup_inv:['Purchase receipt','Приходная накладная','Kirim nakladnoyi'],
 ak_pay_bank:['Bank payment','Списание со счета','Bank hisobidan to‘lov'],
 ak_pay_cash:['Cash payment','Расход из кассы','Kassadan to‘lov'],
 ak_cur_sup:['We owe the supplier at the moment','Наш долг перед поставщиком на текущий момент','Bizning yetkazib beruvchi oldidagi qarzimiz hozirgi holatda'],
 ak_cur_supadv:['The supplier owes us at the moment (advance)','Долг поставщика перед нами на текущий момент (аванс)','Yetkazib beruvchining bizdan qarzi hozirgi holatda (avans)'],
 ak_chg_sup:['Change of our debt to the supplier','Изменение нашего долга перед поставщиком','Yetkazib beruvchi oldidagi qarzimizning o‘zgarishi']
};
Object.keys(PX).forEach(function(k){T.en[k]=PX[k][0];T.ru[k]=PX[k][1];T.uz[k]=PX[k][2]});
var SUP=[];
function sidx(name){var n=String(name||'').trim().toLowerCase();if(!n)return -1;for(var i=0;i<SUP.length;i++){if(!SUP[i].gone&&SUP[i].n.toLowerCase()===n)return i}return -1}
function midx(name){
  var n=String(name||'').trim().toLowerCase();if(!n)return -1;
  for(var j=0;j<MATS.length;j++){
    if(MATS[j].deleted)continue;
    var nm=MATS[j].names?[MATS[j].names.uz,MATS[j].names.ru,MATS[j].names.en]:[MATS[j].name];
    if(nm.some(function(x){return String(x).toLowerCase()===n}))return j;
  }
  return -1;
}
var REC=[];
function findR(no){for(var i=0;i<REC.length;i++){if(REC[i].no===no)return REC[i]}return null}
function rowName(r){return r.p>=0?PRODUCTS[r.p]:mname(r.m)}
function rowItem(r){return r.p>=0?ITEM_BY[PRODUCTS[r.p]]:MAT_BY[r.m]}
function rowUnit(r){var it=rowItem(r);return uname(it?iu(it):(r.p>=0?0:1))}
function supPaid(i){return FIN.reduce(function(s,d){return s+(d.status==='posted'&&d.kind==='out'&&d.art==='sup'&&d.sup===i?d.amt:0)},0)}
function supDebt(i){return REC.reduce(function(s,v){return s+(v.status==='posted'&&v.sup===i?rsum(v.rows):0)},0)-supPaid(i)}
function supUsed(i){return REC.some(function(v){return v.sup===i})||FIN.some(function(d){return d.sup===i})}
function supDocs(c){
  var a=[];
  REC.forEach(function(v){if(v.status==='posted'&&v.sup===c)a.push({d:v.date,k:'inv',lbl:'ak_sup_inv',no:v.no,amt:rsum(v.rows),items:v.rows.map(function(r){return {n:rowName(r),q:r.q,pr:r.pr,u:rowUnit(r)}}),note:''})});
  FIN.forEach(function(f){if(f.status==='posted'&&f.kind==='out'&&f.art==='sup'&&f.sup===c){var cash=ACC[f.acc].t==='cash';a.push({d:f.date,k:cash?'cash':'bank',lbl:cash?'ak_pay_cash':'ak_pay_bank',no:f.no,amt:f.amt,note:aname(f.acc)+(f.comment?' · '+f.comment:'')})}});
  return a.sort(function(x,y){return x.d-y.d||(x.k==='inv'?-1:1)});
}
function openSupAkt(i){
  AK.cus=i;AK.sup=true;AK.msg=null;
  $('#akfrom').value='';$('#akto').value=toDay(new Date());
  location.hash='supplier-akt';
}

/* suppliers page */
var sform=null,smsg=null;
function renderSuForm(){
  var el=$('#suform');
  if(!sform){el.hidden=true;el.innerHTML='';return}
  el.hidden=false;
  el.innerHTML='<h2>'+t(sform.i<0?'su_new_h':'su_edit_h')+'</h2><div class="fgrid">'+
    '<div class="field"><label for="sun">'+t('cu_name')+'</label><input id="sun" data-k="n" type="text" autocomplete="off" value="'+esc(sform.n)+'"></div>'+
    '<div class="field"><label for="suph">'+t('cu_phone')+'</label><input id="suph" data-k="ph" data-phone type="text" autocomplete="off" inputmode="tel" value="'+esc(sform.ph)+'"></div>'+
    '<div class="field"><label for="suct">'+t('cu_contact')+'</label><input id="suct" data-k="ct" type="text" autocomplete="off" value="'+esc(sform.ct)+'"></div></div>'+
    '<div class="pbtns"><button type="button" class="btn primary sm" id="susave">'+t('sp_save')+'</button><button type="button" class="btn ghost sm" id="sucancel">'+t('m_cancel')+'</button></div>'+
    '<p class="msg bad" id="suferr" role="alert">'+(sform.err?t(sform.err).replace('%m',sform.errm||''):'')+'</p>';
}
function renderSup(){
  closeMenu();
  $('#suq').placeholder=t('p_search');$('#suq').setAttribute('aria-label',t('p_search'));
  var q=($('#suq').value||'').trim().toLowerCase(),list=[];
  SUP.forEach(function(c,i){if(!c.gone&&(!q||(c.n+' '+c.ph+' '+c.ct).toLowerCase().indexOf(q)>-1))list.push(i)});
  var head='<thead><tr><th>'+t('cu_name')+'</th><th>'+t('cu_phone')+'</th><th>'+t('cu_contact')+'</th><th class="num">'+t('su_recs')+'</th><th class="num">'+t('su_recd')+'</th><th class="num">'+t('su_debt')+'</th><th><span class="vh">'+t('m_actions')+'</span></th></tr></thead>';
  var body=list.length?list.map(function(i){
    var c=SUP[i],rc=REC.filter(function(v){return v.sup===i&&v.status==='posted'}).length,
        got=REC.reduce(function(s,v){return s+(v.sup===i&&v.status==='posted'?rsum(v.rows):0)},0),debt=supDebt(i);
    return '<tr><td>'+esc(c.n)+'</td><td class="mono">'+esc(c.ph||'–')+'</td><td>'+esc(c.ct||'–')+'</td><td class="num">'+rc+'</td><td class="num">'+(got?money(got):'–')+'</td><td class="num amt '+(debt>0?'out':debt<0?'in':'')+'">'+(debt===0?'–':(debt<0?'− ':'')+money(Math.abs(debt)))+'</td><td class="act">'+kebabHtml('su',i,c.n)+'</td></tr>';
  }).join(''):'<tr><td class="empty" colspan="7">'+t('em_sup')+'</td></tr>';
  $('#sutbl').innerHTML=head+'<tbody>'+body+'</tbody>';
  renderSuForm();
  var e=$('#sumsg');if(!smsg){e.className='msg';e.textContent=''}else{e.className='msg '+(smsg.err?'bad':'ok');e.textContent=tf(smsg.key,{m:smsg.m})}
}
function openSu(i){smsg=null;sform=i===undefined?{i:-1,n:'',ph:'',ct:'',err:null}:{i:i,n:SUP[i].n,ph:SUP[i].ph||'',ct:SUP[i].ct||'',err:null};renderSup();var f=$('#sun');if(f)f.focus()}
function saveSu(){
  var n=sform.n.trim().replace(/\s+/g,' ');
  if(!n){sform.err='mt_err_name';renderSuForm();return}
  var ex=sidx(n);if(ex>-1&&ex!==sform.i){sform.err='su_err_dup';renderSuForm();return}
  var ph=Phone.out(sform.ph);if(ph===null){sform.err='ph_bad';renderSuForm();return}
  var body={name:n,phone:ph,contact:sform.ct.trim()};
  srv(sform.i<0?api('POST','/suppliers',body):api('PUT','/suppliers/'+SUP[sform.i].id,body),function(){
    smsg={key:'su_saved',m:n};sform=null;$('#suq').value='';renderSup();
  },function(e){sform.err='api_raw';sform.errm=apiErr(e);renderSuForm()});
}
function delSu(i){
  var n=SUP[i].n;
  srv(api('DELETE','/suppliers/'+SUP[i].id),function(){smsg={key:'su_deleted',m:n};renderSup()},
    function(e){smsg={key:'api_raw',m:apiErr(e),err:true};renderSup()});
}
$('#sunew').addEventListener('click',function(){openSu()});
$('#suq').addEventListener('input',renderSup);
$('#suform').addEventListener('input',function(e){if(sform&&e.target.dataset.k)sform[e.target.dataset.k]=e.target.value});
$('#suform').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;if(b.id==='susave')saveSu();else if(b.id==='sucancel'){sform=null;renderSuForm()}});
$('#sutbl').addEventListener('click',kebabClick);
MENUS.su={
  html:function(){return mi('akt',ICO.spec,t('ak_h'))+mi('edit',ICO.edit,t('m_edit'))+mi('del',ICO.del,t('m_del'),'del')},
  q:function(){return t('su_del_q')},
  act:function(a,no){if(a==='akt')openSupAkt(+no);else if(a==='edit')openSu(+no);else if(a==='confirmdel')delSu(+no)}
};

