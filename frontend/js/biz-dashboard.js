/* live dashboard */
function m0(n){return money(Math.round(n)).replace(/,00$/,'')}
function numTo(el,to){
  var from=el._v==null?0:el._v;el._v=to;
  if(from===to||(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)){el.firstChild.nodeValue=m0(to);return}
  var t0=performance.now(),dur=650;
  (function f(now){var k=Math.min(1,(now-t0)/dur),e=1-Math.pow(1-k,3);el.firstChild.nodeValue=m0(from+(to-from)*e);if(k<1)requestAnimationFrame(f)})(t0);
}
function dayKey(d){return d.getFullYear()*10000+(d.getMonth()+1)*100+d.getDate()}
function bizData(){
  var end=today0(),days=[],i;
  for(i=29;i>=0;i--){var d=new Date(end);d.setDate(end.getDate()-i);days.push({d:d,k:dayKey(d),s:0,p:0,n:0})}
  var map={};days.forEach(function(x){map[x.k]=x});
  var lim=new Date(end);lim.setDate(end.getDate()-29);var s30=0,n30=0,tod=0,tn=0;
  INV.forEach(function(v){if(v.status!=='posted')return;var a=rsum(v.rows),k=dayKey(v.date);if(v.date>=lim){s30+=a;n30++}if(map[k]){map[k].s+=a;map[k].n++}if(k===dayKey(end)){tod+=a;tn++}});
  FIN.forEach(function(f){if(f.status!=='posted'||f.kind!=='in'||f.art!=='cust')return;var x=map[dayKey(f.date)];if(x)x.p+=f.amt});
  return {days:days,s30:s30,n30:n30,tod:tod,tn:tn};
}
var BZ=null,BZOPEN=false;   // the day-by-day table stays closed on every page load until the user opens it
document.addEventListener('toggle',function(ev){if(ev.target&&ev.target.id==='bzdet')BZOPEN=ev.target.open},true);
function bzTable(days){
  var ts=0,tn=0;days.forEach(function(x){ts+=x.s;tn+=x.n});
  var z=function(v){return v?m0(v):'<span class="dt-z">—</span>'};
  var rows=days.slice().reverse().map(function(x){return '<tr><td class="dt-d"><b class="mono">'+dfmt(x.d)+'</b><small'+(x.d.getDay()%6===0?' class="we"':'')+'>'+wkd(x.d)+'</small></td><td class="num">'+(x.n||'<span class="dt-z">—</span>')+'</td><td class="num">'+z(x.s)+'</td></tr>'}).join('');
  return '<table class="dt"><thead><tr><th>'+t('c_date')+'</th><th class="num">'+t('bz_ndoc')+'</th><th class="num">'+t('bz_shipped')+'</th></tr></thead><tbody>'+rows+'</tbody><tfoot><tr><td class="dt-d"><b>'+t('dt_total')+'</b><small>'+days.length+' '+(lang==='ru'?'дн.':lang==='uz'?'kun':'days')+'</small></td><td class="num">'+tn+'</td><td class="num">'+m0(ts)+'</td></tr></tfoot></table>';
}
function chartBiz(days){
  var W=640,H=230,L=58,R=10,T=14,B=30,mx=0;
  days.forEach(function(x){mx=Math.max(mx,x.s)});
  var top=mx>0?niceMax(mx):4,pw=(W-L-R)/days.length,g='',i;
  for(i=0;i<=4;i++){var v=top*i/4,y=T+(H-T-B)*(1-i/4);g+='<line class="g-line" x1="'+L+'" x2="'+(W-R)+'" y1="'+y+'" y2="'+y+'"/><text class="g-txt" x="'+(L-6)+'" y="'+(y+4)+'" text-anchor="end">'+(v>=1e6?(v/1e6).toFixed(v%1e6?1:0)+'M':fmt(v))+'</text>'}
  days.forEach(function(x,j){if(x.d.getDay()%6===0)g+='<rect class="we-bg" x="'+(L+pw*j)+'" y="'+T+'" width="'+pw+'" height="'+(H-T-B)+'"/>'});
  var pts=[],base=T+(H-T-B);
  days.forEach(function(x,j){
    var cx=L+pw*j+pw/2,y=base-(H-T-B)*(top?x.s/top:0);pts.push([cx,y,x]);
    if((days.length-1-j)%5===0)g+='<text class="g-txt" x="'+cx+'" y="'+(H-10)+'" text-anchor="middle">'+dm(x.d)+'</text>';
  });
  var line=pts.map(function(p){return p[0].toFixed(1)+','+p[1].toFixed(1)}).join(' ');
  g+='<polygon class="l-area" points="'+pts[0][0].toFixed(1)+','+base+' '+line+' '+pts[pts.length-1][0].toFixed(1)+','+base+'"/>';
  g+='<polyline class="l-plan" points="'+line+'"/>';
  pts.forEach(function(p){if(p[2].s>0)g+='<circle class="l-dot" cx="'+p[0].toFixed(1)+'" cy="'+p[1].toFixed(1)+'" r="3.5"><title>'+dm(p[2].d)+': '+money(p[2].s)+'</title></circle>'});
  g+='<line id="bzcur" class="l-cur" x1="0" x2="0" y1="'+T+'" y2="'+base+'" style="opacity:0"/>';
  BZ={days:days,W:W,L:L,R:R,pw:pw};
  g+='<rect id="bzov" x="'+L+'" y="'+T+'" width="'+(W-L-R)+'" height="'+(H-T-B)+'" fill="transparent"/>';
  return '<svg class="bzc" viewBox="0 0 '+W+' '+H+'" width="100%" role="img" aria-label="'+t('bz_chart')+'">'+g+'</svg><div class="tip" id="bztip"></div>';
}
document.addEventListener('pointermove',function(ev){
  var o=ev.target&&ev.target.id==='bzov'?ev.target:null,tip=$('#bztip');
  if(!tip||!BZ)return;
  var cur=$('#bzcur');
  if(!o){tip.style.opacity=0;if(cur)cur.style.opacity=0;return}
  var r=o.getBoundingClientRect(),i=Math.floor((ev.clientX-r.left)/r.width*BZ.days.length);i=Math.max(0,Math.min(BZ.days.length-1,i));
  var x=BZ.days[i];
  if(cur){var cxs=BZ.L+BZ.pw*(i+.5);cur.setAttribute('x1',cxs);cur.setAttribute('x2',cxs);cur.style.opacity=1}
  tip.innerHTML='<b>'+dfmt(x.d)+', '+wkd(x.d)+'</b><br>'+t('bz_shipped')+': <span class="mono">'+m0(x.s)+'</span><br>'+t('bz_ndoc')+': <span class="mono">'+x.n+'</span>';
  tip.style.opacity=1;
  var ch=tip.parentNode.getBoundingClientRect(),tw=tip.offsetWidth,cx=r.left-ch.left+(i+.5)/BZ.days.length*r.width;
  tip.style.transform='translate('+Math.max(0,Math.min(ch.width-tw,cx-tw/2))+'px,6px)';
});
function feedItems(){
  var a=[];
  INV.forEach(function(v){if(v.status==='posted')a.push({d:v.date,ic:NI.dn,c:'',x:v.no+' · '+CUS[v.cus].n,s:t('nav_inv'),m:'− '+money(rsum(v.rows)),sec:'inv'})});
  REC.forEach(function(v){if(v.status==='posted')a.push({d:v.date,ic:NI.rec,c:'',x:v.no+' · '+SUP[v.sup].n,s:t('nav_rec'),m:money(rsum(v.rows)),sec:'rec'})});
  FIN.forEach(function(f){if(f.status!=='posted'||f.kind==='tr')return;var who=f.cus>-1?CUS[f.cus].n:f.sup>-1?SUP[f.sup].n:f.party;a.push({d:f.date,ic:NI.money,c:f.kind==='in'?'in':'out',x:f.no+(who?' · '+who:''),s:t(f.kind==='in'?'f_pay_in':'f_pay_out'),m:(f.kind==='in'?'+ ':'− ')+money(f.amt),sec:ACC[f.acc].t})});
  return a.filter(function(x){return lvl(x.sec)>0}).sort(function(x,y){return y.d-x.d}).slice(0,8);
}
function bizTile(href,ic,label,val,sub,cls){return '<a class="bt '+(cls||'')+'" href="'+href+'"><span class="lb">'+svgi(ic,16)+label+'</span><span class="v" data-n="'+val+'">'+m0(0)+'<small>'+t('cur')+'</small></span><span class="sb">'+sub+'</span></a>'}
function renderBiz(){
  var box=$('#biz');if(!box||!ME)return;
  var d=bizData(),db=totalDebts(),lo=lowItems(),od=overdueOrders(),cash=0,tiles='';
  var bankT=accList('bank').reduce(function(a,i){return a+accBal(i)},0),cashT=accList('cash').reduce(function(a,i){return a+accBal(i)},0);
  var openOrd=ORD.filter(function(o){return o.status!=='deleted'&&ordState(o)!=='shipped'}).length;
  if(lvl('inv')>0)tiles+=bizTile('#invoices',NI.inv,t('bz_sales'),d.s30,tf('bz_sub_inv',{n:d.n30}));
  if(lvl('cus')>0)tiles+=bizTile('#customers',NI.cus,t('bz_recv'),db.r,'',db.r>0?'':'good');
  if(lvl('sup')>0)tiles+=bizTile('#suppliers',NI.sup,t('bz_pay'),db.p,'');
  if(lvl('bank')>0)tiles+=bizTile('#bank',NI.bank,t('bz_bank'),bankT,tf('bz_n_acc',{n:accList('bank').length}),bankT<0?'bad':'');
  if(lvl('cash')>0)tiles+=bizTile('#cash',NI.cash,t('bz_cashd'),cashT,tf('bz_n_acc',{n:accList('cash').length}),cashT<0?'bad':'');
  var small='';
  if(lvl('ord')>0)small+='<a class="bt" href="#orders"><span class="lb">'+svgi(NI.ord,16)+t('bz_ord')+'</span><span class="v" data-i="'+openOrd+'">'+openOrd+'</span><span class="sb">'+(od.length?tf('bz_sub_ord',{n:od.length}):'&nbsp;')+'</span></a>';
  if(lvl('wh')>0)small+='<a class="bt '+(lo.length?'bad':'good')+'" href="#warehouse"><span class="lb">'+svgi(NI.warn,16)+t('bz_low')+'</span><span class="v">'+lo.length+'</span><span class="sb">&nbsp;</span></a>';
  var h='<div class="bz-hero"><div class="bz-hi"><h1>'+tf('bz_hello',{m:ME.n.split(' ')[0]})+'</h1><p>'+tf('bz_today',{n:d.tn,m:money(d.tod)})+'</p></div><div class="bz-clock" role="timer" aria-label="'+t('bz_live')+'"><span class="live"><i></i><span>'+t('bz_live')+'</span></span><b class="mono" id="clock2"></b><span class="bz-date" id="clockd"></span></div></div>';
  h+='<div class="btiles">'+tiles+small+'</div>';
  var main='';
  if(lvl('inv')>0||lvl('cus')>0){
    main+='<div class="panel"><h2>'+t('bz_chart')+'</h2><div class="chart">'+chartBiz(d.days)+'</div><details class="data" id="bzdet"'+(BZOPEN?' open':'')+'><summary>'+t('show_data')+'</summary><div class="scroll">'+bzTable(d.days)+'</div></details></div>';
  }
  if(main)h+='<div class="bgrid" style="grid-template-columns:1fr">'+main+'</div>';
  var lists='';
  if(lvl('cus')>0){
    var ds=[];CUS.forEach(function(c,i){if(!c.gone){var v=custDebt(i);if(v>0)ds.push([c.n,v,custAging(i).overdue>0])}});ds.sort(function(a,b){return b[1]-a[1]});ds=ds.slice(0,5);
    lists+='<div class="panel"><h2>'+t('bz_debtors')+'</h2>'+(ds.length?'<ul class="bl">'+ds.map(function(x){return '<li><div class="r1"><span>'+esc(x[0])+(x[2]?flameHtml():'')+'</span><b>'+money(x[1])+'</b></div><div class="bar"><i style="width:'+Math.max(4,Math.round(x[1]/ds[0][1]*100))+'%"></i></div></li>'}).join('')+'</ul>':'<p class="empty">'+t('bz_nodebt')+'</p>')+'</div>';
  }
  if(lvl('wh')>0){
    var ls=lo.slice().sort(function(a,b){return a.tot/Math.max(a.min,1)-b.tot/Math.max(b.min,1)}).slice(0,6);
    lists+='<div class="panel"><h2>'+t('bz_stock')+'</h2>'+(ls.length?'<ul class="bl">'+ls.map(function(x){var pc=x.min?Math.min(100,Math.round(x.tot/x.min*100)):0;return '<li><div class="r1"><span>'+esc(iname(x))+'</span><b>'+fmt(x.tot)+' / '+tf('bz_min',{n:fmt(x.min)})+'</b></div><div class="bar"><i class="'+(x.s==='out'?'bad':'warn')+'" style="width:'+Math.max(3,pc)+'%"></i></div></li>'}).join('')+'</ul>':'<p class="empty">'+t('bz_nostock')+'</p>')+'</div>';
  }
  var accs=accList().filter(function(i){return lvl(ACC[i].t)>0});
  if(accs.length){
    var mx=Math.max.apply(null,accs.map(function(i){return Math.abs(accBal(i))}))||1;
    lists='<div class="panel"><h2>'+t('bz_accs')+'</h2><ul class="bl">'+accs.map(function(i){var b=accBal(i);return '<li><div class="r1"><span>'+svgi(ACC[i].t==='bank'?NI.bank:NI.cash,15)+' '+esc(aname(i))+'</span><b>'+money(b)+'</b></div><div class="bar"><i class="'+(b<0?'bad':'')+'" style="width:'+Math.max(3,Math.round(Math.abs(b)/mx*100))+'%"></i></div></li>'}).join('')+'</ul></div>'+lists;
  }
  if(lists)h+='<div class="bgrid3">'+lists+'</div>';
  box.innerHTML=h;
  box.querySelectorAll('[data-n]').forEach(function(el){numTo(el,+el.dataset.n)});
  tickClock();
}
var DAYS={uz:['yakshanba','dushanba','seshanba','chorshanba','payshanba','juma','shanba'],ru:['воскресенье','понедельник','вторник','среда','четверг','пятница','суббота'],en:['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']};
var MONS={uz:['yanvar','fevral','mart','aprel','may','iyun','iyul','avgust','sentabr','oktabr','noyabr','dekabr'],ru:['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'],en:['January','February','March','April','May','June','July','August','September','October','November','December']};
function dateLine(d){var l=DAYS[lang]?lang:'en';return DAYS[l][d.getDay()]+', '+d.getDate()+' '+MONS[l][d.getMonth()]+' '+d.getFullYear()}
function tickClock(){
  var d=new Date(),s=pad2(d.getHours())+':'+pad2(d.getMinutes())+':'+pad2(d.getSeconds());
  var a=$('#clock'),b=$('#clock2');if(a)a.textContent=s;if(b)b.textContent=s;
  var c=$('#clockd');if(c)c.textContent=dateLine(d);
}
var busT=null;
function busTick(){
  clearTimeout(busT);
  busT=setTimeout(function(){bellUpdate();if(location.hash==='#dashboard')renderBiz()},60);
}
setInterval(function(){tickClock();if(document.visibilityState==='visible')bellUpdate()},1000);

