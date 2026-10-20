/* Settings > Company: our own details printed on the waybill, and the waybill wording strings */
var COX={
 tab_company:['Company','Компания','Kompaniya'],
 co_h:['Details printed on the waybill','Реквизиты для печати накладной','Yuk xatida chiqadigan rekvizitlar'],
 co_name:['Company name','Название компании','Kompaniya nomi'],
 co_address:['Address','Адрес','Manzil'],
 co_postcode:['Postcode','Почтовый индекс','Pochta indeksi'],
 co_okonh:['OKONH','ОКОНХ','OKONX'],
 co_account:['Bank account number','Расчётный счёт','Hisob raqami'],
 co_bank:['Bank and branch','Банк и филиал','Bank va filiali'],
 co_mfo:['MFO','МФО','MFO'],
 co_inn:['INN (tax number)','ИНН','INN'],
 co_phone:['Phone','Телефон','Telefon'],
 co_receive_note:['Note after “Received”','Примечание после «Получил»','«Oldim» dan keyingi izoh'],
 co_saved:['Company details saved.','Реквизиты сохранены.','Rekvizitlar saqlandi.'],
 co_logo_note:['The Prime Beton logo is printed at the top of the waybill.','Вверху накладной печатается логотип Prime Beton.','Yuk xatining tepasida Prime Beton logotipi chop etiladi.'],
 iv_drv:['Driver','Водитель','Haydovchi'],
 iv_veh:['Vehicle number','Номер машины','Mashina raqami'],
 iv_print:['Print waybill','Печать накладной','Yuk xatini chop etish'],
 iv_waybill:['Waybill (print)','Накладная (печать)','Yuk xati (chop etish)'],
 iv_print_after:['Open the waybill for printing after saving','Открыть накладную для печати после сохранения','Saqlagach yuk xatini chop etish uchun ochish']
};
Object.keys(COX).forEach(function(k){T.en[k]=COX[k][0];T.ru[k]=COX[k][1];T.uz[k]=COX[k][2]});

var CO={data:null,msg:null,err:false,fields:['name','address','postcode','okonh','account','bank','mfo','inn','phone','receive_note']};
function coLoad(){
  return api('GET','/company').then(function(d){CO.data=d;if(ST.tab==='company')renderCompany()},function(){});
}
function renderCompany(){
  var el=$('#stcompany');if(!el)return;
  if(ST.tab!=='company'){el.hidden=true;return}
  el.hidden=false;
  var d=CO.data||{},h='<h2>'+t('co_h')+'</h2><p class="note">'+t('co_logo_note')+'</p><div class="fgrid">';
  CO.fields.forEach(function(k){
    var wide=k==='address'||k==='bank'||k==='receive_note';
    h+='<div class="field"'+(wide?' style="grid-column:1/-1"':'')+'><label for="co_'+k+'">'+t('co_'+k)+'</label><input id="co_'+k+'" data-k="'+k+'" type="text" autocomplete="off" value="'+esc(d[k]||'')+'"></div>';
  });
  h+='</div><div class="pbtns"><button type="button" class="btn primary sm" id="cosave">'+t('sp_save')+'</button></div><p class="msg'+(CO.msg?(CO.err?' bad':' ok'):'')+'" id="comsg" role="status">'+(CO.msg?esc(CO.msg):'')+'</p>';
  el.innerHTML=h;
}
var _renderSet=renderSet;
renderSet=function(){
  _renderSet();
  var co=ST.tab==='company';
  var nb=$('#stnew'),tb=$('#sttblbox'),fm=$('#stform');
  if(nb)nb.hidden=co;if(tb)tb.hidden=co;if(co&&fm){fm.hidden=true;fm.innerHTML=''}
  if(co&&!CO.data)coLoad();
  renderCompany();
};
document.addEventListener('click',function(e){
  var b=e.target.closest&&e.target.closest('#cosave');if(!b)return;
  var body={};CO.fields.forEach(function(k){var i=$('#co_'+k);body[k]=i?i.value:''});
  b.disabled=true;
  api('PUT','/company',body).then(function(d){CO.data=d;CO.msg=t('co_saved');CO.err=false;renderCompany()},function(er){CO.msg=apiErr(er);CO.err=true;renderCompany()});
});
