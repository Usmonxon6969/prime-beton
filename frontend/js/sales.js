/* sales */
var SX={
 nav_cus:['Customers','Покупатели','Mijozlar'],
 nav_ord:['Orders','Заказы','Buyurtmalar'],
 nav_inv:['Delivery notes','Расходные накладные','Chiqim nakladnoylari'],
 cu_h:['Customers','Покупатели','Mijozlar'],
 cu_note:['Buyers of your products. Orders and delivery notes are linked to them.','Покупатели вашей продукции. Заказы и накладные привязываются к ним.','Mahsulotlaringiz xaridorlari. Buyurtma va nakladnoylar ularga bog‘lanadi.'],
 cu_new_h:['New customer','Новый покупатель','Yangi mijoz'],
 cu_edit_h:['Edit customer','Изменить покупателя','Mijozni tahrirlash'],
 cu_name:['Name','Наименование','Nomi'],
 cu_phone:['Phone','Телефон','Telefon'],
 cu_contact:['Contact person','Контактное лицо','Mas’ul shaxs'],
 cu_orders:['Orders','Заказы','Buyurtmalar'],
 cu_sold:['Shipped, UZS','Отгружено, сум','Jo‘natilgan, so‘m'],
 cu_del_q:['Delete this customer?','Удалить этого покупателя?','Bu mijoz o‘chirilsinmi?'],
 cu_err_dup:['A customer with this name already exists.','Покупатель с таким названием уже есть.','Bunday nomli mijoz allaqachon bor.'],
 cu_err_used:['%m has orders or delivery notes and cannot be deleted.','У %m есть заказы или накладные, удалить нельзя.','%m uchun buyurtma yoki nakladnoy bor, o‘chirib bo‘lmaydi.'],
 cu_saved:['Customer %m saved.','Покупатель %m сохранён.','%m mijozi saqlandi.'],
 cu_deleted:['Customer %m deleted.','Покупатель %m удалён.','%m mijozi o‘chirildi.'],
 od_h:['Customer orders','Заказы покупателей','Buyurtmalar'],
 od_note:['Orders from customers. To ship an order, create a delivery note from it.','Заказы покупателей. Чтобы отгрузить заказ, создайте на его основании накладную.','Mijozlar buyurtmalari. Jo‘natish uchun buyurtma asosida nakladnoy yarating.'],
 od_new_h:['New order','Новый заказ','Yangi buyurtma'],
 od_edit_h:['Edit order %s','Редактирование заказа %s','%s buyurtmasini tahrirlash'],
 od_save:['Save order','Сохранить заказ','Buyurtmani saqlash'],
 c_cus:['Customer','Покупатель','Mijoz'],
 c_due:['Delivery date','Срок поставки','Yetkazish sanasi'],
 c_sum:['Amount, UZS','Сумма, сум','Summa, so‘m'],
 c_ship:['Shipped','Отгружено','Jo‘natildi'],
 c_price:['Price','Цена','Narx'],
 c_order:['Order','Заказ','Buyurtma'],
 c_wh:['Warehouse','Склад','Ombor'],
 os_new:['New','Новый','Yangi'],
 os_partial:['Partly shipped','Частично отгружен','Qisman jo‘natilgan'],
 os_shipped:['Shipped','Отгружен','Jo‘natilgan'],
 m_invoice:['Create delivery note','Создать накладную','Nakladnoy yaratish'],
 od_saved:['Order %m saved.','Заказ %m сохранён.','%m buyurtmasi saqlandi.'],
 od_deleted:['Order %m deleted.','Заказ %m удалён.','%m buyurtmasi o‘chirildi.'],
 od_restored:['Order %m restored.','Заказ %m восстановлен.','%m buyurtmasi tiklandi.'],
 od_err_cus:['Choose a customer from the list.','Выберите покупателя из списка.','Mijozni ro‘yxatdan tanlang.'],
 err_price:['Enter a price for every row.','Укажите цену для каждой позиции.','Har bir qator uchun narxni kiriting.'],
 od_err_ship:['The quantity of %m is below what was already shipped.','Количество %m меньше уже отгруженного.','%m miqdori allaqachon jo‘natilganidan kam.'],
 od_err_inv:['%m has posted delivery notes. Delete them first.','По %m есть проведённые накладные. Сначала удалите их.','%m bo‘yicha o‘tkazilgan nakladnoylar bor. Avval ularni o‘chiring.'],
 od_del_q:['Delete this order?','Удалить этот заказ?','Bu buyurtma o‘chirilsinmi?'],
 iv_h:['Delivery notes','Расходные накладные','Chiqim nakladnoylari'],
 iv_note:['Goods leaving a warehouse. Posting a note reduces the stock automatically.','Отпуск товара со склада. При проведении накладной остаток уменьшается автоматически.','Ombordan tovar chiqimi. Nakladnoy o‘tkazilganda qoldiq avtomatik kamayadi.'],
 iv_new_h:['New delivery note','Новая расходная накладная','Yangi chiqim nakladnoyi'],
 iv_edit_h:['Edit delivery note %s','Редактирование накладной %s','%s nakladnoyini tahrirlash'],
 iv_post:['Post','Провести','O‘tkazish'],
 iv_posted:['Delivery note %m posted. Stock updated.','Накладная %m проведена. Остаток обновлён.','%m nakladnoyi o‘tkazildi. Qoldiq yangilandi.'],
 iv_saved:['Delivery note %m saved. Stock updated.','Накладная %m сохранена. Остаток обновлён.','%m nakladnoyi saqlandi. Qoldiq yangilandi.'],
 iv_deleted:['Delivery note %m deleted. The goods are back in the warehouse.','Накладная %m удалена. Товар возвращён на склад.','%m nakladnoyi o‘chirildi. Tovar omborga qaytdi.'],
 iv_restored:['Delivery note %m restored. Stock updated.','Накладная %m восстановлена. Остаток обновлён.','%m nakladnoyi tiklandi. Qoldiq yangilandi.'],
 iv_err_stock:['Not enough %m in %w. Available: %n.','Недостаточно %m на складе %w. Доступно: %n.','%w omborida %m yetarli emas. Mavjud: %n.'],
 iv_err_over:['%m exceeds the unshipped balance of the order.','%m превышает неотгруженный остаток заказа.','%m buyurtmaning jo‘natilmagan qoldig‘idan oshib ketdi.'],
 iv_err_ordcus:['The customer must match the order.','Покупатель должен совпадать с заказом.','Mijoz buyurtmadagi mijoz bilan bir xil bo‘lishi kerak.'],
 iv_err_ordgone:['The order of this note is deleted. Restore the order first.','Заказ этой накладной удалён. Сначала восстановите заказ.','Bu nakladnoyning buyurtmasi o‘chirilgan. Avval buyurtmani tiklang.'],
 iv_ord_lbl:['Based on order (optional)','На основании заказа (необязательно)','Buyurtma asosida (ixtiyoriy)'],
 iv_none:['No order','Без заказа','Buyurtmasiz'],
 iv_view:['View','Просмотр','Ko‘rish'],
 iv_form:['Delivery note %s dated %d','Расходная накладная %s от %d','%s-sonli chiqim nakladnoyi, %d'],
 iv_to:['Buyer','Покупатель','Xaridor'],
 iv_gave:['Released by','Отпустил','Topshirdi'],
 iv_took:['Received by','Получил','Qabul qildi'],
 iv_del_q:['Delete this delivery note? It stays in the journal as Deleted and the goods return to the warehouse.','Удалить накладную? Она останется в журнале со статусом Удалён, товар вернётся на склад.','Nakladnoy o‘chirilsinmi? U jurnalda “o‘chirilgan” holatida qoladi, tovar omborga qaytadi.'],
 sv_avail:['In stock: %n','На складе: %n','Omborda: %n'],
 cur:['UZS','сум','so‘m'],
 pd_price:['Selling price, UZS','Цена продажи, сум','Sotuv narxi, so‘m']
};
Object.keys(SX).forEach(function(k){T.en[k]=SX[k][0];T.ru[k]=SX[k][1];T.uz[k]=SX[k][2]});
function tf(k,a){a=a||{};return t(k).replace('%m',a.m||'').replace('%w',a.w||'').replace('%n',a.n!=null?a.n:'').replace('%s',a.s||'').replace('%d',a.d||'')}
var MENUS={};
function mi(act,ico,label,cls){return '<button type="button" role="menuitem" data-act="'+act+'"'+(cls?' class="'+cls+'"':'')+'>'+ico+label+'</button>'}
function dfmt(d){return pad2(d.getDate())+'.'+pad2(d.getMonth()+1)+'.'+d.getFullYear()}
function toDay(d){return d.getFullYear()+'-'+pad2(d.getMonth()+1)+'-'+pad2(d.getDate())}
function pday(v){if(!v)return null;var d=new Date(v+'T00:00:00');return isNaN(d.getTime())?null:d}
function money(n){
  n=Math.round((n||0)*100)/100;
  var a=n.toFixed(2).split('.');
  return a[0].replace(/\B(?=(\d{3})+(?!\d))/g,'\u00a0')+','+a[1];
}
function parseMoney(v){var x=parseFloat(String(v).replace(/[^\d,]/g,'').replace(',','.'));return x>0?x:0}
function moneyType(el){
  var v=el.value,pos=el.selectionStart==null?v.length:el.selectionStart;
  var before=v.slice(0,pos).replace(/[^\d,.]/g,'').length;
  var s=v.replace(/\./g,',').replace(/[^\d,]/g,''),ci=s.indexOf(','),ip=ci<0?s:s.slice(0,ci),dp=ci<0?null:s.slice(ci+1).replace(/,/g,'').slice(0,2);
  ip=ip.replace(/^0+(?=\d)/,'');
  var out=ip.replace(/\B(?=(\d{3})+(?!\d))/g,'\u00a0')+(dp===null?'':','+dp),c=0,i=0;
  el.value=out;
  for(;i<out.length&&c<before;i++){if(/[\d,]/.test(out.charAt(i)))c++}
  if(el.setSelectionRange){try{el.setSelectionRange(i,i)}catch(e){}}
}
function rsum(rows){return rows.reduce(function(s,r){return s+(r.q>0&&r.pr>0?r.q*r.pr:0)},0)}
function rqty(rows){return rows.reduce(function(s,r){return s+(r.q>0?r.q:0)},0)}
function rtext(rows){return rows.map(function(r){return PRODUCTS[r.p]+' × '+r.q}).join(', ')}
function blankSR(){return [{p:-1,q:0,pr:0,t:''}]}
function cpRows(rows){return rows.map(function(r){return {p:r.p,q:r.q,pr:r.pr,t:''}})}

