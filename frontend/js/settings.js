/* reference data: warehouses, bank accounts, cash desks, units of measure */
var SDX={
 nav_set:['Settings','Настройки','Sozlamalar'],
 grp_set:['Administration','Администрирование','Boshqaruv'],
 set_h:['Reference data','Справочники','Spravochniklar'],
 set_note:['Warehouses, bank accounts, cash desks and units of measure used across the system.','Склады, банковские счета, кассы и единицы измерения, которые используются во всей системе.','Butun tizimda ishlatiladigan omborlar, bank hisoblari, kassalar va o‘lchov birliklari.'],
 tab_wh:['Warehouses','Склады','Omborlar'],
 tab_bank:['Bank accounts','Банковские счета','Bank hisoblari'],
 tab_cash:['Cash desks','Кассы','Kassalar'],
 tab_unit:['Units of measure','Единицы измерения','O‘lchov birliklari'],
 st_new_wh:['New warehouse','Новый склад','Yangi ombor'],
 st_new_bank:['New bank account','Новый банковский счёт','Yangi bank hisobi'],
 st_new_cash:['New cash desk','Новая касса','Yangi kassa'],
 st_new_unit:['New unit of measure','Новая единица измерения','Yangi o‘lchov birligi'],
 st_edit_wh:['Edit warehouse','Изменить склад','Omborni tahrirlash'],
 st_edit_bank:['Edit bank account','Изменить банковский счёт','Bank hisobini tahrirlash'],
 st_edit_cash:['Edit cash desk','Изменить кассу','Kassani tahrirlash'],
 st_edit_unit:['Edit unit of measure','Изменить единицу измерения','O‘lchov birligini tahrirlash'],
 st_name:['Name','Наименование','Nomi'],
 st_num:['Account number','Номер счёта','Hisob raqami'],
 st_open:['Opening balance, UZS','Начальный остаток, сум','Boshlang‘ich qoldiq, so‘m'],
 st_bal:['Balance, UZS','Остаток, сум','Qoldiq, so‘m'],
 st_type:['Type','Тип','Turi'],
 st_ws:['Plant','Завод','Zavod'],
 st_store:['Warehouse','Склад','Ombor'],
 st_items:['Items in stock','Позиций на остатке','Qoldiqdagi pozitsiyalar'],
 st_uz:['Name (Uzbek)','Название (узбекский)','Nomi (o‘zbekcha)'],
 st_ru:['Name (Russian)','Название (русский)','Nomi (ruscha)'],
 st_en:['Name (English)','Название (английский)','Nomi (inglizcha)'],
 st_used:['Used by','Используется','Ishlatilgan'],
 st_unit:['Unit of measure','Единица измерения','O‘lchov birligi'],
 st_saved:['%m saved.','%m сохранено.','%m saqlandi.'],
 st_deleted:['%m deleted.','%m удалено.','%m o‘chirildi.'],
 st_err_name:['Enter a name.','Укажите наименование.','Nomini kiriting.'],
 st_err_dup:['This name already exists.','Такое наименование уже есть.','Bunday nom allaqachon bor.'],
 st_err_used:['%m is in use and cannot be deleted.','%m используется, удалить нельзя.','%m ishlatilmoqda, o‘chirib bo‘lmaydi.'],
 st_err_ws:['%m is a production plant. It can be renamed but not deleted.','%m — производственный завод. Его можно переименовать, но нельзя удалить.','%m ishlab chiqarish zavodi. Uning nomini o‘zgartirish mumkin, o‘chirib bo‘lmaydi.'],
 st_err_neg:['The balance of %m would become negative.','Остаток по «%m» станет отрицательным.','“%m” qoldig‘i manfiy bo‘lib qoladi.'],
 st_err_last:['At least one unit of measure must remain.','Должна остаться хотя бы одна единица измерения.','Kamida bitta o‘lchov birligi qolishi kerak.'],
 st_del_q:['Delete this entry?','Удалить эту запись?','Bu yozuv o‘chirilsinmi?'],
 bz_bank:['Bank accounts','Банковские счета','Bank hisoblari'],
 bz_cashd:['Cash desks','Кассы','Kassalar'],
 bz_n_acc:['%n accounts','Счетов: %n','Hisoblar: %n'],
 bz_accs:['Balances by account','Остатки по счетам','Hisoblar bo‘yicha qoldiq'],
 rc_item_ph:['Choose a material or product','Выберите материал или продукцию','Material yoki mahsulotni tanlang'],
 rc_items:['Items','Позиции','Pozitsiyalar'],
 unit_dona:['pcs','шт','dona']
};
Object.keys(SDX).forEach(function(k){T.en[k]=SDX[k][0];T.ru[k]=SDX[k][1];T.uz[k]=SDX[k][2]});
T.en.rc_err_mat='Choose a material or product from the list.';T.ru.rc_err_mat='Выберите материал или продукцию из списка.';T.uz.rc_err_mat='Material yoki mahsulotni ro‘yxatdan tanlang.';
T.en.rc_err_stock='%m was already used: only %n left in %w, the receipt cannot be reduced.';T.ru.rc_err_stock='%m уже израсходован: на складе %w осталось %n, поступление уменьшить нельзя.';T.uz.rc_err_stock='%m allaqachon ishlatilgan: %w omborida %n qoldi, kirimni kamaytirib bo‘lmaydi.';
T.en.rc_note='Materials or finished products received from suppliers. Posting a receipt increases the warehouse stock and what we owe the supplier.';
T.ru.rc_note='Материалы или готовая продукция от поставщиков. При проведении остаток склада и наш долг поставщику увеличиваются.';
T.uz.rc_note='Yetkazib beruvchidan material yoki tayyor mahsulot kirimi. O‘tkazilganda ombor qoldig‘i va yetkazib beruvchi oldidagi qarzimiz oshadi.';
var ST={tab:'wh',form:null,msg:null};
function whStockN(i){return ITEMS.filter(function(x){return x.st[i]>0}).length}
function unitUsed(u){return ITEMS.filter(function(x){return iu(x)===u}).length}
function stRows(){
  var a=[];
  if(ST.tab==='wh')whIdx().forEach(function(i){a.push(i)});
  else if(ST.tab==='unit')UNITS.forEach(function(x,i){if(!x.gone)a.push(i)});
  else ACC.forEach(function(x,i){if(!x.gone&&x.t===ST.tab)a.push(i)});
  return a;
}
function stName(i){return ST.tab==='wh'?WH[i]:ST.tab==='unit'?uname(i):aname(i)}
function renderStForm(){
  var el=$('#stform'),f=ST.form;
  if(!f){el.hidden=true;el.innerHTML='';return}
  el.hidden=false;
  var h='<h2>'+t((f.i<0?'st_new_':'st_edit_')+ST.tab)+'</h2><div class="fgrid">';
  if(ST.tab==='unit'){
    ['uz','ru','en'].forEach(function(l){h+='<div class="field"><label for="stn_'+l+'">'+t('st_'+l)+'</label><input id="stn_'+l+'" data-k="'+l+'" type="text" autocomplete="off" value="'+esc(f[l])+'"></div>'});
  }else{
    h+='<div class="field"><label for="stname">'+t('st_name')+'</label><input id="stname" data-k="name" type="text" autocomplete="off" value="'+esc(f.name)+'"></div>';
    if(ST.tab==='wh'&&f.i<0)h+='<div class="field"><label for="stws">'+t('st_type')+'</label><select id="stws" data-k="ws"><option value="0"'+(f.ws?'':' selected')+'>'+t('st_store')+'</option><option value="1"'+(f.ws?' selected':'')+'>'+t('st_ws')+'</option></select></div>';
    if(ST.tab==='bank')h+='<div class="field"><label for="stnum">'+t('st_num')+'</label><input id="stnum" data-k="num" type="text" inputmode="numeric" autocomplete="off" value="'+esc(f.num)+'"></div>';
    if(ST.tab!=='wh')h+='<div class="field"><label for="stopen">'+t('st_open')+'</label><input id="stopen" data-k="open" type="text" inputmode="decimal" autocomplete="off" placeholder="0,00" value="'+(f.open>0?money(f.open):'')+'"></div>';
  }
  h+='</div><div class="pbtns"><button type="button" class="btn primary sm" id="stsave">'+t('sp_save')+'</button><button type="button" class="btn ghost sm" id="stcancel">'+t('m_cancel')+'</button></div><p class="msg bad" id="stferr" role="alert">'+(f.err?tf(f.err,{m:f.errm||''}):'')+'</p>';
  el.innerHTML=h;
}
function renderSet(){
  closeMenu();
  document.querySelectorAll('#sttabs button').forEach(function(b){b.textContent=t('tab_'+b.dataset.tab);b.setAttribute('aria-pressed',String(b.dataset.tab===ST.tab))});
  var tab=ST.tab,rows=stRows(),head,body;
  if(tab==='wh'){
    head='<th>'+t('st_name')+'</th><th>'+t('st_type')+'</th><th class="num">'+t('st_items')+'</th>';
    body=rows.map(function(i){return '<tr><td>'+esc(WH[i])+'</td><td>'+t(i<SITES.length?'st_ws':'st_store')+'</td><td class="num">'+whStockN(i)+'</td><td class="act">'+kebabHtml('st','wh:'+i,WH[i])+'</td></tr>'});
  }else if(tab==='unit'){
    head='<th>'+t('st_uz')+'</th><th>'+t('st_ru')+'</th><th>'+t('st_en')+'</th><th class="num">'+t('st_used')+'</th>';
    body=rows.map(function(i){var n=UNITS[i].n;return '<tr><td>'+esc(n.uz)+'</td><td>'+esc(n.ru)+'</td><td>'+esc(n.en)+'</td><td class="num">'+unitUsed(i)+'</td><td class="act">'+kebabHtml('st','unit:'+i,uname(i))+'</td></tr>'});
  }else{
    head='<th>'+t('st_name')+'</th>'+(tab==='bank'?'<th>'+t('st_num')+'</th>':'')+'<th class="num">'+t('st_open')+'</th><th class="num">'+t('st_bal')+'</th>';
    body=rows.map(function(i){var a=ACC[i];return '<tr><td>'+esc(aname(i))+'</td>'+(tab==='bank'?'<td class="mono">'+esc(a.num||'–')+'</td>':'')+'<td class="num">'+money(a.open)+'</td><td class="num"><b>'+money(accBal(i))+'</b></td><td class="act">'+kebabHtml('st',tab+':'+i,aname(i))+'</td></tr>'});
  }
  var cols=head.split('</th>').length;
  $('#sttbl').innerHTML='<thead><tr>'+head+'<th><span class="vh">'+t('m_actions')+'</span></th></tr></thead><tbody>'+(body.length?body.join(''):'<tr><td class="empty" colspan="'+cols+'">'+t('it_empty')+'</td></tr>')+'</tbody>';
  renderStForm();
  var e=$('#stmsg');if(!ST.msg){e.className='msg';e.textContent=''}else{e.className='msg '+(ST.msg.err?'bad':'ok');e.textContent=tf(ST.msg.key,{m:ST.msg.m})}
}
function openSt(i){
  ST.msg=null;
  if(i===undefined)ST.form={i:-1,name:'',num:'',open:0,uz:'',ru:'',en:'',err:null};
  else if(ST.tab==='unit'){var n=UNITS[i].n;ST.form={i:i,uz:n.uz,ru:n.ru,en:n.en,err:null}}
  else if(ST.tab==='wh')ST.form={i:i,name:WH[i],err:null};
  else ST.form={i:i,name:aname(i),num:ACC[i].num||'',open:ACC[i].open,err:null};
  renderSet();var f=$('#stname')||$('#stn_uz');if(f)f.focus();
}
function saveSt(){
  var f=ST.form,tab=ST.tab,nm,call;
  function fail(k,m){f.err=k;f.errm=m||'';renderStForm()}
  function apiFail(e){fail('api_raw',apiErr(e))}
  if(tab==='unit'){
    var u={uz:f.uz.trim(),ru:f.ru.trim(),en:f.en.trim()},any=u.uz||u.ru||u.en;
    if(!any){return fail('st_err_name')}
    ['uz','ru','en'].forEach(function(l){if(!u[l])u[l]=any});
    var dup=UNITS.some(function(x,i){return i!==f.i&&(x.n.uz.toLowerCase()===u.uz.toLowerCase()||x.n.en.toLowerCase()===u.en.toLowerCase())});
    if(dup)return fail('st_err_dup');
    var ub={name:u.uz,name_ru:u.ru,name_en:u.en};
    call=f.i<0?api('POST','/units',ub):api('PUT','/units/'+UNID[f.i],ub);
    nm=u[lang];
  }else{
    nm=f.name.trim().replace(/\s+/g,' ');
    if(!nm)return fail('st_err_name');
    if(tab==='wh'){
      if(whIdx().some(function(i){return i!==f.i&&WH[i].toLowerCase()===nm.toLowerCase()}))return fail('st_err_dup');
      call=f.i<0?api('POST','/warehouses',{name:nm,is_workshop:!!+f.ws}):api('PUT','/warehouses/'+WHID[f.i],{name:nm});
    }else{
      if(accList(tab).some(function(i){return i!==f.i&&aname(i).toLowerCase()===nm.toLowerCase()}))return fail('st_err_dup');
      var open=+f.open>0?+f.open:0,num=(f.num||'').trim();
      if(f.i<0){
        call=api('POST','/accounts',{kind:tab,name_uz:nm,name_ru:nm,name_en:nm,number:num,opening_balance:open});
      }else{
        var a=ACC[f.i],old=a.n[lang],names={uz:a.n.uz,ru:a.n.ru,en:a.n.en};
        ['uz','ru','en'].forEach(function(l){if(names[l]===old)names[l]=nm});names[lang]=nm;
        call=api('PATCH','/accounts/'+a.id,{name_uz:names.uz,name_ru:names.ru,name_en:names.en,number:num,opening_balance:open});
      }
    }
  }
  srv(call,function(){ST.msg={key:'st_saved',m:nm};ST.form=null;afterSt()},apiFail);
}
function afterSt(){renderSet();renderWh();renderItems();renderFin();renderMatPage();renderRcEd();renderIvEd()}
function delSt(tab,i){
  var nm,call;
  if(tab==='wh'){nm=WH[i];call=api('DELETE','/warehouses/'+WHID[i]);if(ws===i)ws=-1}
  else if(tab==='unit'){nm=uname(i);call=api('DELETE','/units/'+UNID[i])}
  else{nm=aname(i);call=api('DELETE','/accounts/'+ACC[i].id)}
  srv(call,function(){ST.msg={key:'st_deleted',m:nm};afterSt()},function(e){ST.msg={key:'api_raw',m:apiErr(e),err:true};renderSet()});
}
$('#stnew').addEventListener('click',function(){openSt()});
$('#sttabs').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;ST.tab=b.dataset.tab;ST.form=null;ST.msg=null;renderSet()});
$('#stform').addEventListener('input',function(e){
  var f=ST.form,k=e.target.dataset.k;if(!f||!k)return;
  if(k==='open'){moneyType(e.target);f.open=parseMoney(e.target.value)}else f[k]=e.target.value;
  f.err=null;var er=$('#stferr');if(er)er.textContent='';
});
$('#stform').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;if(b.id==='stsave')saveSt();else if(b.id==='stcancel'){ST.form=null;renderStForm()}});
$('#sttbl').addEventListener('click',kebabClick);
MENUS.st={
  html:function(){return mi('edit',ICO.edit,t('m_edit'))+mi('del',ICO.del,t('m_del'),'del')},
  q:function(){return t('st_del_q')},
  act:function(a,no){var p=String(no).split(':'),i=+p[1];if(a==='edit')openSt(i);else if(a==='confirmdel')delSt(p[0],i)}
};


