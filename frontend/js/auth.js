/* release layer: roles, app shell, notifications, live dashboard, search */
var RX={
 em_doc:['No documents yet. Press Create to add the first one.','Документов пока нет. Нажмите «Создать», чтобы добавить первый.','Hozircha hujjat yo‘q. Birinchisini qo‘shish uchun «Yaratish» tugmasini bosing.'],
 em_cus:['No customers yet. Press Create to add the first one.','Покупателей пока нет. Нажмите «Создать», чтобы добавить первого.','Hozircha mijoz yo‘q. Birinchisini qo‘shish uchun «Yaratish» tugmasini bosing.'],em_sup:['No suppliers yet. Press Create to add the first one.','Поставщиков пока нет. Нажмите «Создать», чтобы добавить первого.','Hozircha yetkazib beruvchi yo‘q. Birinchisini qo‘shish uchun «Yaratish» tugmasini bosing.'],
 cu_flame:['Overdue debt','Просроченный долг','Muddati o‘tgan qarz'],bz_avg:['Average per day','В среднем в день','Kuniga o‘rtacha'],bz_gap:['Unpaid','Не оплачено','To‘lanmagan'],bz_ndoc:['Delivery notes','Накладных','Nakladnoylar'],
 show_data:['Day-by-day breakdown','Подробно по дням','Kunlar bo‘yicha batafsil'],
 dt_diff:['Difference','Разница','Farq'],dt_pct:['Plan met','Выполнение','Bajarilishi'],dt_def:['Defects','Брак','Brak'],
 dt_total:['Total / average','Итого / среднее','Jami / o‘rtacha'],dt_best:['Best day','Лучший день','Eng yaxshi kun'],
 dt_worst:['Weakest day','Слабый день','Eng sust kun'],dt_hit:['Days at or above plan','Дней с планом или выше','Rejaga yetgan kunlar'],
 dt_over:['Over plan','Выше плана','Rejadan yuqori'],dt_under:['Under plan','Ниже плана','Rejadan past'],
 grp_prod:['Production','Производство','Ishlab chiqarish'],
 grp_sales:['Sales','Продажи','Savdo'],
 grp_buy:['Purchasing','Закупки','Xaridlar'],
 grp_fin:['Finance','Финансы','Moliya'],
 role_admin:['Administrator','Администратор','Administrator'],
 role_director:['Director','Директор','Direktor'],
 role_prod:['Production manager','Начальник производства','Ishlab chiqarish boshlig‘i'],
 role_wh:['Storekeeper','Кладовщик','Omborchi'],
 role_sales:['Sales manager','Менеджер по продажам','Sotuv menejeri'],
 role_acc:['Accountant','Бухгалтер','Buxgalter'],
 login_otp_bad:['The code is wrong or already used.','Код неверный или уже использован.','Kod noto‘g‘ri yoki allaqachon ishlatilgan.'],otp_l:['Code from the authenticator app','Код из приложения-аутентификатора','Autentifikator ilovasidagi kod'],login_bad:['Wrong username or password.','Неверное имя пользователя или пароль.','Foydalanuvchi nomi yoki parol noto‘g‘ri.'],
 login_demo2:['Demo accounts. Pick a role to sign in.','Демо-аккаунты. Выберите роль для входа.','Demo hisoblar. Kirish uchun rolni tanlang.'],
 signout:['Sign out','Выйти','Chiqish'],
 signed_in:['Signed in as %m.','Вы вошли как %m.','%m sifatida kirdingiz.'],
 signed_out:['You signed out.','Вы вышли из системы.','Tizimdan chiqdingiz.'],
 ro_note:['View only','Только просмотр','Faqat ko‘rish'],
 noaccess:['Your role has no access to that section.','У вашей роли нет доступа к этому разделу.','Sizning rolingiz bu bo‘limga ruxsat bermaydi.'],
 srch:['Search','Поиск','Qidirish'],
 srch_ph:['Search pages, customers, orders, products…','Страницы, покупатели, заказы, продукция…','Sahifa, mijoz, buyurtma, mahsulot qidirish…'],
 srch_none:['Nothing found.','Ничего не найдено.','Hech narsa topilmadi.'],
 srch_hint:['↑ ↓ to move, Enter to open, Esc to close','↑ ↓ выбрать, Enter открыть, Esc закрыть','↑ ↓ tanlash, Enter ochish, Esc yopish'],
 cg_pages:['Pages','Страницы','Sahifalar'],
 cg_new:['Create','Создать','Yaratish'],
 cmd_ord:['New order','Новый заказ','Yangi buyurtma'],
 cmd_inv:['New delivery note','Новая расходная накладная','Yangi chiqim nakladnoyi'],
 cmd_rec:['New purchase receipt','Новое поступление','Yangi kirim nakladnoyi'],
 cmd_prod:['New production document','Новый документ производства','Yangi ishlab chiqarish hujjati'],
 nt_h:['Notifications','Уведомления','Bildirishnomalar'],
 nt_alerts:['Needs attention','Требует внимания','Diqqat talab qiladi'],
 nt_act:['Activity','Активность','Faoliyat'],
 nt_none:['All clear. Nothing needs your attention.','Всё в порядке. Ничего не требует внимания.','Hammasi joyida. Diqqat talab qiladigan narsa yo‘q.'],
 nt_noact:['Actions you take will appear here.','Здесь появятся ваши действия.','Qilgan amallaringiz shu yerda ko‘rinadi.'],
 nt_clear:['Clear activity','Очистить','Tozalash'],
 al_stock:['%n items are low or out of stock','%n позиций на исходе или закончились','%n ta pozitsiya tugayapti yoki tugagan'],
 al_over:['%n orders are past their delivery date','%n заказов просрочены','%n ta buyurtma muddatidan o‘tgan'],
 al_debt:['Customers owe %m UZS','Покупатели должны %m сум','Mijozlar qarzi %m so‘m'],
 al_pay:['We owe suppliers %m UZS','Мы должны поставщикам %m сум','Yetkazib beruvchilarga qarzimiz %m so‘m'],
 al_open:['Open','Открыть','Ochish'],
 th_dark:['Switch to dark mode','Включить тёмную тему','Qorong‘i rejimga o‘tish'],
 th_light:['Switch to light mode','Включить светлую тему','Yorug‘ rejimga o‘tish'],
 menu:['Menu','Меню','Menyu'],
 bz_hello:['Hello, %m','Здравствуйте, %m','Salom, %m'],
 bz_today:['Today: %n delivery notes shipped for %m UZS. Figures update as documents are posted.','Сегодня: %n расходных накладных на %m сум. Цифры обновляются при проведении документов.','Bugun: %n ta chiqim nakladnoyi, %m so‘m. Raqamlar hujjat o‘tkazilishi bilan yangilanadi.'],
 bz_live:['Live','Онлайн','Jonli'],
 bz_sales:['Sales, last 30 days','Продажи за 30 дней','Savdo, oxirgi 30 kun'],
 bz_recv:['Customers owe us','Дебиторка','Mijozlar qarzi'],
 bz_pay:['We owe suppliers','Кредиторка','Bizning qarzimiz'],
 bz_cash:['Cash and bank','Деньги: банк и касса','Bank va kassa'],
 bz_ord:['Open orders','Открытые заказы','Ochiq buyurtmalar'],
 bz_low:['Low or out of stock','На исходе или нет','Tugayotgan yoki tugagan'],
 bz_sub_ord:['%n past delivery date','%n просрочено','%n tasi muddatidan o‘tgan'],
 bz_sub_inv:['%n delivery notes','%n накладных','%n ta nakladnoy'],
 bz_chart:['Shipments, last 30 days','Отгрузки за 30 дней','Jo‘natilgan yuk, oxirgi 30 kun'],
 bz_shipped:['Shipped','Отгружено','Jo‘natilgan'],
 bz_paid:['Paid','Оплачено','To‘langan'],
 bz_debtors:['Largest customer debts','Крупнейшие долги покупателей','Eng katta mijoz qarzlari'],
 bz_stock:['Stock alerts','Остатки на исходе','Qoldiq ogohlantirishlari'],
 bz_feed:['Latest documents','Последние документы','So‘nggi hujjatlar'],
 bz_nodebt:['No customer debts.','Долгов покупателей нет.','Mijoz qarzlari yo‘q.'],
 bz_nostock:['All stock is above the minimum.','Все остатки выше минимума.','Barcha qoldiqlar minimumdan yuqori.'],
 bz_min:['min %n','мин %n','min %n'],
 f_pay_in:['Payment received','Поступление оплаты','To‘lov kirimi'],
 f_pay_out:['Payment made','Оплата','To‘lov chiqimi']
};
Object.keys(RX).forEach(function(k){T.en[k]=RX[k][0];T.ru[k]=RX[k][1];T.uz[k]=RX[k][2]});
var ALL1={set:1,dash:1,prod:1,wh:1,items:1,mats:1,specs:1,cus:1,ord:1,inv:1,sup:1,rec:1,bank:1,cash:1};
var DEMO=[
 {u:'admin',p:'admin123',r:'admin',n:'Usmonxon Abbosov'},
 {u:'direktor',p:'dir123',r:'director',n:'Rustam Karimov'},
 {u:'ishlab',p:'prod123',r:'prod',n:'Sherzod Aliyev'},
 {u:'omborchi',p:'sklad123',r:'wh',n:'Bahodir Tursunov'},
 {u:'sotuv',p:'sotuv123',r:'sales',n:'Dilnoza Yusupova'},
 {u:'buxgalter',p:'buh123',r:'acc',n:'Malika Rahimova'}
];
var ME=null;
function lvl(sec){return ME&&ME.levels?(ME.levels[sec]||0):0}
function secOf(h){
  if(/^production/.test(h))return 'prod';
  var m={warehouse:'wh',products:'items',materials:'mats',specifications:'specs',customers:'cus','customer-akt':'cus',suppliers:'sup','supplier-akt':'sup',dashboard:'dash',settings:'set'};
  if(m[h])return m[h];
  if(/^order/.test(h))return 'ord';if(/^invoice/.test(h))return 'inv';if(/^receipt/.test(h))return 'rec';
  if(/^bank/.test(h))return 'bank';if(/^cash/.test(h))return 'cash';
  return null;
}
var NAV=[
 {g:null,i:[['dash','dashboard','nav_dash']]},
 {g:'grp_prod',i:[['prod','production','nav_prod'],['specs','specifications','nav_specs'],['mats','materials','p_mats'],['items','products','nav_items']]},
 {g:'nav_wh',i:[['wh','warehouse','nav_wh']]},
 {g:'grp_sales',i:[['cus','customers','nav_cus'],['ord','orders','nav_ord'],['inv','invoices','nav_inv']]},
 {g:'grp_buy',i:[['sup','suppliers','nav_sup'],['rec','receipts','nav_rec']]},
 {g:'grp_fin',i:[['bank','bank','nav_bank'],['cash','cash','nav_cash']]},
 {g:'grp_set',i:[['set','settings','nav_set']]}
];
var SECHASH={};NAV.forEach(function(g){g.i.forEach(function(x){SECHASH[x[0]]=x[1]})});
function svgi(p,s){s=s||18;return '<svg width="'+s+'" height="'+s+'" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+p+'</svg>'}
var NI={
 dash:'<path d="M3 3h6v7H3zM11 3h6v4h-6zM11 9h6v8h-6zM3 12h6v5H3z"/>',
 prod:'<path d="M2.5 16.5V8l5 3V8l5 3V4.5h5v12z"/>',
 wh:'<path d="M2 6l8-3.5L18 6v9l-8 3.5L2 15zM2 6l8 3.5L18 6M10 9.5V18"/>',
 items:'<rect x="3" y="3" width="14" height="14" rx="2"/><path d="M3 8h14M8 8v9"/>',
 mats:'<path d="M10 2.5l8 4-8 4-8-4zM2 10l8 4 8-4M2 13.5l8 4 8-4"/>',
 specs:'<path d="M5 2.5h7l3 3v12H5zM8 9h5M8 12h5M8 6h2"/>',
 cus:'<circle cx="7.5" cy="7" r="3"/><path d="M2 16c.6-3 3-4.5 5.5-4.5S12.4 13 13 16M13 4.5a3 3 0 010 5M15 11.8c1.6.5 2.7 1.8 3 4.2"/>',
 ord:'<rect x="4" y="3.5" width="12" height="14" rx="2"/><path d="M7.5 3.5V2.5h5v1M7 9h6M7 12.5h4"/>',
 inv:'<path d="M2 5h10v8H2zM12 8h3.5L18 10.5V13h-6"/><circle cx="5.5" cy="15" r="1.5"/><circle cx="14" cy="15" r="1.5"/>',
 sup:'<path d="M3 8l1.2-4.5h11.6L17 8M3 8h14v9H3zM8 17v-5h4v5"/>',
 rec:'<path d="M10 2.5v9M6.5 8.5L10 12l3.5-3.5M3 13v3.5h14V13"/>',
 bank:'<path d="M2.5 8L10 3l7.5 5M4.5 8v7M8 8v7M12 8v7M15.5 8v7M2.5 17h15"/>',
 cash:'<rect x="2.5" y="5" width="15" height="10" rx="2"/><circle cx="10" cy="10" r="2.3"/>',
 search:'<circle cx="9" cy="9" r="5.5"/><path d="M13.2 13.2L17 17"/>',
 bell:'<path d="M5 8a5 5 0 0110 0c0 5 2 6 2 6H3s2-1 2-6zM8.3 16.5a2 2 0 003.4 0"/>',
 moon:'<path d="M16.5 11.5A7 7 0 018.5 3.5a7 7 0 108 8z"/>',
 palette:'<path d="M10 2.5a7.5 7.5 0 100 15c1.2 0 1.6-.8 1.2-1.7-.5-1 .1-2.1 1.3-2.1h1.4a3.1 3.1 0 003.1-3.1C17 6 14 2.5 10 2.5z"/><circle cx="6.5" cy="9" r="1"/><circle cx="9" cy="6" r="1"/><circle cx="12.5" cy="6.5" r="1"/>',
 sun:'<circle cx="10" cy="10" r="3.5"/><path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.3 4.3l1.4 1.4M14.3 14.3l1.4 1.4M4.3 15.7l1.4-1.4M14.3 5.7l1.4-1.4"/>',
 menu:'<path d="M3 5.5h14M3 10h14M3 14.5h14"/>',
 out:'<path d="M8 3.5H4.5v13H8M12 6.5L15.5 10 12 13.5M15.5 10H8"/>',
 ok:'<circle cx="10" cy="10" r="7.5"/><path d="M6.8 10.2l2.2 2.2 4.2-4.6"/>',
 flame:'<path d="M10 2.2c.6 2.8 4.2 4.4 4.2 8.6a4.2 4.2 0 0 1-8.4 0c0-1.6.6-2.7 1.6-3.7.2 1.1.7 1.7 1.4 2.1C8.6 6.6 9.3 4.4 10 2.2z"/>',
 warn:'<path d="M10 3L18 16.5H2z"/><path d="M10 8.5v3.5M10 14.3v.1"/>',
 plus:'<path d="M10 4v12M4 10h12"/>',
 set:'<circle cx="10" cy="10" r="2.6"/><path d="M10 2.5v2M10 15.5v2M2.5 10h2M15.5 10h2M4.7 4.7l1.4 1.4M13.9 13.9l1.4 1.4M4.7 15.3l1.4-1.4M13.9 6.1l1.4-1.4"/>',
 money:'<path d="M3 6h14v9H3zM3 9h14M7 12.5h2"/>',
 dn:'<path d="M10 3v10M6 9.5L10 13.5l4-4M4 16.5h12"/>'
};
/* session: the server decides who you are and what you may do */
function userFrom(m){return {u:m.username,r:m.role,n:m.full_name,levels:m.levels,home:m.home,tfa:!!m.totp_enabled,must2fa:!!m.must_setup_2fa,feat:m.features||[],owner:!!m.owner}}
function setMe(u){ME=u}
function sessionExpired(){if(!ME)return;Tabs.reset();apiSetToken(null);ME=null;buildSide();document.body.classList.remove('app','nav-open');toast(apiErr({code:'unauthorized'}),true,true);location.hash='login';route()}
function homeHash(){return ME?(SECHASH[ME.home]||'dashboard'):'overview'}
function initials(n){return n.split(' ').map(function(x){return x.charAt(0)}).slice(0,2).join('').toUpperCase()}
function buildSide(){
  var el=$('#side');
  if(!ME){el.innerHTML='';return}
  var h='';
  NAV.forEach(function(g){
    var it=g.i.filter(function(x){return lvl(x[0])>0});if(!it.length)return;
    if(g.g)h+='<div class="grp">'+t(g.g)+'</div>';
    it.forEach(function(x){h+='<a href="#'+x[1]+'" id="nav-'+x[0]+'">'+svgi(NI[x[0]])+'<span>'+t(x[2])+'</span></a>'});
  });
  h+='<div class="me"><div class="av" aria-hidden="true">'+esc(initials(ME.n))+'</div><div class="who"><b>'+esc(ME.n)+'</b><span>'+t('role_'+ME.r)+'</span></div><button type="button" class="ibtn" id="themebtn2" aria-label="Theme">'+svgi(NI.palette)+'</button><button type="button" class="ibtn" id="signout" aria-label="'+t('signout')+'" title="'+t('signout')+'">'+svgi(NI.out)+'</button></div>';
  el.innerHTML=h;
}
function signOut(){try{api('POST','/auth/logout').catch(function(){})}catch(e){}Tabs.wipe();Tabs.reset();apiSetToken(null);setMe(null);buildSide();document.body.classList.remove('app','nav-open');toast(t('signed_out'));location.hash='overview';route()}
function doLogin(u,p,keep){
  var key=String(u).trim().toLowerCase();
  var body={username:key,password:p},ov=$('#otpf')&&!$('#otpf').hidden?$('#otp').value:'';if(ov)body.otp=ov;
  api('POST','/auth/login',body).then(function(r){
    apiSetToken(r.access_token,keep);setMe(userFrom(r.user));
    return Store.load();
  }).then(function(){
    $('#pw').value='';$('#pw').type='password';updateTg();$('#otp').value='';$('#otpf').hidden=true;setErr('#eo','#otp',null);
    setErr('#eu','#u',null);setErr('#ep','#pw',null);
    buildSide();Tabs.load();toast(tf('signed_in',{m:ME.n}));
    var same=location.hash==='#'+homeHash();location.hash=homeHash();if(same)route();
  },function(e){
    apiSetToken(null);setMe(null);
    if(e.code==='bad_login'){setErr('#ep','#pw','login_bad');$('#pw').focus()}
    else if(e.code==='otp_required'||e.code==='bad_otp'){$('#otpf').hidden=false;setErr('#eo','#otp',e.code==='bad_otp'?'login_otp_bad':null);$('#otp').value='';$('#otp').focus()}
    else toast(apiErr(e),true);
  });
}
/* open the app straight away when a saved session exists */
function boot(){
  fetch(API.base+'/health').then(function(r){return r.json()}).then(function(h){Store.demo=!!h.demo_users;renderDemo()}).catch(function(){});
  if(!API.token){route();return}
  api('GET','/auth/me').then(function(m){setMe(userFrom(m));return Store.load()}).then(function(){buildSide();Tabs.load();route()},function(){apiSetToken(null);setMe(null);route()});
}
function renderDemo(){
  $('#demoh').hidden=!Store.demo;$('#demoacc').hidden=!Store.demo;
  if(!Store.demo){$('#demoacc').innerHTML='';return}
  $('#demoh').textContent=t('login_demo2');
  $('#demoacc').innerHTML=DEMO.map(function(x){return '<button type="button" data-u="'+x.u+'"><span>'+t('role_'+x.r)+'</span><small>'+x.u+' · '+x.p+'</small></button>'}).join('');
}
$('#demoacc').addEventListener('click',function(e){var b=e.target.closest('[data-u]');if(!b)return;var x=DEMO.filter(function(y){return y.u===b.dataset.u})[0];$('#u').value=x.u;$('#pw').value=x.p;doLogin(x.u,x.p,$('#rm').checked)});


function flameHtml(){return '<span class="flame" title="'+t('cu_flame')+'" role="img" aria-label="'+t('cu_flame')+'">'+svgi(NI.flame,16)+'</span>'}
