/* Monthly management meeting: the month against the month before as a slide deck (on screen, full screen, or a PowerPoint file). Loaded after extra.js. */
(function(){
'use strict';
var X={
 nav_mtg:['Monthly meeting','Совещание за месяц','Oylik majlis'],
 mt_h:['Monthly meeting','Ежемесячное совещание','Oylik majlis'],
 mt_note:['The month against the month before, built from the posted documents. Open the slides on a screen at the meeting or download them as a PowerPoint file.','Месяц в сравнении с предыдущим по проведённым документам. Откройте слайды на экране совещания или скачайте PowerPoint.','Oy o‘tgan oy bilan taqqoslanadi, o‘tkazilgan hujjatlardan olinadi. Majlisda ekranda oching yoki PowerPoint qilib yuklab oling.'],
 mt_month:['Month','Месяц','Oy'],mt_present:['Full screen','На весь экран','To‘liq ekran'],mt_pptx:['Download PowerPoint','Скачать PowerPoint','PowerPoint yuklab olish'],
 mt_prev:['Previous slide','Предыдущий слайд','Oldingi slayd'],mt_next:['Next slide','Следующий слайд','Keyingi slayd'],mt_exit:['Close','Закрыть','Yopish'],
 mt_ai:['Talking to the team','Разговор с командой','Jamoa bilan suhbat'],mt_ai_wait:['AI is reading the figures…','AI изучает цифры…','AI raqamlarni o‘qiyapti…'],mt_q:['Questions for the meeting','Вопросы для обсуждения','Majlis uchun savollar'],mt_pts:['Talking points','Тезисы','Asosiy gaplar'],
 mt_prem:['Premium feature','Премиум-функция','Premium imkoniyat'],
 mt_prem_h:['Monthly meeting is a premium feature','Ежемесячное совещание — премиум-функция','Oylik majlis — premium imkoniyat'],
 mt_prem_p:['It builds the whole meeting for you: slides with the month’s figures, the comparison with last month, AI remarks and a PowerPoint file.','Оно готовит совещание целиком: слайды с цифрами месяца, сравнение с прошлым месяцем, комментарии AI и файл PowerPoint.','U majlisni to‘liq tayyorlab beradi: oy raqamlari bilan slaydlar, o‘tgan oy bilan taqqoslash, AI sharhlari va PowerPoint fayl.'],
 mt_pm:['Previous month','Предыдущий месяц','Oldingi oy'],mt_nm:['Next month','Следующий месяц','Keyingi oy'],mt_held:['held','проведено','o‘tkazilgan'],
 mt_pick:['Choose a month','Выберите месяц','Oyni tanlang'],mt_py:['Previous year','Предыдущий год','Oldingi yil'],mt_ny:['Next year','Следующий год','Keyingi yil'],
 mt_prem_what:['What you get','Что вы получите','Nimalar ochiladi'],
 mt_f1h:['A ready deck for every month','Готовая презентация на каждый месяц','Har oy uchun tayyor taqdimot'],
 mt_f1:['Pick a month and the system builds the whole meeting from your own records, with nothing to type in: a cover, overview, production, scrap, sales, debts, stock, staff and a summary slide.','Выберите месяц, и система соберёт всё совещание из ваших данных, вводить ничего не нужно: титул, обзор, производство, брак, продажи, долги, склад, сотрудники и итоговый слайд.','Oyni tanlang, tizim butun majlisni o‘z yozuvlaringizdan yig‘adi, hech narsa kiritish shart emas: muqova, umumiy ko‘rinish, ishlab chiqarish, brak, savdo, qarzlar, ombor, xodimlar va yakuniy slayd.'],
 mt_f2h:['Comparison with last month','Сравнение с прошлым месяцем','O‘tgan oy bilan taqqoslash'],
 mt_f2:['Every figure shows the change against last month, in percent and in pieces. For the month that is still running, it is compared with the same days of last month, so the comparison is fair.','Каждая цифра показывает изменение к прошлому месяцу в процентах и в штуках. Для идущего месяца сравнение идёт с теми же днями прошлого месяца, поэтому оно честное.','Har bir raqam o‘tgan oyga nisbatan o‘zgarishni foiz va dona bilan ko‘rsatadi. Davom etayotgan oy o‘tgan oyning aynan shu kunlari bilan solishtiriladi, shuning uchun taqqoslash adolatli bo‘ladi.'],
 mt_f3h:['Products, plants, debts and stock','Продукция, заводы, долги и склад','Mahsulotlar, zavodlar, qarzlar va ombor'],
 mt_f3:['Output by product and by plant with last month beside it, a daily output line, the products with the most scrap, top customers by shipments, customer and supplier debts with overdue amounts, low stock with a forecast of how many days it will last, and workers’ earnings.','Выпуск по изделиям и заводам с прошлым месяцем рядом, линия выпуска по дням, изделия с наибольшим браком, главные клиенты по отгрузкам, долги клиентов и поставщиков с просрочкой, низкие остатки с прогнозом на сколько дней хватит и заработок работников.','Mahsulot va zavodlar bo‘yicha ishlab chiqarish (yonida o‘tgan oy), kunlik ishlab chiqarish chizig‘i, eng ko‘p brak chiqqan mahsulotlar, jo‘natmalar bo‘yicha asosiy mijozlar, mijoz va yetkazib beruvchi qarzlari (muddati o‘tganlari bilan), kam qolgan materiallar va necha kunga yetishi prognozi, ishchilar topgan summa.'],
 mt_f4h:['AI remarks and questions','Замечания и вопросы от AI','AI sharhlari va savollar'],
 mt_f4:['The AI reads the month’s figures and writes short remarks for each slide, then prepares questions for the team to discuss. It only sees the finished numbers, never your database, and it never changes anything.','AI читает цифры месяца, пишет короткие замечания к каждому слайду и готовит вопросы для обсуждения командой. Он видит только готовые цифры, но не базу данных, и ничего не меняет.','AI oy raqamlarini o‘qib, har bir slayd uchun qisqa sharh yozadi va jamoa muhokamasi uchun savollar tayyorlaydi. U faqat tayyor raqamlarni ko‘radi, bazaga kirmaydi va hech narsani o‘zgartirmaydi.'],
 mt_f5h:['Present on screen','Показ на экране','Ekranda namoyish'],
 mt_f5:['Full-screen mode with animated numbers and charts. Move between slides with the arrow keys or the buttons, and run the meeting straight from the page.','Полноэкранный режим с анимацией чисел и графиков. Листайте слайды стрелками клавиатуры или кнопками и проводите совещание прямо со страницы.','Raqamlar va grafiklar animatsiyali to‘liq ekran rejimi. Slaydlarni klaviatura strelkalari yoki tugmalar bilan almashtiring va majlisni to‘g‘ridan-to‘g‘ri sahifadan o‘tkazing.'],
 mt_f6h:['PowerPoint file','Файл PowerPoint','PowerPoint fayl'],
 mt_f6:['Download the same deck, with the AI remarks if you want them, as a PowerPoint file to send, print or present from any computer.','Скачайте ту же презентацию, при желании с замечаниями AI, в виде файла PowerPoint, чтобы отправить, распечатать или показать на любом компьютере.','Xuddi shu taqdimotni, xohlasangiz AI sharhlari bilan, PowerPoint fayl sifatida yuklab oling: yuborish, chop etish yoki istalgan kompyuterdan ko‘rsatish mumkin.'],
 mt_f7h:['Each person sees their own part','Каждый видит свою часть','Har kim o‘z qismini ko‘radi'],
 mt_f7:['Slides follow the role. A warehouse keeper does not see salaries, and an accountant does not see production, so one deck is safe to open for everyone.','Слайды зависят от роли. Кладовщик не видит зарплат, а бухгалтер не видит производство, поэтому одну презентацию безопасно открывать для всех.','Slaydlar rolga qarab ko‘rinadi. Omborchi maoshlarni ko‘rmaydi, buxgalter ishlab chiqarishni ko‘rmaydi, shuning uchun bitta taqdimotni hamma uchun ochish xavfsiz.'],
 mt_term:['Once switched on it works for one month and allows two meetings in that time (two different months). Opening a month you already held again is free.','После включения функция работает один месяц и позволяет провести два совещания за это время (два разных месяца). Повторное открытие уже проведённого месяца бесплатно.','Yoqilgandan keyin u bir oy davomida ishlaydi va shu muddatda ikkita majlis o‘tkazish mumkin (ikki xil oy). Allaqachon o‘tkazilgan oyni qayta ochish bepul.'],
 mt_exp:['Your premium access has ended. To use it again, contact the administrator.','Срок премиум-доступа закончился. Чтобы пользоваться снова, обратитесь к администратору.','Premium muddati tugadi. Qayta foydalanish uchun administratorga murojaat qiling.'],
 mt_st:['Premium until {d} · meetings left: {n} of {l}','Премиум до {d} · осталось совещаний: {n} из {l}','Premium {d} gacha · qolgan majlislar: {n} / {l}'],
 mt_ask_h:['Hold the meeting for {m}?','Провести совещание за {m}?','{m} uchun majlis o‘tkazamizmi?'],
 mt_ask_p:['This uses one of your {n} remaining meetings.','Это спишет одно из ваших оставшихся совещаний: {n}.','Bu qolgan {n} ta majlisdan bittasini sarflaydi.'],
 mt_ask_go:['Open the meeting','Открыть совещание','Majlisni ochish'],
 mt_lim_h:['No meetings left','Совещания закончились','Majlislar tugadi'],
 mt_lim_p:['You have used both meetings of this month. Months you already held can still be opened. For more, contact the administrator.','Оба совещания этого периода использованы. Уже проведённые месяцы можно открывать снова. Для новых обратитесь к администратору.','Shu muddatdagi ikkala majlis ham ishlatildi. Allaqachon o‘tkazilgan oylarni qayta ochish mumkin. Yangilari uchun administratorga murojaat qiling.'],
 mt_prem_ask:['To switch it on, contact the administrator.','Чтобы включить, обратитесь к администратору.','Yoqish uchun administratorga murojaat qiling.'],
 mt_err:['Could not build the slides.','Не удалось собрать слайды.','Slaydlarni yig‘ib bo‘lmadi.'],mt_none:['Nothing to show for your role.','Для вашей роли нет данных.','Sizning rolingiz uchun ko‘rsatiladigan ma’lumot yo‘q.']
};
Object.keys(X).forEach(function(k){T.en[k]=X[k][0];T.ru[k]=X[k][1];T.uz[k]=X[k][2]});
NI.mtg='<rect x="3" y="3.5" width="14" height="10" rx="1"/><path d="M7 17l3-3.5 3 3.5M10 13.5V17"/><path d="M6.5 10l2-2 2 1.5 3-3"/>';
NAV.forEach(function(g){if(g.g==='grp_ai')g.i.splice(2,0,['mtg','meeting','nav_mtg'])});
SECHASH.mtg='meeting';
var _uf2=userFrom;
userFrom=function(m){var u=_uf2(m),l=u.levels||{};u.levels=l;l.mtg=(l.prod||l.inv||l.cus||l.sup||l.wh||l.pay)?2:0;return u};

var MS={month:'',deck:null,i:0,busy:false};
function Q(o){var a=[];Object.keys(o).forEach(function(k){if(o[k]!==''&&o[k]!=null)a.push(encodeURIComponent(k)+'='+encodeURIComponent(o[k]))});return a.length?'?'+a.join('&'):''}
function num(v,type){
  /* whole numbers with a space between thousands (1 234 567); under 10 one decimal, never a trailing ",0" */
  if(v==null||v==='')return '';
  var n=+v,neg=n<0,a=Math.abs(n);
  a=(type==='money'||a>=10)?Math.round(a):Math.round(a*10)/10;
  var p=String(a).split('.');
  return (neg&&a>0?'-':'')+p[0].replace(/\B(?=(\d{3})+(?!\d))/g,' ')+(p[1]?','+p[1]:'');
}
function prevMonth(){var d=new Date();d.setDate(1);d.setMonth(d.getMonth()-1);return d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)}
function fmt(v,type){
  if(v==null||v==='')return '';
  if(type==='pct')return (v>0?'+':'')+num(v,'num')+'%';
  return num(v,type)||String(v);
}
function kpiHtml(k,d,i){
  var dl='',bars='',tg=k.target?'<div class="mt-tg '+(k.target.ok?'ok':'bad')+'">'+(k.target.ok?'✓ ':'▼ ')+esc(k.target.text)+'</div>':'';
  if(k.delta!=null){var up=k.delta>=0,good=k.bad_up?!up:up;dl='<div class="mt-d '+(good?'ok':'bad')+'">'+(up?'▲':'▼')+' '+num(Math.abs(k.delta),'num')+'% <span>'+esc(d.vs)+'</span></div>'}
  if(k.prev!=null&&(k.value||k.prev)){
    var mx=Math.max(k.value,k.prev)||1;
    bars='<div class="mt-vs"><div><span>'+esc(d.labels.cur)+'</span><i class="a" data-w="'+(k.value*100/mx).toFixed(1)+'"></i></div><div><span>'+esc(d.labels.prev)+'</span><i class="b" data-w="'+(k.prev*100/mx).toFixed(1)+'"></i></div></div>';
  }
  return '<div class="mt-k" style="--i:'+i+'"><div class="mt-kl">'+esc(k.label)+'</div><div class="mt-kv"><b class="cu" data-to="'+k.value+'">'+num(k.value,'num')+'</b>'+(k.unit?' <small>'+esc(k.unit)+'</small>':'')+'</div>'+dl+bars+tg+'</div>';
}
function tabHtml(tb){
  if(!tb.rows.length)return '';
  var th=tb.columns.map(function(c){return '<th'+(c.type!=='text'?' class="num"':'')+'>'+esc(c.label)+'</th>'}).join('');
  var tr=tb.rows.map(function(r,ri){return '<tr style="--i:'+ri+'">'+tb.columns.map(function(c){
    var v=r[c.key],cls=c.type!=='text'?' class="num'+(c.type==='pct'&&v!=null?(v>=0?' ok':' bad'):'')+'"':'';
    return '<td'+cls+'>'+(c.type==='text'?esc(v==null?'':v):esc(fmt(v,c.type)))+'</td>'}).join('')+'</tr>'}).join('');
  return '<div class="mt-t">'+(tb.title?'<div class="mt-tt">'+esc(tb.title)+'</div>':'')+'<table class="dt"><thead><tr>'+th+'</tr></thead><tbody>'+tr+'</tbody></table></div>';
}
function lineHtml(s){
  var p=s.points;if(!p||!p.length)return '';
  var w=520,h=210,l=44,r=10,tp=14,b=26,mx=Math.max.apply(null,p.map(function(a){return a.y}))||1;
  var X1=function(i){return l+(p.length>1?i*(w-l-r)/(p.length-1):(w-l-r)/2)},Y=function(v){return tp+(h-tp-b)*(1-v/mx)};
  var pts=p.map(function(a,i){return X1(i).toFixed(1)+','+Y(a.y).toFixed(1)}).join(' ');
  var g='';for(var k=0;k<=3;k++){var v=mx*k/3;g+='<line x1="'+l+'" x2="'+(w-r)+'" y1="'+Y(v).toFixed(1)+'" y2="'+Y(v).toFixed(1)+'" class="mt-g"/><text x="'+(l-6)+'" y="'+(Y(v)+4).toFixed(1)+'" text-anchor="end" class="mt-ax">'+Math.round(v)+'</text>'}
  var step=Math.ceil(p.length/10),xl=p.map(function(a,i){return i%step===0?'<text x="'+X1(i).toFixed(1)+'" y="'+(h-8)+'" text-anchor="middle" class="mt-ax">'+esc(a.x)+'</text>':''}).join('');
  var dots=p.map(function(a,i){return '<circle style="--i:'+i+'" cx="'+X1(i).toFixed(1)+'" cy="'+Y(a.y).toFixed(1)+'" r="3.5" class="mt-dot"><title>'+esc(a.x)+': '+a.y+'</title></circle>'}).join('');
  return '<div class="mt-c"><div class="mt-cl">'+esc(s.label)+'</div><svg viewBox="0 0 '+w+' '+h+'" role="img" aria-label="'+esc(s.label)+'">'+g+xl+'<polyline points="'+pts+'" class="mt-line" pathLength="1"/>'+dots+'</svg></div>';
}
function aiHtml(txt){return '<div class="mt-ai"><em>'+esc(t('mt_ai'))+'</em><p>'+esc(txt)+'</p></div>'}
function slideHtml(sl,d){
  if(sl.cover)return '<div class="mt-cover"><div class="mt-rule"></div><h2>'+esc(d.title)+'</h2><p>'+esc(d.label)+'</p>'+(d.note?'<p class="mt-note">'+esc(d.note)+'</p>':'')+'<small>Prime Beton</small></div>';
  var h='<h3>'+esc(sl.title)+'</h3>';
  if(sl.kpis&&sl.kpis.length)h+='<div class="mt-ks">'+sl.kpis.map(function(k,i){return kpiHtml(k,d,i)}).join('')+'</div>';
  if(sl.spots&&sl.spots.length)h+='<div class="mt-sps">'+sl.spots.map(function(p,i){return '<div class="mt-sp" style="--i:'+(i+(sl.kpis||[]).length)+'"><div class="mt-spl">'+esc(p.label)+'</div><div class="mt-spn">'+esc(p.name)+'</div>'+(p.value!=null?'<div class="mt-spv">'+num(p.value,'num')+(p.unit?' <small>'+esc(p.unit)+'</small>':'')+'</div>':'')+(p.note?'<div class="mt-spt">'+esc(p.note)+'</div>':'')+'</div>'}).join('')+'</div>';
  var tabs='';
  (sl.tables||[]).forEach(function(tb){tabs+=tabHtml(tb)});
  var ch=sl.series?lineHtml(sl.series):'';
  if(tabs||ch)h+='<div class="mt-b'+(ch?' two':'')+'">'+(tabs?'<div class="mt-col'+(!ch&&(sl.tables||[]).filter(function(x){return x.rows.length}).length>1?' cols':'')+'">'+tabs+'</div>':'')+ch+'</div>';
  var pts=(sl.id==='summary'&&MS.ai&&MS.ai.points)?MS.ai.points:[];
  var bl=(sl.bullets||[]).concat(pts);
  if(bl.length)h+='<ul class="mt-bl">'+bl.map(function(b,i){return '<li style="--i:'+i+'"'+(i>=(sl.bullets||[]).length?' class="ai"':'')+'>'+esc(b)+'</li>'}).join('')+'</ul>';
  if(sl.qs)h+='<ol class="mt-ql">'+sl.qs.map(function(q,i){return '<li style="--i:'+i+'">'+esc(q)+'</li>'}).join('')+'</ol>';
  if(sl.empty&&!sl.kpis&&!sl.spots&&!bl.length)h+='<p class="empty">'+esc(d.empty_text)+'</p>';
  if(sl.id&&sl.id!=='questions'){
    if(MS.ai&&MS.ai.ai&&MS.ai.slides&&MS.ai.slides[sl.id])h+=aiHtml(MS.ai.slides[sl.id]);
    else if(MS.aiWait)h+='<div class="mt-ai wait"><em>'+esc(t('mt_ai'))+'</em><p>'+esc(t('mt_ai_wait'))+'</p></div>';
  }
  return h;
}
function slides(){
  var d=MS.deck;if(!d)return [];
  var a=[{cover:1}].concat(d.slides);
  if(MS.ai&&MS.ai.ai&&MS.ai.questions&&MS.ai.questions.length)a.push({id:'questions',title:d.labels.questions||t('mt_q'),qs:MS.ai.questions});
  return a;
}
var REDUCE=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
function animate(el){
  var bars=el.querySelectorAll('.mt-vs i');
  if(REDUCE){bars.forEach(function(b){b.style.width=b.dataset.w+'%'});return}
  requestAnimationFrame(function(){requestAnimationFrame(function(){bars.forEach(function(b,i){b.style.transitionDelay=(260+i*60)+'ms';b.style.width=b.dataset.w+'%'})})});
  el.querySelectorAll('.cu').forEach(function(n,i){
    var to=+n.dataset.to,t0=null,dur=900,dec=Math.abs(to-Math.round(to))>0.004;
    n.textContent=num(0,'num');
    function f(ts){if(t0===null)t0=ts+i*70;var p=Math.min(Math.max((ts-t0)/dur,0),1),e=1-Math.pow(1-p,3),v=to*e;n.textContent=num(dec?Math.round(v*100)/100:Math.round(v),'num');if(p<1)requestAnimationFrame(f);else n.textContent=num(to,'num')}
    requestAnimationFrame(f);
  });
}
function stage(dir,keep){
  var a=slides(),sl=a[MS.i];if(!sl)return;
  var el=$('#mt-stage');if(!el)return;
  el.innerHTML=slideHtml(sl,MS.deck);
  if(!keep){el.classList.remove('r','l');void el.offsetWidth;el.classList.add(dir<0?'l':'r');animate(el)}
  else el.querySelectorAll('.mt-vs i').forEach(function(b){b.style.width=b.dataset.w+'%'});
  $('#mt-pos').textContent=(MS.i+1)+' / '+a.length;
  $('#mt-prev').disabled=MS.i===0;$('#mt-next').disabled=MS.i===a.length-1;
  var dots=$('#mt-dots');dots.innerHTML=a.map(function(s,i){return '<button type="button" class="mt-dot-b" data-i="'+i+'" aria-label="'+esc(s.cover?MS.deck.title:s.title)+'"'+(i===MS.i?' aria-current="true"':'')+'></button>'}).join('');
}
/* the user's own meetings are limited: a month not held yet costs one, so ask before spending it (the main administrator has no limit) */
function fill(k,o){return t(k).replace(/\{(\w+)\}/g,function(_,x){return o[x]})}
function gate(m){
  if(!ME||ME.owner||MS.okm===m)return 'free';
  var g=ME.prem;if(!g)return 'free';
  if(g.used.indexOf(m)>=0)return 'free';
  return g.uses_left>0?'ask':'limit';
}
function panel(h,p,btn){
  MS.deck=null;MS.ai=null;MS.busy=false;
  var el=$('#mt-stage');if(!el)return;
  el.classList.remove('r','l');
  el.innerHTML='<div class="mt-gate"><h2>'+h+'</h2><p>'+p+'</p>'+(btn?'<button type="button" class="btn primary" id="mt-go">'+btn+'</button>':'')+'</div>';
  $('#mt-pos').textContent='';$('#mt-dots').innerHTML='';$('#mt-prev').disabled=true;$('#mt-next').disabled=true;
  var b=$('#mt-go');if(b)b.addEventListener('click',function(){MS.okm=MS.month;load()});
}
function status(){
  var g=ME&&!ME.owner&&ME.prem;if(!g)return '';
  var d=new Date(g.expires_at.replace(' ','T')+'Z');
  return '<p class="mt-status">'+fill('mt_st',{d:d.toLocaleDateString(LOC[lang]),n:g.uses_left,l:g.uses_limit})+'</p>';
}
function load(){
  if(MS.busy)return;
  var gt=gate(MS.month);
  if(gt==='limit')return panel(t('mt_lim_h'),t('mt_lim_p'));
  if(gt==='ask')return panel(fill('mt_ask_h',{m:MS.month}),fill('mt_ask_p',{n:ME.prem.uses_left}),t('mt_ask_go'));
  MS.busy=true;MS.ai=null;MS.aiWait=false;var m=MS.month;
  api('GET','/reports/meeting'+Q({month:m,lang:lang})).then(function(d){MS.busy=false;MS.deck=d;if(ME&&ME.prem&&ME.prem.used.indexOf(m)<0){ME.prem.used.push(m);ME.prem.uses_left=Math.max(0,ME.prem.uses_left-1);var st=$('.mt-status');if(st)st.outerHTML=status()}MS.i=Math.min(MS.i,d.slides.length);
    stage(1);
    MS.aiWait=true;stage(1,true);
    api('GET','/reports/meeting/ai'+Q({month:m,lang:lang})).then(function(a){
      if(MS.month!==m)return;MS.aiWait=false;MS.ai=a;stage(1,true);
    },function(){MS.aiWait=false;stage(1,true)});
  },function(e){MS.busy=false;if(e&&e.code==='premium_required'){ME.feat=[];wall();return}if(e&&e.code==='premium_limit'){panel(t('mt_lim_h'),t('mt_lim_p'));return}toast(t('mt_err')+' '+apiErr(e),true)});
}
/* month picker: arrows for the neighbour months and a pop-up with the twelve months of a year (the browser's own month field looks different in every browser and language) */
var MNAME={uz:['Yanvar','Fevral','Mart','Aprel','May','Iyun','Iyul','Avgust','Sentyabr','Oktyabr','Noyabr','Dekabr'],
 ru:['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'],
 en:['January','February','March','April','May','June','July','August','September','October','November','December']};
function ym(y,m){return y+'-'+('0'+(m+1)).slice(-2)}
function curYM(){var d=new Date();return ym(d.getFullYear(),d.getMonth())}
function shiftYM(v,n){var p=v.split('-'),d=new Date(+p[0],+p[1]-1+n,1);return ym(d.getFullYear(),d.getMonth())}
function mlabel(v){var p=v.split('-');return (MNAME[lang]||MNAME.en)[+p[1]-1]+' '+p[0]}
var CHEV='<svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 8l5 5 5-5"/></svg>';
function pickerHtml(){
  return '<div class="mt-mp"><span class="mt-mpl" id="mt-mpl">'+t('mt_month')+'</span><div class="mt-mpr" role="group" aria-labelledby="mt-mpl">'+
   '<button type="button" class="mt-mpb" id="mt-mprev" aria-label="'+t('mt_pm')+'">‹</button>'+
   '<button type="button" class="mt-mpv" id="mt-mlabel" aria-haspopup="dialog" aria-expanded="false" aria-controls="mt-mpop"><span id="mt-mtext"></span>'+CHEV+'</button>'+
   '<button type="button" class="mt-mpb" id="mt-mnext" aria-label="'+t('mt_nm')+'">›</button></div>'+
   '<div class="mt-mpop" id="mt-mpop" role="dialog" aria-label="'+t('mt_pick')+'" hidden></div></div>';
}
function popHtml(){
  var used=(ME&&ME.prem&&!ME.owner)?ME.prem.used:[],cur=curYM(),ny=+cur.slice(0,4);
  var h='<div class="mt-mph"><button type="button" class="mt-mpb" data-y="-1" aria-label="'+t('mt_py')+'">‹</button><b>'+MS.py+'</b><button type="button" class="mt-mpb" data-y="1" aria-label="'+t('mt_ny')+'"'+(MS.py>=ny?' disabled':'')+'>›</button></div><div class="mt-mpg">';
  (MNAME[lang]||MNAME.en).forEach(function(n,i){
    var v=ym(MS.py,i),fut=v>cur;
    h+='<button type="button" class="mt-mpm'+(v===MS.month?' on':'')+(v===cur?' now':'')+'" data-ym="'+v+'"'+(fut?' disabled':'')+(v===MS.month?' aria-current="true"':'')+'>'+n.slice(0,3)+(used.indexOf(v)>=0?'<i title="'+t('mt_held')+'"></i>':'')+'</button>';
  });
  return h+'</div>';
}
function pickerSync(){
  var a=$('#mt-mtext');if(a)a.textContent=mlabel(MS.month);
  var nx=$('#mt-mnext');if(nx)nx.disabled=MS.month>=curYM();
}
function popOpen(on){
  var pop=$('#mt-mpop'),b=$('#mt-mlabel');if(!pop)return;
  if(on){MS.py=+MS.month.slice(0,4);pop.innerHTML=popHtml();pop.hidden=false;var s=pop.querySelector('.on')||pop.querySelector('.mt-mpm');if(s)s.focus()}
  else pop.hidden=true;
  b.setAttribute('aria-expanded',on?'true':'false');
}
function setMonth(v){
  if(!v||v===MS.month&&MS.deck)return;
  MS.month=v;MS.i=0;MS.busy=false;pickerSync();popOpen(false);load();
}
function has(){return !!(ME&&ME.feat&&ME.feat.indexOf('meeting')>=0)}
function wall(){
  var el=$('#xv-meeting');
  el.innerHTML='<div class="wrap dash"><div class="dhead"><div><h1>'+t('mt_h')+'</h1></div></div>'+
   '<div class="mt-prem"><span class="mt-lock" aria-hidden="true"><svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg></span>'+
   '<em>'+t('mt_prem')+'</em><h2>'+t('mt_prem_h')+'</h2><p>'+t('mt_prem_p')+'</p>'+
   '<h3>'+t('mt_prem_what')+'</h3><div class="mt-feats">'+[1,2,3,4,5,6,7].map(function(i){return '<div class="mt-feat"><b>'+t('mt_f'+i+'h')+'</b><span>'+t('mt_f'+i)+'</span></div>'}).join('')+'</div>'+
   '<p class="mt-term">'+t('mt_term')+'</p>'+
   '<p class="mt-ask"><b>'+t(ME&&ME.prem&&!ME.prem.active?'mt_exp':'mt_prem_ask')+'</b></p></div></div>';
}
function render(){
  /* the switch is the main administrator's: ask the server again, a grant made a minute ago must work without signing in anew */
  api('GET','/auth/me').then(function(m){if(ME){ME.feat=m.features||[];ME.prem=(m.premium||[]).filter(function(g){return g.feature==='meeting'})[0]||null}},function(){}).then(function(){has()?renderDeck():wall()});
}
function renderDeck(){
  var el=$('#xv-meeting');if(!MS.month)MS.month=prevMonth();
  el.innerHTML='<div class="wrap dash"><div class="dhead"><div><h1>'+t('mt_h')+'</h1><p class="note">'+t('mt_note')+'</p>'+status()+'</div></div>'+
   '<div class="mt-bar">'+pickerHtml()+
   '<button type="button" class="btn ghost" id="mt-full">'+t('mt_present')+'</button><button type="button" class="btn primary" id="mt-pptx">'+t('mt_pptx')+'</button></div>'+
   '<div id="mt-wrap"><div class="mt-frame" id="mt-frame"><div class="mt-stage" id="mt-stage" aria-live="polite"></div>'+
   '<div class="mt-nav"><button type="button" class="btn ghost" id="mt-prev" aria-label="'+t('mt_prev')+'">‹</button><div id="mt-dots" class="mt-dots"></div><span id="mt-pos" class="mt-pos"></span><button type="button" class="btn ghost" id="mt-next" aria-label="'+t('mt_next')+'">›</button></div></div></div></div>';
  pickerSync();
  $('#mt-mprev').addEventListener('click',function(){setMonth(shiftYM(MS.month,-1))});
  $('#mt-mnext').addEventListener('click',function(){if(MS.month<curYM())setMonth(shiftYM(MS.month,1))});
  $('#mt-mlabel').addEventListener('click',function(){popOpen($('#mt-mpop').hidden)});
  $('#mt-mpop').addEventListener('click',function(e){
    var y=e.target.closest('[data-y]');if(y){MS.py+=+y.dataset.y;$('#mt-mpop').innerHTML=popHtml();var f=$('#mt-mpop').querySelector('[data-y="'+y.dataset.y+'"]');if(f&&!f.disabled)f.focus();return}
    var m=e.target.closest('[data-ym]');if(m)setMonth(m.dataset.ym);
  });
  $('#mt-mpop').addEventListener('keydown',function(e){if(e.key==='Escape'){e.stopPropagation();popOpen(false);$('#mt-mlabel').focus()}});
  if(!MS.mpbound){MS.mpbound=1;document.addEventListener('click',function(e){var p=$('#mt-mpop');if(p&&!p.hidden&&!e.target.closest('.mt-mp'))popOpen(false)})}
  $('#mt-pptx').addEventListener('click',function(){if(!MS.deck)return;openBlob('/reports/meeting/export.pptx'+Q({month:MS.month,lang:lang,ai:(MS.ai&&MS.ai.ai)?1:''}),'meeting-'+MS.month+'.pptx',true)});
  $('#mt-full').addEventListener('click',function(){var f=$('#mt-frame');if(document.fullscreenElement){document.exitFullscreen()}else if(f.requestFullscreen){f.requestFullscreen()}});
  $('#mt-prev').addEventListener('click',function(){go(-1)});$('#mt-next').addEventListener('click',function(){go(1)});
  $('#mt-dots').addEventListener('click',function(e){var b=e.target.closest('[data-i]');if(b){var n=+b.dataset.i;stage_dir(n)}});
  load();
}
function go(n){var a=slides(),i=MS.i+n;if(i>=0&&i<a.length){MS.i=i;stage(n)}}
function stage_dir(n){var d=n-MS.i;MS.i=n;stage(d)}
document.addEventListener('keydown',function(e){
  if(!$('#xv-meeting')||$('#xv-meeting').hidden||/INPUT|SELECT|TEXTAREA/.test((e.target||{}).tagName||'')||($('#mt-mpop')&&!$('#mt-mpop').hidden))return;
  if(e.key==='ArrowRight'||e.key==='PageDown'||e.key===' '){e.preventDefault();go(1)}else if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();go(-1)}
});
window.addView('meeting','mtg',render);
})();
