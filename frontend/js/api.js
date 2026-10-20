/* API client: one place that talks to the server */
var API={base:(typeof window!=='undefined'&&window.API_BASE)||'/api',token:null};
try{API.token=sessionStorage.getItem('daybook-token')||localStorage.getItem('daybook-token')}catch(e){}
function apiSetToken(tok,keep){
  API.token=tok||null;
  try{
    localStorage.removeItem('daybook-token');sessionStorage.removeItem('daybook-token');
    if(tok)(keep?localStorage:sessionStorage).setItem('daybook-token',tok);
  }catch(e){}
}
/* Dates travel as local wall-clock time without a zone, so what the user typed is what comes back. */
function isoLocal(d){
  var p=function(n){return String(n).padStart(2,'0')};
  return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate())+'T'+p(d.getHours())+':'+p(d.getMinutes())+':'+p(d.getSeconds());
}
function fromIso(s){return s?new Date(s):null}

/* Double clicks and impatient repeated clicks: the same create request (same path, same data) that is still running, or that
   succeeded a moment ago, is not sent a second time; the caller simply gets the first answer. A failed request is forgotten at once,
   so pressing Save again after an error works. Sign-in, AI questions and Telegram codes are left alone. */
var APIDUP={ttl:8000,seen:{}};
function api(method,path,body){
  if(method!=='POST'||/^\/(auth|ai|telegram)/.test(path))return apiSend(method,path,body);
  var key=path+'|'+(body===undefined?'':JSON.stringify(body)),now=Date.now(),hit=APIDUP.seen[key];
  if(hit&&(!hit.done||(body!==undefined&&now-hit.t<APIDUP.ttl)))return hit.p;
  for(var k in APIDUP.seen){var o=APIDUP.seen[k];if(o.done&&now-o.t>APIDUP.ttl)delete APIDUP.seen[k]}
  var rec={done:false,t:now};
  rec.p=apiSend(method,path,body).then(function(r){rec.done=true;rec.t=Date.now();return r},function(e){delete APIDUP.seen[key];throw e});
  APIDUP.seen[key]=rec;
  return rec.p;
}
function apiSend(method,path,body){
  var opt={method:method,headers:{}};
  if(API.token)opt.headers['Authorization']='Bearer '+API.token;
  if(body!==undefined){opt.headers['Content-Type']='application/json';opt.body=JSON.stringify(body)}
  return fetch(API.base+path,opt).then(function(r){
    if(r.status===204)return null;
    return r.json().catch(function(){return null}).then(function(j){
      if(r.ok)return j;
      var d=(j&&j.detail)||{};
      if(typeof d==='string')d={code:'error',message:d,params:{}};
      if(Array.isArray(d))d={code:'invalid',message:'Invalid data',params:{}};
      var e=new Error(d.message||'Request failed');
      e.code=d.code||'error';e.params=d.params||{};e.status=r.status;
      if(e.code==='2fa_required'&&location.hash!=='#security'){location.hash='security'}
      if(r.status===401&&path!=='/auth/login'&&typeof sessionExpired==='function')sessionExpired();
      throw e;
    });
  },function(){
    var e=new Error('Network error');e.code='network';e.params={};e.status=0;throw e;
  });
}