/* customers */
var CUS=[];
function cidx(name){var n=String(name||'').trim().toLowerCase();if(!n)return -1;for(var i=0;i<CUS.length;i++){if(!CUS[i].gone&&CUS[i].n.toLowerCase()===n)return i}return -1}
var ORD=[],INV=[];
function cuUsed(i){return ORD.concat(INV).some(function(d){return d.cus===i})||(typeof FIN!=='undefined'&&FIN.some(function(d){return d.cus===i}))}
function findO(no){for(var i=0;i<ORD.length;i++){if(ORD[i].no===no)return ORD[i]}return null}
function findI(no){for(var i=0;i<INV.length;i++){if(INV[i].no===no)return INV[i]}return null}

/* orders: shipped balance comes from posted delivery notes */
function shippedMap(o,except){var m={};INV.forEach(function(v){if(v.status!=='posted'||v.ord!==o.no||v.no===except)return;v.rows.forEach(function(r){m[r.p]=(m[r.p]||0)+r.q})});return m}
function ordNeed(o){var m={};o.rows.forEach(function(r){m[r.p]=(m[r.p]||0)+r.q});return m}
function ordRemain(o,except){var sh=shippedMap(o,except),need=ordNeed(o),m={};Object.keys(need).forEach(function(k){var r=need[k]-(sh[k]||0);if(r>0)m[k]=r});return m}
function ordShipped(o){var sh=shippedMap(o),need=ordNeed(o),s=0,n=0;Object.keys(need).forEach(function(k){s+=Math.min(sh[k]||0,need[k]);n+=need[k]});return [s,n]}
function ordState(o){if(o.status==='deleted')return 'deleted';var x=ordShipped(o);return x[0]>=x[1]?'shipped':(x[0]>0?'partial':'new')}
var OSL={'new':['draft','os_new'],partial:['pending','os_partial'],shipped:['posted','os_shipped'],deleted:['deleted','deleted']};

