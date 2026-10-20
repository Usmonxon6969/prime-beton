/* Stock counts / write-offs and piece-rate payroll. Loaded after extra.js, which gives us addView(). */
(function(){
'use strict';
var X={
 nav_adj:['Counts & write-offs','Инвентаризация','Inventarizatsiya'],nav_pay:['Pay & workers','Зарплата','Ish haqi'],grp_stock:['Stock control','Контроль склада','Ombor nazorati'],grp_pay:['Payroll','Оплата труда','Ish haqi'],
 p_scrap:['Scrap','Брак','Brak'],p_crew:['Crew (shares the piece pay)','Бригада (делит сдельную оплату)','Brigada (donabay haqni bo‘lishadi)'],p_crew_none:['No workers yet. Add them on the Pay page.','Работников пока нет. Добавьте их на странице «Зарплата».','Hozircha ishchilar yo‘q. Ularni «Ish haqi» sahifasida qo‘shing.'],
 f_worker:['Worker','Работник','Ishchi'],f_worker_none:['— not linked to a worker —','— без привязки к работнику —','— ishchiga bog‘lanmagan —'],
 api_worker_mismatch:['Choose an active worker for a salary payment.','Для выплаты зарплаты выберите действующего работника.','Oylik to‘lovi uchun faol ishchini tanlang.'],
 ad_h:['Counts and write-offs','Инвентаризация и списания','Inventarizatsiya va hisobdan chiqarish'],ad_note:['A count sets the stock to what was counted. A write-off removes spoiled, damaged or lost goods.','Инвентаризация приводит остаток к пересчитанному. Списание убирает испорченное, повреждённое или потерянное.','Inventarizatsiya qoldiqni sanalgan miqdorga keltiradi. Hisobdan chiqarish buzilgan, shikastlangan yoki yo‘qolgan tovarni olib tashlaydi.'],
 ad_count:['Stock count','Инвентаризация','Inventarizatsiya'],ad_writeoff:['Write-off','Списание','Hisobdan chiqarish'],ad_new:['New document','Новый документ','Yangi hujjat'],
 ad_wh:['Warehouse','Склад','Ombor'],ad_date:['Date','Дата','Sana'],ad_reason:['Reason','Причина','Sabab'],ad_comment:['Comment','Комментарий','Izoh'],
 ad_item:['Item','Позиция','Pozitsiya'],ad_system:['In system','В учёте','Hisobda'],ad_counted:['Counted','Посчитано','Sanaldi'],ad_diff:['Difference','Разница','Farq'],ad_qty:['Quantity','Количество','Miqdor'],
 ad_add:['Add item','Добавить позицию','Pozitsiya qo‘shish'],ad_load:['Load all items in stock','Загрузить все позиции с остатком','Qoldig‘i bor hamma pozitsiyani yuklash'],ad_post:['Post','Провести','O‘tkazish'],
 ad_log:['Documents','Документы','Hujjatlar'],ad_none:['No documents yet.','Документов пока нет.','Hujjatlar hali yo‘q.'],ad_posted:['Document %s posted.','Документ %s проведён.','%s hujjati o‘tkazildi.'],
 ad_pick:['— choose item —','— выберите позицию —','— pozitsiyani tanlang —'],ad_rm:['Remove','Убрать','Olib tashlash'],ad_del:['Delete','Удалить','O‘chirish'],ad_restore:['Restore','Восстановить','Tiklash'],
 ad_err_rows:['Add at least one item with a quantity.','Добавьте хотя бы одну позицию с количеством.','Kamida bitta miqdorli pozitsiya qo‘shing.'],ad_err_reason:['Choose the reason for the write-off.','Выберите причину списания.','Hisobdan chiqarish sababini tanlang.'],ad_err_wh:['Choose a warehouse.','Выберите склад.','Omborni tanlang.'],
 r_scrap:['Scrap','Брак','Brak'],r_damage:['Damage','Повреждение','Shikastlanish'],r_loss:['Loss','Потеря','Yo‘qotish'],r_expired:['Expired','Истёк срок','Muddati o‘tgan'],r_other:['Other','Другое','Boshqa'],
 api_reason_required:['Choose the reason for the write-off.','Выберите причину списания.','Hisobdan chiqarish sababini tanlang.'],api_duplicate_item:['Each item can be counted only once.','Каждую позицию можно посчитать только один раз.','Har bir pozitsiyani faqat bir marta sanash mumkin.'],api_kind_locked:['The type of the document cannot be changed.','Тип документа изменить нельзя.','Hujjat turini o‘zgartirib bo‘lmaydi.'],
 py_h:['Pay and workers','Зарплата и работники','Ish haqi va ishchilar'],py_note:['Pay is by the piece: each batch earns good units × the product rate, shared equally by its crew.','Оплата сдельная: партия приносит годные единицы × расценку, поровну между бригадой.','Haq donabay: har bir partiya yaroqli dona × narx, brigada teng bo‘lishadi.'],
 py_stmt:['Statement','Ведомость','Qaydnoma'],py_workers:['Workers','Работники','Ishchilar'],py_rates:['Rates','Расценки','Narxlar'],py_bonus:['Bonuses & deductions','Премии и удержания','Mukofot va ushlanmalar'],
 py_from:['From','С','Dan'],py_to:['To','По','Gacha'],py_worker:['Worker','Работник','Ishchi'],py_pos:['Position','Должность','Lavozim'],py_earned:['Earned','Начислено','Hisoblandi'],py_adj:['Bonus / deduction','Премии / удержания','Mukofot / ushlanma'],py_paid:['Paid','Выплачено','To‘langan'],py_owed:['Owed','К выплате','To‘lanishi kerak'],
 py_unassigned:['Pay of batches without a crew: %n','Оплата партий без бригады: %n','Brigadasiz partiyalar haqi: %n'],py_total:['Total','Итого','Jami'],py_pay_hint:['Pay salary from the Bank or Cash page: choose the article “Salary” and the worker.','Выплату зарплаты проводите в разделе «Банк» или «Касса»: статья «Зарплата» и работник.','Oylikni «Bank» yoki «Kassa» sahifasida to‘lang: «Ish haqi» moddasi va ishchi.'],
 py_name:['Name','Имя','Ism'],py_phone:['Phone','Телефон','Telefon'],py_active:['Active','Работает','Ishlaydi'],py_add:['Add worker','Добавить работника','Ishchi qo‘shish'],py_save:['Save','Сохранить','Saqlash'],py_del:['Remove','Убрать','Olib tashlash'],py_off:['archived','в архиве','arxivda'],py_saved:['Saved.','Сохранено.','Saqlandi.'],
 py_nomatch:['Nothing found.','Ничего не найдено.','Hech narsa topilmadi.'],py_rate:['Rate per unit','Расценка за единицу','Bir dona narxi'],py_product:['Product','Продукция','Mahsulot'],py_rates_note:['Rates apply to batches posted from now on; earlier batches keep their pay.','Расценки действуют для новых партий; прошлые партии сохраняют начисленное.','Narxlar yangi partiyalarga amal qiladi; oldingilari o‘z haqini saqlaydi.'],
 py_amount:['Amount (− for a deduction)','Сумма (− для удержания)','Summa (ushlanma uchun −)'],py_note_f:['Note','Примечание','Izoh'],py_date:['Date','Дата','Sana'],py_addb:['Add entry','Добавить запись','Yozuv qo‘shish'],py_none:['Nothing here yet.','Пока ничего нет.','Hozircha hech narsa yo‘q.'],py_pickw:['— choose worker —','— выберите работника —','— ishchini tanlang —'],
 api_amount_required:['Enter an amount.','Укажите сумму.','Summani kiriting.'],api_invalid_item:['Rates can be set for products only.','Расценки задаются только для продукции.','Narx faqat mahsulot uchun belgilanadi.']
};
Object.keys(X).forEach(function(k){T.en[k]=X[k][0];T.ru[k]=X[k][1];T.uz[k]=X[k][2]});
var XA={
 py_akt:['Act','Акт сверки','Akt sverka'],py_akt_h:['Worker reconciliation act','Акт сверки с работником','Ishchi bilan akt sverka'],
 py_back:['Back to statement','К ведомости','Qaydnomaga qaytish'],
 py_open:['Owed at the start of the period','Долг на начало периода','Davr boshidagi qoldiq'],py_accr:['Accrued','Начислено','Hisoblangan'],
 py_close:['Owed to the worker at the end','Долг перед работником на конец','Davr oxirida ishchiga to‘lash kerak'],
 py_close_adv:['Paid in advance (the worker owes) at the end','Выплачено вперёд (аванс) на конец','Davr oxirida avans (ishchi qarzdor)'],
 py_bal:['Balance','Сальдо','Qoldiq'],py_doc:['Document','Документ','Hujjat'],
 py_k_earn:['Piece-rate pay, batch','Сдельная оплата, партия','Donabay haq, partiya'],py_k_adj:['Bonus / deduction','Премия / удержание','Mukofot / ushlanma'],py_k_pay:['Salary payment','Выплата зарплаты','Oylik to‘lovi'],
 py_crew:['crew of %n','бригада из %n','brigada: %n kishi'],py_copy:['Copy as text','Копировать текстом','Matn sifatida nusxalash'],
 py_copied:['Copied to clipboard.','Скопировано в буфер обмена.','Nusxalandi.'],py_copyfail:['Could not copy. Select the table and copy it by hand.','Не удалось скопировать. Выделите таблицу и скопируйте вручную.','Nusxalab bo‘lmadi. Jadvalni belgilab, qo‘lda nusxalang.'],
 py_noops:['No entries in this period.','За этот период записей нет.','Bu davrda yozuv yo‘q.']
};
Object.keys(XA).forEach(function(k){T.en[k]=XA[k][0];T.ru[k]=XA[k][1];T.uz[k]=XA[k][2]});
if(typeof APIX!=='undefined'){['worker_mismatch','reason_required','duplicate_item','kind_locked','amount_required','invalid_item'].forEach(function(c){if(X['api_'+c])APIX[c]=X['api_'+c]})}

/* navigation */
NI.adj='<path d="M4 3.5h12v13H4zM7 8l1.5 1.5L12 6M7 13h6"/>';
NI.pay='<circle cx="7.5" cy="7" r="3"/><path d="M2 16c.6-3 3-4.5 5.5-4.5S12.4 13 13 16M14 5.5v6M12 8h4"/>';
NAV.splice(NAV.length-2,0,{g:'grp_stock',i:[['adj','stock','nav_adj']]},{g:'grp_pay',i:[['pay','payroll','nav_pay']]});
SECHASH.adj='stock';SECHASH.pay='payroll';

function Q(o){var a=[];Object.keys(o).forEach(function(k){if(o[k]!==''&&o[k]!=null)a.push(encodeURIComponent(k)+'='+encodeURIComponent(o[k]))});return a.length?'?'+a.join('&'):''}
function say(id,txt,bad){var m=$(id);if(m){m.className='msg '+(bad?'bad':'ok');m.textContent=txt}}
function itemList(){
  var l=[];PRID.forEach(function(id,k){l.push({id:id,name:PRODUCTS[k]})});MATID.forEach(function(id,j){l.push({id:id,name:mname(j)})});
  return l;
}
function itemName(id){var k=PRID.indexOf(id);if(k>-1)return PRODUCTS[k];var j=MATID.indexOf(id);return j>-1?mname(j):'#'+id}
function sysQty(id,wh){
  var wi=WH_IDX[wh];for(var i=0;i<ITEMS.length;i++){if(ITEMS[i].id===id)return +(ITEMS[i].st[wi]||0)}return 0;
}
var REASONS=['scrap','damage','loss','expired','other'];

/* ================= stock counts and write-offs ================= */
var AD={kind:'count',wh:0,lines:[],reason:'',msg:null,docs:[],date:''};
var ADX={};window.adxOpen=function(id){ADX[id]=true};                                    // ids of the log rows whose full list of positions is open
function adLine(d,r){return itemName(r.item_id)+' '+(d.kind==='count'?(r.delta>0?'+':'')+fmt(r.delta):'−'+fmt(r.qty))}
/* the «Items» cell of the log: one position per line, three at most; a click on the row opens all of them in a table under it */
function adPos(d){
  var n=d.rows.length;
  return '<button type="button" class="pos-btn" data-pos="'+d.id+'" aria-expanded="'+(ADX[d.id]?'true':'false')+'" title="'+esc(t('pos_open'))+'">'+d.rows.slice(0,3).map(function(r,i){
    return '<span class="pos-line">'+esc(adLine(d,r))+(i===2&&n>3?'<span class="pos-more">'+esc(t('pos_more').replace('%n',n-3))+'</span>':'')+'</span>';
  }).join('')+'</button>';
}
function adTable(d){
  return '<div class="pos-table ad-table" role="table" aria-label="'+esc(t('c_items'))+'"><div role="row" class="ph"><span role="columnheader">№</span><span role="columnheader">'+t('c_items')+'</span><span role="columnheader" class="num">'+t(d.kind==='count'?'ad_diff':'ad_qty')+'</span></div>'+
    d.rows.map(function(r,i){return '<div role="row"><span role="cell" class="mono">'+(i+1)+'</span><span role="cell">'+esc(itemName(r.item_id))+'</span><span role="cell" class="num">'+(d.kind==='count'?(r.delta>0?'+':'')+fmt(r.delta):'−'+fmt(r.qty))+'</span></div>'}).join('')+'</div>';
}
function nowLocal(){return toLocal(new Date())}
function renderStock(){
  var el=$('#xv-stock'),edit=lvl('adj')>1;
  if(!AD.wh&&WHID.length)AD.wh=WHID[0];
  if(!AD.date)AD.date=nowLocal();
  api('GET','/adjustments').then(function(docs){AD.docs=docs;paintStock(el,edit)},function(e){el.innerHTML='<div class="wrap dash"><p class="msg bad">'+esc(apiErr(e))+'</p></div>'});
}
function paintStock(el,edit){
  var items=itemList(),isCount=AD.kind==='count',h='<div class="wrap dash"><div class="dhead"><div><h1>'+t('ad_h')+'</h1><p class="note">'+t('ad_note')+'</p></div></div>';
  if(edit){
    h+='<div class="panel stack"><h2>'+t('ad_new')+'</h2><div class="seg" id="ad-kind" role="group" style="justify-self:start"><button type="button" data-k="count" aria-pressed="'+isCount+'">'+t('ad_count')+'</button><button type="button" data-k="writeoff" aria-pressed="'+!isCount+'">'+t('ad_writeoff')+'</button></div>'+
      '<div class="akbar"><div class="field"><label for="ad-wh">'+t('ad_wh')+'</label><select id="ad-wh">'+WH.map(function(n,i){return '<option value="'+WHID[i]+'"'+(WHID[i]===AD.wh?' selected':'')+'>'+esc(n)+'</option>'}).join('')+'</select></div>'+
      '<div class="field"><label for="ad-date">'+t('ad_date')+'</label><input id="ad-date" type="datetime-local" value="'+AD.date+'"></div>'+
      (isCount?'':'<div class="field"><label for="ad-reason">'+t('ad_reason')+'</label><select id="ad-reason"><option value="">—</option>'+REASONS.map(function(r){return '<option value="'+r+'"'+(AD.reason===r?' selected':'')+'>'+t('r_'+r)+'</option>'}).join('')+'</select></div>')+
      '<div class="field" style="flex:1"><label for="ad-com">'+t('ad_comment')+'</label><input id="ad-com" type="text" value="'+esc(AD.comment||'')+'"></div></div>'+
      '<div style="overflow-x:auto"><table class="dt"><thead><tr><th>'+t('ad_item')+'</th>'+(isCount?'<th class="num">'+t('ad_system')+'</th><th class="num">'+t('ad_counted')+'</th><th class="num">'+t('ad_diff')+'</th>':'<th class="num">'+t('ad_qty')+'</th>')+'<th></th></tr></thead><tbody>'+
      AD.lines.map(function(l,i){
        var sys=isCount&&l.item_id?sysQty(l.item_id,AD.wh):0,diff=isCount&&l.qty!==''?(+l.qty-sys):null;
        return '<tr><td><select data-i="'+i+'" data-f="item"><option value="">'+t('ad_pick')+'</option>'+items.map(function(it){return '<option value="'+it.id+'"'+(it.id===l.item_id?' selected':'')+'>'+esc(it.name)+'</option>'}).join('')+'</select></td>'+
          (isCount?'<td class="num">'+(l.item_id?fmt(sys):'')+'</td>':'')+'<td class="num"><input type="number" step="any" min="0" data-i="'+i+'" data-f="qty" value="'+(l.qty===''?'':l.qty)+'" style="width:110px;text-align:right" aria-label="'+t(isCount?'ad_counted':'ad_qty')+'"></td>'+
          (isCount?'<td class="num"'+(diff<0?' style="color:var(--bad)"':'')+'>'+(diff==null?'':(diff>0?'+':'')+fmt(diff))+'</td>':'')+
          '<td><button type="button" class="link" data-rm="'+i+'" aria-label="'+t('ad_rm')+'">×</button></td></tr>';
      }).join('')+'</tbody></table></div>'+
      '<div class="pbtns"><button type="button" class="btn ghost sm" id="ad-add">'+t('ad_add')+'</button>'+(isCount?'<button type="button" class="btn ghost sm" id="ad-load">'+t('ad_load')+'</button>':'')+'<button type="button" class="btn primary sm" id="ad-post">'+t('ad_post')+'</button></div><p class="msg" id="ad-msg" role="status"></p></div>';
  }
  h+='<div class="panel stack"><h2>'+t('ad_log')+'</h2>'+(AD.docs.length?'<div style="overflow-x:auto"><table class="dt"><thead><tr><th>№</th><th>'+t('ad_date')+'</th><th>'+t('ad_wh')+'</th><th>'+t('ad_reason')+'</th><th>'+t('c_items')+'</th><th>'+t('c_status')+'</th>'+(edit?'<th></th>':'')+'</tr></thead><tbody>'+
    AD.docs.map(function(d){
      var wi=WH_IDX[d.warehouse_id],del=d.status==='deleted';
      return '<tr class="ad-row '+(del?'is-deleted':'')+(ADX[d.id]?' is-open':'')+'" data-id="'+d.id+'"><td class="mono">'+esc(d.number)+'</td><td class="mono">'+dtf(new Date(d.date))+'</td><td>'+esc(wi!=null?WH[wi]:'')+'</td><td>'+(d.kind==='count'?t('ad_count'):t('r_'+(d.reason||'other')))+'</td>'+
        '<td class="wrap">'+adPos(d)+'</td><td>'+pill(del?'deleted':'posted')+'</td>'+
        (edit?'<td><button type="button" class="btn ghost sm" data-'+(del?'rs':'dl')+'="'+d.id+'">'+t(del?'ad_restore':'ad_del')+'</button></td>':'')+'</tr>'+
        (ADX[d.id]?'<tr class="ad-detail"><td colspan="'+(edit?7:6)+'">'+adTable(d)+'</td></tr>':'');
    }).join('')+'</tbody></table></div>':'<p class="empty">'+t('ad_none')+'</p>')+'</div></div>';
  el.innerHTML=h;
  if(AD.msg)say('#ad-msg',AD.msg.txt,AD.msg.bad);
  el.onclick=function(e){
    var row=e.target.closest('tr.ad-row');                                         // a click on a log row (not on its Delete / Restore button) opens or closes its table of positions
    if(row&&!e.target.closest('[data-dl],[data-rs]')){
      if(window.getSelection&&String(window.getSelection()))return;                // the user is selecting text: leave it alone
      var id=row.dataset.id,viaBtn=!!e.target.closest('.pos-btn');
      if(ADX[id])delete ADX[id];else ADX[id]=true;
      paintStock(el,edit);
      if(viaBtn){var pb=el.querySelector('[data-pos="'+id+'"]');if(pb)pb.focus()}
      return;
    }
    var b=e.target.closest('button');if(!b)return;
    if(b.dataset.k){AD.kind=b.dataset.k;AD.lines=[];AD.msg=null;paintStock(el,edit);return}
    if(b.dataset.rm!==undefined){AD.lines.splice(+b.dataset.rm,1);paintStock(el,edit);return}
    if(b.id==='ad-add'){AD.lines.push({item_id:0,qty:''});paintStock(el,edit);return}
    if(b.id==='ad-load'){
      AD.lines=[];itemList().forEach(function(it){var q=sysQty(it.id,AD.wh);if(q>0)AD.lines.push({item_id:it.id,qty:q})});paintStock(el,edit);return}
    if(b.id==='ad-post'){postStock(el,edit);return}
    var act=b.dataset.dl||b.dataset.rs;
    if(act)api(b.dataset.dl?'DELETE':'POST','/adjustments/'+act+(b.dataset.rs?'/restore':''),b.dataset.rs?{}:undefined).then(function(){return Store.load()}).then(function(){AD.msg=null;renderStock()},function(er){toast(apiErr(er),true)});
  };
  el.onchange=function(e){
    var f=e.target;
    if(f.id==='ad-wh'){AD.wh=+f.value;setTimeout(function(){paintStock(el,edit)},0);return}
    if(f.id==='ad-date'){AD.date=f.value;return}
    if(f.id==='ad-reason'){AD.reason=f.value;return}
    if(f.id==='ad-com'){AD.comment=f.value;return}
    if(f.dataset.f==='item'){AD.lines[+f.dataset.i].item_id=+f.value;if(AD.kind==='count'&&f.value&&AD.lines[+f.dataset.i].qty==='')AD.lines[+f.dataset.i].qty=sysQty(+f.value,AD.wh);setTimeout(function(){paintStock(el,edit)},0)}
    else if(f.dataset.f==='qty'){
      var ln=AD.lines[+f.dataset.i];ln.qty=f.value===''?'':+f.value;
      var dc=f.closest('tr').querySelector('td:nth-child(4)');                       // count rows: update the difference in place (a repaint here would fight the input's blur)
      if(AD.kind==='count'&&dc&&ln.item_id){var df=ln.qty===''?null:ln.qty-sysQty(ln.item_id,AD.wh);dc.textContent=df==null?'':(df>0?'+':'')+fmt(df);dc.style.color=df<0?'var(--bad)':''}
    }
  };
}
function postStock(el,edit){
  var rows=AD.lines.filter(function(l){return l.item_id&&l.qty!==''&&l.qty>=0&&(AD.kind==='count'||l.qty>0)});
  var fail=function(k){AD.msg={txt:t(k),bad:true};say('#ad-msg',t(k),true)};
  if(!AD.wh)return fail('ad_err_wh');
  if(!rows.length)return fail('ad_err_rows');
  if(AD.kind==='writeoff'&&!AD.reason)return fail('ad_err_reason');
  var dt=new Date(AD.date);if(isNaN(dt.getTime()))return fail('err_date');
  var body={date:isoLocal(dt),kind:AD.kind,warehouse_id:AD.wh,reason:AD.kind==='writeoff'?AD.reason:'',comment:AD.comment||'',rows:rows.map(function(l){return {item_id:l.item_id,qty:+l.qty}})};
  api('POST','/adjustments',body).then(function(d){
    AD.lines=[];AD.reason='';AD.comment='';AD.date='';AD.msg={txt:tf('ad_posted',{s:d.number})};
    return Store.load();
  }).then(function(){renderStock();toast(AD.msg.txt)},function(er){AD.msg={txt:apiErr(er),bad:true};say('#ad-msg',AD.msg.txt,true)});
}

/* ================= payroll ================= */
var PY={tab:'stmt',from:'',to:'',set:false,aw:0,w:[],rates:{},adj:[],msg:null};
function renderPay(){
  var el=$('#xv-payroll'),edit=lvl('pay')>1;
  if(!PY.set){var n=new Date();PY.from=toDay(new Date(n.getFullYear(),n.getMonth(),1));PY.to=toDay(n);PY.set=true}   // set once: an empty range means "all time"
  var tabs=['stmt','workers','rates','bonus'],names={stmt:'py_stmt',workers:'py_workers',rates:'py_rates',bonus:'py_bonus'};
  var head='<div class="wrap dash"><div class="dhead"><div><h1>'+t('py_h')+'</h1><p class="note">'+t('py_note')+'</p></div></div><div class="seg" id="py-tabs" role="group" style="justify-self:start;max-width:100%;overflow-x:auto">'+tabs.map(function(k){return '<button type="button" data-t="'+k+'" aria-pressed="'+(PY.tab===k||(k==='stmt'&&PY.tab==='akt'))+'">'+t(names[k])+'</button>'}).join('')+'</div><div id="py-body"></div></div>';
  el.innerHTML=head;
  el.onclick=function(e){var b=e.target.closest('#py-tabs button');if(b){PY.tab=b.dataset.t;PY.msg=null;renderPay()}};
  var body=$('#py-body'),err=function(e){body.innerHTML='<p class="msg bad">'+esc(apiErr(e))+'</p>'};
  if(PY.tab==='stmt')payStmt(body,err);
  else if(PY.tab==='akt')payAkt(body,err);
  else if(PY.tab==='workers')payWorkers(body,edit,err);
  else if(PY.tab==='rates')payRates(body,edit,err);
  else payBonus(body,edit,err);
}
function payStmt(body,err){
  api('GET','/payroll'+Q({start:PY.from?PY.from+'T00:00:00':'',end:PY.to?PY.to+'T23:59:59':''})).then(function(st){
    var cols=['py_worker','py_pos','py_earned','py_adj','py_paid','py_owed'];
    body.innerHTML='<div class="panel stack">'+payBar()+''+
      (st.rows.length?'<div style="overflow-x:auto"><table class="dt"><thead><tr>'+cols.map(function(c,i){return '<th'+(i>1?' class="num"':'')+'>'+t(c)+'</th>'}).join('')+'<th></th></tr></thead><tbody>'+
        st.rows.map(function(r){return '<tr><td>'+esc(r.name)+(r.active?'':' <small class="note">('+t('py_off')+')</small>')+'</td><td>'+esc(r.position)+'</td><td class="num">'+money(r.earned)+'</td><td class="num">'+money(r.adjust)+'</td><td class="num">'+money(r.paid)+'</td><td class="num"><b>'+money(r.owed)+'</b></td><td><button type="button" class="btn ghost sm" data-akt="'+r.worker_id+'">'+t('py_akt')+'</button></td></tr>'}).join('')+'</tbody><tfoot><tr><td>'+t('py_total')+'</td><td></td><td class="num">'+money(st.totals.earned)+'</td><td class="num">'+money(st.totals.adjust)+'</td><td class="num">'+money(st.totals.paid)+'</td><td class="num">'+money(st.totals.owed)+'</td><td></td></tr></tfoot></table></div>':'<p class="empty">'+t('py_none')+'</p>')+
      (st.unassigned?'<p class="note">'+tf('py_unassigned',{n:money(st.unassigned)})+'</p>':'')+'<p class="note">'+t('py_pay_hint')+'</p></div>';
    bindBar(function(){payStmt(body,err)});
    body.onclick=function(e){var b=e.target.closest('[data-akt]');if(b){PY.aw=+b.dataset.akt;PY.tab='akt';renderPay()}};
  },err);
}

/* the date bar shared by the statement and the worker act: presets (all time, this month, ...) and two dates */
function payBar(){
  return '<div class="akbar" id="py-bar">'+dpHtml(PY.from,PY.to)+'<div class="field"><label for="py-from">'+t('py_from')+'</label><input id="py-from" type="date" value="'+PY.from+'"></div><div class="field"><label for="py-to">'+t('py_to')+'</label><input id="py-to" type="date" value="'+PY.to+'"></div></div>';
}
function bindBar(redo){
  var bar=$('#py-bar');
  bar.onchange=function(e){if(e.target.id==='py-from')PY.from=e.target.value;else if(e.target.id==='py-to')PY.to=e.target.value;redo()};
  bar.onclick=function(e){var b=e.target.closest('[data-dp]');if(b){var r=dpRange(b.dataset.dp);PY.from=r.from;PY.to=r.to;redo()}};
}
function payAkt(body,err){
  api('GET','/payroll/worker/'+PY.aw+Q({start:PY.from?PY.from+'T00:00:00':'',end:PY.to?PY.to+'T23:59:59':''})).then(function(a){
    var w=a.worker,per=(!PY.from&&!PY.to)?t('ak_period_all'):t('ak_period').replace('%a',PY.from?dfmt(pday(PY.from)):'…').replace('%b',PY.to?dfmt(pday(PY.to)):'…');
    var nm=function(id){var k=PRID.indexOf(id);return k>=0?PRODUCTS[k]:'#'+id};
    var sg=function(n){return n<0?'− '+money(-n):money(n)};
    var closeLbl=t(a.closing<0?'py_close_adv':'py_close');
    var L=[t('py_akt_h')+': '+w.name,per,'',t('py_open')+'\t'+sg(a.opening),t('py_accr')+'\t'+money(a.accrued),t('py_paid')+'\t'+money(a.paid),closeLbl+'\t'+money(Math.abs(a.closing)),'',[t('py_doc'),t('py_accr'),t('py_paid'),t('py_bal')].join('\t')];
    var trs=a.rows.map(function(r){
      var title=t('py_k_'+r.kind)+(r.kind==='adj'?'':' '+r.no)+' '+t('ak_dated')+' '+dfmt(new Date(r.date));
      var det=r.kind==='earn'?(r.items||[]).map(function(i){return nm(i.item_id)+': '+(Math.round(i.qty*1000)/1000)}).join(', ')+' · '+t('py_crew').replace('%n',r.crew):r.note;
      L.push([title+(det?' ('+det+')':''),r.accrued?sg(r.accrued):'',r.paid?money(r.paid):'',sg(r.balance)].join('\t'));
      return '<tr><td><div class="pdoc">'+esc(title)+(det?'<small class="note">'+esc(det)+'</small>':'')+'</div></td><td class="num">'+(r.accrued?sg(r.accrued):'')+'</td><td class="num">'+(r.paid?money(r.paid):'')+'</td><td class="num">'+sg(r.balance)+'</td></tr>';
    });
    PY.text=L.join('\n');
    body.innerHTML='<div class="panel stack"><div class="pbtns"><button type="button" class="btn ghost sm" id="pa-back">← '+t('py_back')+'</button><button type="button" class="btn ghost sm" id="pa-copy">'+t('py_copy')+'</button></div>'+
      '<h2>'+t('py_akt_h')+': '+esc(w.name)+'</h2><p class="note">'+esc([w.position,w.phone].filter(Boolean).join(' · '))+'</p>'+payBar()+
      '<div class="aksum"><div class="akper">'+esc(per)+'</div><div class="akl"><span>'+t('py_open')+'</span><b>'+sg(a.opening)+'</b></div><div class="akl"><span>'+t('py_accr')+'</span><b>'+money(a.accrued)+'</b></div><div class="akl"><span>'+t('py_paid')+'</span><b>'+money(a.paid)+'</b></div><div class="akl last"><span>'+closeLbl+'</span><b>'+money(Math.abs(a.closing))+'</b></div></div>'+
      '<div style="overflow-x:auto"><table class="dt"><thead><tr><th><span class="vh">'+t('py_doc')+'</span></th><th class="num">'+t('py_accr')+'</th><th class="num">'+t('py_paid')+'</th><th class="num">'+t('py_bal')+'</th></tr></thead><tbody>'+(trs.length?trs.join(''):'<tr><td colspan="4" class="empty">'+t('py_noops')+'</td></tr>')+'</tbody></table></div><p class="msg" id="py-msg" role="status"></p></div>';
    bindBar(function(){payAkt(body,err)});
    $('#pa-back').onclick=function(){PY.tab='stmt';renderPay()};
    $('#pa-copy').onclick=function(){copyText(PY.text,function(ok){say('#py-msg',t(ok?'py_copied':'py_copyfail'),!ok)})};
  },err);
}
function copyText(txt,done){
  try{if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(function(){done(true)},function(){done(false)});return}}catch(e){}
  try{var ta=document.createElement('textarea');ta.value=txt;ta.setAttribute('readonly','');ta.style.cssText='position:fixed;opacity:0;top:0;left:0';document.body.appendChild(ta);ta.select();var ok=document.execCommand('copy');document.body.removeChild(ta);done(!!ok)}catch(e2){done(false)}
}
function payWorkers(body,edit,err){
  api('GET','/workers').then(function(ws){
    body.innerHTML='<div class="panel stack"><div style="overflow-x:auto"><table class="dt"><thead><tr><th>'+t('py_name')+'</th><th>'+t('py_pos')+'</th><th>'+t('py_phone')+'</th><th>'+t('py_active')+'</th>'+(edit?'<th></th>':'')+'</tr></thead><tbody>'+
      (ws.length?ws.map(function(w){
        if(!edit)return '<tr><td>'+esc(w.name)+'</td><td>'+esc(w.position)+'</td><td>'+esc(w.phone)+'</td><td>'+(w.is_active?'✓':t('py_off'))+'</td></tr>';
        return '<tr data-w="'+w.id+'"><td><input type="text" data-f="name" value="'+esc(w.name)+'"></td><td><input type="text" data-f="position" value="'+esc(w.position)+'"></td><td><input type="text" data-phone inputmode="tel" data-f="phone" value="'+esc(w.phone)+'"></td><td><input type="checkbox" data-f="act"'+(w.is_active?' checked':'')+'></td><td><button type="button" class="btn ghost sm" data-save="'+w.id+'">'+t('py_save')+'</button> <button type="button" class="btn ghost sm" data-del="'+w.id+'">'+t('py_del')+'</button></td></tr>';
      }).join(''):'<tr><td colspan="5" class="empty">'+t('py_none')+'</td></tr>')+'</tbody></table></div><p class="msg" id="py-msg" role="status"></p></div>'+
      (edit?'<div class="panel stack"><h2>'+t('py_add')+'</h2><div class="akbar"><div class="field"><label for="nw-name">'+t('py_name')+'</label><input id="nw-name" type="text"></div><div class="field"><label for="nw-pos">'+t('py_pos')+'</label><input id="nw-pos" type="text"></div><div class="field"><label for="nw-ph">'+t('py_phone')+'</label><input id="nw-ph" data-phone inputmode="tel" type="text"></div><button type="button" class="btn primary sm" id="nw-add">'+t('py_add')+'</button></div></div>':'');
    var done=function(){return Store.load().then(function(){renderPay()})};
    body.onclick=function(e){
      var s=e.target.closest('[data-save]'),d=e.target.closest('[data-del]');
      if(s){var tr=s.closest('tr'),wph=Phone.out(tr.querySelector('[data-f=phone]').value);if(wph===null){say('#py-msg',t('ph_bad'),true);return}api('PUT','/workers/'+s.dataset.save,{name:tr.querySelector('[data-f=name]').value,position:tr.querySelector('[data-f=position]').value,phone:wph,is_active:tr.querySelector('[data-f=act]').checked}).then(function(){say('#py-msg',t('py_saved'));return Store.load()},function(er){say('#py-msg',apiErr(er),true)});return}
      if(d){api('DELETE','/workers/'+d.dataset.del).then(done,function(er){say('#py-msg',apiErr(er),true)});return}
      if(e.target.closest('#nw-add')){var nph=Phone.out($('#nw-ph').value);if(nph===null){say('#py-msg',t('ph_bad'),true);return}api('POST','/workers',{name:$('#nw-name').value,position:$('#nw-pos').value,phone:nph}).then(done,function(er){say('#py-msg',apiErr(er),true)});}
    };
  },err);
}
var RATE_TR={а:'a',б:'b',в:'v',г:'g',д:'d',е:'e',ё:'e',ж:'zh',з:'z',и:'i',й:'y',к:'k',л:'l',м:'m',н:'n',о:'o',п:'p',р:'r',с:'s',т:'t',у:'u',ф:'f',х:'h',ц:'ts',ч:'ch',ш:'sh',щ:'sh',ъ:'',ы:'y',ь:'',э:'e',ю:'yu',я:'ya'};
function rateFold(x){   /* search key: case, spaces, comma/dot, 66*12 = 66x12 = 66:12, Cyrillic = Latin spelling */
  x=String(x||'').toLowerCase().replace(/(\d)\s*[x×х:]\s*(?=\d)/g,'$1*').replace(/,/g,'.').replace(/[\s\-_"'«»]+/g,'');
  return x.replace(/[а-яё]/g,function(c){return RATE_TR[c]!=null?RATE_TR[c]:c});
}
function payRates(body,edit,err){
  api('GET','/rates').then(function(rs){
    var cur={};rs.forEach(function(r){cur[r.item_id]=r.rate});
    body.innerHTML='<div class="panel stack"><p class="note">'+t('py_rates_note')+'</p><div class="field" style="max-width:360px"><input id="rtq" type="search" autocomplete="off" placeholder="'+esc(t('p_search'))+'" aria-label="'+esc(t('p_search'))+'"></div><div style="overflow-x:auto"><table class="dt"><thead><tr><th>'+t('py_product')+'</th><th class="num">'+t('py_rate')+'</th></tr></thead><tbody>'+
      PRID.map(function(id,k){return '<tr data-n="'+esc(rateFold(PRODUCTS[k]))+'"><td>'+esc(PRODUCTS[k])+'</td><td class="num">'+(edit?'<input type="number" min="0" step="any" data-it="'+id+'" value="'+(cur[id]!=null?cur[id]:'')+'" style="width:140px;text-align:right" aria-label="'+esc(PRODUCTS[k])+'">':money(cur[id]||0))+'</td></tr>'}).join('')+'</tbody></table></div>'+
      (edit?'<div class="pbtns"><button type="button" class="btn primary sm" id="rt-save">'+t('py_save')+'</button></div>':'')+'<p class="empty" id="rtnone" hidden>'+t('py_nomatch')+'</p><p class="msg" id="py-msg" role="status"></p></div>';
    var rq=body.querySelector('#rtq');
    rq.addEventListener('input',function(){            /* rows are only hidden, so rates typed but not yet saved are kept */
      var q=rateFold(rq.value),shown=0;
      body.querySelectorAll('tbody tr').forEach(function(tr){var ok=!q||tr.dataset.n.indexOf(q)>-1;tr.hidden=!ok;if(ok)shown++});
      body.querySelector('#rtnone').hidden=shown>0;
    });
    body.onclick=function(e){
      if(!e.target.closest('#rt-save'))return;
      var list=[];body.querySelectorAll('[data-it]').forEach(function(i){if(i.value!=='')list.push({item_id:+i.dataset.it,rate:+i.value})});
      api('PUT','/rates',{rates:list}).then(function(){say('#py-msg',t('py_saved'))},function(er){say('#py-msg',apiErr(er),true)});
    };
  },err);
}
function payBonus(body,edit,err){
  api('GET','/pay-adjusts').then(function(rows){
    var wn={};WORKERS.forEach(function(w){wn[w.id]=w.name});
    body.innerHTML=(edit?'<div class="panel stack"><h2>'+t('py_addb')+'</h2><div class="akbar"><div class="field"><label for="pb-w">'+t('py_worker')+'</label><select id="pb-w"><option value="">'+t('py_pickw')+'</option>'+WORKERS.map(function(w){return '<option value="'+w.id+'">'+esc(w.name)+'</option>'}).join('')+'</select></div>'+
      '<div class="field"><label for="pb-d">'+t('py_date')+'</label><input id="pb-d" type="date" value="'+toDay(new Date())+'"></div><div class="field"><label for="pb-a">'+t('py_amount')+'</label><input id="pb-a" type="number" step="any"></div><div class="field" style="flex:1"><label for="pb-n">'+t('py_note_f')+'</label><input id="pb-n" type="text"></div><button type="button" class="btn primary sm" id="pb-add">'+t('py_addb')+'</button></div><p class="msg" id="py-msg" role="status"></p></div>':'')+
      '<div class="panel stack">'+(rows.length?'<div style="overflow-x:auto"><table class="dt"><thead><tr><th>'+t('py_date')+'</th><th>'+t('py_worker')+'</th><th class="num">'+t('py_adj')+'</th><th>'+t('py_note_f')+'</th>'+(edit?'<th></th>':'')+'</tr></thead><tbody>'+
        rows.map(function(r){var del=r.status==='deleted';return '<tr class="'+(del?'is-deleted':'')+'"><td class="mono">'+dfmt(new Date(r.date))+'</td><td>'+esc(wn[r.worker_id]||('#'+r.worker_id))+'</td><td class="num"'+(r.amount<0?' style="color:var(--bad)"':'')+'>'+money(r.amount)+'</td><td>'+esc(r.note)+'</td>'+(edit?'<td><button type="button" class="btn ghost sm" data-'+(del?'rs':'dl')+'="'+r.id+'">'+t(del?'ad_restore':'ad_del')+'</button></td>':'')+'</tr>'}).join('')+'</tbody></table></div>':'<p class="empty">'+t('py_none')+'</p>')+'</div>';
    body.onclick=function(e){
      var b=e.target.closest('button');if(!b)return;
      if(b.id==='pb-add'){
        var w=+$('#pb-w').value,a=+$('#pb-a').value,d=$('#pb-d').value;
        if(!w||!a||!d){say('#py-msg',t(!w?'py_pickw':'api_amount_required'),true);return}
        api('POST','/pay-adjusts',{worker_id:w,date:d+'T12:00:00',amount:a,note:$('#pb-n').value}).then(function(){renderPay()},function(er){say('#py-msg',apiErr(er),true)});return}
      var id=b.dataset.dl||b.dataset.rs;
      if(id)api(b.dataset.dl?'DELETE':'POST','/pay-adjusts/'+id+(b.dataset.rs?'/restore':''),b.dataset.rs?{}:undefined).then(function(){renderPay()},function(er){toast(apiErr(er),true)});
    };
  },err);
}

window.payRefresh=function(){var v=$('#xv-payroll');if(v&&!v.hidden&&PY.tab==='stmt'&&$('#py-body'))renderPay()};   /* live updates: only the read-only statement */
window.addView('stock','adj',renderStock);
window.addView('payroll','pay',renderPay);
})();