/* server error codes -> text in the current language */
var APIX={
 network:['The server cannot be reached. Check the connection and try again.','Сервер недоступен. Проверьте соединение и повторите.','Serverga ulanib bo‘lmadi. Ulanishni tekshirib, qayta urinib ko‘ring.'],
 error:['Something went wrong. Try again.','Что-то пошло не так. Повторите попытку.','Xatolik yuz berdi. Qayta urinib ko‘ring.'],
 unauthorized:['Your session has ended. Sign in again.','Сессия завершена. Войдите снова.','Sessiya tugadi. Qayta kiring.'],
 forbidden:['Your role cannot do this.','Ваша роль не позволяет это сделать.','Rolingiz bu amalga ruxsat bermaydi.'],
 bad_login:['Wrong username or password.','Неверное имя пользователя или пароль.','Foydalanuvchi nomi yoki parol noto‘g‘ri.'],
 invalid:['Check the entered data.','Проверьте введённые данные.','Kiritilgan ma’lumotlarni tekshiring.'],
 not_found:['The record was not found. It may have been deleted.','Запись не найдена. Возможно, она удалена.','Yozuv topilmadi. U o‘chirilgan bo‘lishi mumkin.'],
 insufficient_stock:['Not enough {item} in {warehouse}: {available} {unit} available.','Недостаточно «{item}» на складе {warehouse}: доступно {available} {unit}.','{warehouse} omborida {item} yetarli emas: {available} {unit} mavjud.'],
 cash_negative:['The cash desk {account} cannot go below zero.','Остаток кассы «{account}» не может быть отрицательным.','{account} kassasi qoldig‘i manfiy bo‘lishi mumkin emas.'],
 bank_negative:['Not enough money on {account}: {available} available.','Недостаточно денег на счёте «{account}»: доступно {available}.','{account} hisobida pul yetarli emas: {available} mavjud.'],
 over_order:['{item}: only {left} left to ship on the order.','{item}: по заказу осталось отгрузить только {left}.','{item}: buyurtma bo‘yicha faqat {left} jo‘natish qoldi.'],
 order_below_shipped:['{item}: {shipped} already shipped, the order row cannot be smaller.','{item}: уже отгружено {shipped}, строку заказа нельзя уменьшить.','{item}: {shipped} jo‘natilgan, buyurtma qatorini kamaytirib bo‘lmaydi.'],
 order_has_invoices:['The order has delivery notes, so it cannot be changed this way.','По заказу есть накладные, поэтому так изменить его нельзя.','Buyurtma bo‘yicha nakladnoylar bor, shuning uchun bunday o‘zgartirib bo‘lmaydi.'],
 order_customer_mismatch:['The order belongs to another customer.','Заказ принадлежит другому покупателю.','Buyurtma boshqa mijozga tegishli.'],
 doc_deleted:['The document is deleted. Restore it first.','Документ удалён. Сначала восстановите его.','Hujjat o‘chirilgan. Avval tiklang.'],
 duplicate:['{name} already exists.','«{name}» уже существует.','«{name}» allaqachon mavjud.'],
 item_in_use:['{name} is used in documents and cannot be changed or deleted.','«{name}» используется в документах, изменить или удалить нельзя.','{name} hujjatlarda ishlatilgan, o‘zgartirib yoki o‘chirib bo‘lmaydi.'],
 item_has_stock:['{name} still has stock and cannot be deleted.','«{name}» ещё есть на складе, удалить нельзя.','{name} omborda qoldig‘i bor, o‘chirib bo‘lmaydi.'],
 material_in_specs:['{name} is used in a specification.','«{name}» используется в спецификации.','{name} spetsifikatsiyada ishlatilgan.'],
 unit_in_use:['The unit {name} is used by products or materials.','Единица «{name}» используется в продукции или материалах.','{name} birligi mahsulot yoki materialda ishlatilgan.'],
 last_unit:['At least one unit of measure must remain.','Должна остаться хотя бы одна единица измерения.','Kamida bitta o‘lchov birligi qolishi kerak.'],
 warehouse_has_stock:['{name} still holds stock.','На складе «{name}» ещё есть остатки.','{name} omborida qoldiq bor.'],
 warehouse_in_use:['Documents use the warehouse {name}.','Склад «{name}» используется в документах.','{name} ombori hujjatlarda ishlatilgan.'],
 plant_locked:['Production plants cannot be deleted.','Производственные завода удалить нельзя.','Ishlab chiqarish zavodlarini o‘chirib bo‘lmaydi.'],
 account_in_use:['Money documents use this account.','Этот счёт используется в денежных документах.','Bu hisob pul hujjatlarida ishlatilgan.'],
 account_has_balance:['Zero the opening balance before deleting the account.','Обнулите начальный остаток перед удалением счёта.','Hisobni o‘chirishdan oldin boshlang‘ich qoldiqni nolga tushiring.'],
 customer_in_use:['{name} has orders, delivery notes or payments and cannot be deleted.','У «{name}» есть заказы, накладные или оплаты, удалить нельзя.','{name} uchun buyurtma, nakladnoy yoki to‘lov bor, o‘chirib bo‘lmaydi.'],
 supplier_in_use:['{name} has receipts or payments and cannot be deleted.','У «{name}» есть поступления или оплаты, удалить нельзя.','{name} uchun kirim yoki to‘lov bor, o‘chirib bo‘lmaydi.'],
 name_required:['Enter the name.','Введите название.','Nomini kiriting.'],
 no_rows:['Add at least one row.','Добавьте хотя бы одну строку.','Kamida bitta qator qo‘shing.'],
 same_account:['Choose two different accounts.','Выберите два разных счёта.','Ikki xil hisobni tanlang.'],
 bad_article:['This article does not fit the document type.','Эта статья не подходит к виду документа.','Bu modda hujjat turiga mos kelmaydi.'],
 account_required:['Choose an account.','Выберите счёт.','Hisobni tanlang.'],
 customer_required:['Choose a customer.','Выберите покупателя.','Mijozni tanlang.'],
 supplier_required:['Choose a supplier.','Выберите поставщика.','Yetkazib beruvchini tanlang.'],
 unknown_item:['The item no longer exists.','Позиции больше нет.','Pozitsiya endi mavjud emas.'],
 unknown_unit:['The unit no longer exists.','Единицы больше нет.','Birlik endi mavjud emas.'],
 unknown_material:['The material no longer exists.','Материала больше нет.','Material endi mavjud emas.'],
 raw:['%m','%m','%m']
};
Object.keys(APIX).forEach(function(k){T.en['api_'+k]=APIX[k][0];T.ru['api_'+k]=APIX[k][1];T.uz['api_'+k]=APIX[k][2]});

function apiText(v){
  if(v&&typeof v==='object')return v[lang]||v.en||v.uz||'';
  if(typeof v==='number')return fmt(v);
  return v==null?'':String(v);
}
function apiErr(e){
  var code=(e&&e.code)||'error',p=Object.assign({},(e&&e.params)||{});
  if(code==='weak_password'&&p.reason&&(T[lang]['api_weak_'+p.reason]||T.en['api_weak_'+p.reason]))code='weak_'+p.reason;
  if(p.item_id!=null&&typeof itemNameById==='function')p.item=itemNameById(p.item_id)||'';
  if(p.item&&typeof p.item==='object')p.item=apiText(p.item);
  var s=T[lang]['api_'+code]||T.en['api_'+code];
  if(!s)return T[lang].api_error||(e&&e.message)||'Error';
  return s.replace(/\{(\w+)\}/g,function(_,n){return apiText(p[n])});
}
/* message object for the existing `{key,m,err}` message areas */
function apiMsg(e){return {key:'api_raw',m:apiErr(e),err:true}}

/* run an API call, reload server data, then continue. Failures are shown instead of thrown. */
function srv(call,ok,fail){
  var failed=false;
  function bad(e){failed=true;if(fail)fail(e);else toast(apiErr(e),true)}
  return call.then(function(r){return Store.load().then(function(){return r},function(e){bad(e)})},bad).then(function(r){if(!failed&&ok)ok(r)});
}