/* delivery notes move finished goods out of the warehouse */
function invShort(site,rows){var need={};rows.forEach(function(r){need[r.p]=(need[r.p]||0)+r.q});var ks=Object.keys(need);for(var i=0;i<ks.length;i++){var it=ITEM_BY[PRODUCTS[ks[i]]],have=it?it.st[site]:0;if(need[ks[i]]>have)return {m:PRODUCTS[ks[i]],w:WH[site],n:fmt(have)}}return null}

/* shared row editor */
function fillLists(){
  $('#plist').innerHTML=PRODUCTS.filter(function(n,i){return !PGONE[i]}).map(function(n){return '<option value="'+esc(n)+'"></option>'}).join('');
  $('#clist').innerHTML=CUS.filter(function(c){return !c.gone}).map(function(c){return '<option value="'+esc(c.n)+'"></option>'}).join('');
}
var OS={no:null,rows:blankSR(),msg:null},IS={no:null,view:null,rows:blankSR(),site:0,ord:'',msg:null};
function SS(k){return k==='od'?OS:IS}
function rowHint(k,r){
  var h=[];
  if(k==='iv'&&r.p>=0){var it=ITEM_BY[PRODUCTS[r.p]];h.push(tf('sv_avail',{n:fmt(it?it.st[IS.site]:0)}))}
  if(r.q>0&&r.pr>0)h.push(fmt(r.q)+' '+uname(punit(r.p))+' \u00d7 '+money(r.pr)+' = '+money(r.q*r.pr)+' '+t('cur'));
  return h.join(' \u00b7 ');
}
function srowsHtml(k,rows){
  return rows.map(function(r,i){
    return '<div class="srow"><input id="'+k+'p'+i+'" data-i="'+i+'" data-k="p" type="text" data-pick="prod" role="combobox" aria-autocomplete="list" autocomplete="off" spellcheck="false" placeholder="'+t('p_search')+'" aria-label="'+t('p_products')+'" value="'+esc(r.p>=0?PRODUCTS[r.p]:(r.t||''))+'">'+
     '<input id="'+k+'q'+i+'" data-i="'+i+'" data-k="q" type="number" min="1" step="1" inputmode="numeric" placeholder="'+t('p_qty')+'" aria-label="'+t('p_qty')+'" value="'+(r.q>0?r.q:'')+'">'+
     '<input id="'+k+'r'+i+'" data-i="'+i+'" data-k="pr" type="text" inputmode="decimal" autocomplete="off" placeholder="0,00" aria-label="'+t('c_price')+'" value="'+(r.pr>0?money(r.pr):'')+'">'+
     (rows.length>1?'<button type="button" class="link" data-rm="'+i+'" aria-label="'+t('p_rm')+'">×</button>':'<span></span>')+
     '<span class="hint">'+rowHint(k,r)+'</span></div>';
  }).join('');
}
function rowsUnit(rows){var s={};rows.forEach(function(r){if(r.p>=0)s[punit(r.p)]=1});var k=Object.keys(s);return k.length===1?' '+uname(+k[0]):''}
function updTotal(k){var rr=SS(k).rows;$('#'+k+'total').textContent=t('p_total')+': '+fmt(rqty(rr))+rowsUnit(rr)+' \u00b7 '+money(rsum(rr))+' '+t('cur')}
function serr(k,key,a){var S=SS(k),e=$('#'+(k==='od'?'oderr':'iverr'));S.msg=key?{key:key,a:a}:null;e.textContent=key?tf(key,a):''}
function renderSRows(k){$('#'+k+'rows').innerHTML=srowsHtml(k,SS(k).rows);updTotal(k)}
function rowsInput(k,e){
  var el=e.target,kk=el.dataset.k;if(!kk)return;
  var S=SS(k),i=+el.dataset.i,r=S.rows[i];
  if(kk==='p'){
    var p=pidx(el.value);r.p=p;r.t=el.value;
  }else if(kk==='pr'){moneyType(el);r.pr=parseMoney(el.value)}
  else{var v=parseFloat(el.value);v=v>0?v:0;r[kk]=Math.floor(v)}
  var h=$('#'+k+'rows').children[i].querySelector('.hint');if(h)h.textContent=rowHint(k,r);
  updTotal(k);serr(k,null);
}
function rowsClick(k,e){
  var b=e.target.closest('[data-rm]');if(!b)return;var S=SS(k);
  if(S.rows.length>1){S.rows.splice(+b.dataset.rm,1);renderSRows(k)}
}
function addRow(k){var S=SS(k);S.rows.push({p:-1,q:0,pr:0,t:''});renderSRows(k);var l=$('#'+k+'p'+(S.rows.length-1));if(l)l.focus()}
function checkRows(k){
  var S=SS(k);
  if(S.rows.some(function(r){return r.p<0})){serr(k,'err_prod');return false}
  if(!S.rows.every(function(r){return r.q>0})){serr(k,'err_qty');return false}
  if(!S.rows.every(function(r){return r.pr>0})){serr(k,'err_price');return false}
  return true;
}
['od','iv'].forEach(function(k){
  $('#'+k+'rows').addEventListener('input',function(e){rowsInput(k,e)});
  $('#'+k+'rows').addEventListener('click',function(e){rowsClick(k,e)});
  $('#'+k+'add').addEventListener('click',function(){addRow(k)});
});

