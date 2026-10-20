/* overview slips */
function renderSlips(){
  var s=[['req','REQ-000431',1,'posted','4 800 kg'],['rpt','RPT-000431',1,'posted','1 186 '+t('unit')],['rcv','RCV-000431',2,'pending','1 120 '+t('unit')]];
  var rows=s.map(function(x){return '<div class="slip"><div><div class="no">'+x[1]+'</div><div class="ty">'+t(x[0])+'</div><div class="meta">'+t('dr_plant')+' '+(x[2]+1)+'</div></div><div class="qty">'+x[4]+'</div><div></div>'+pill(x[3])+'</div>'}).join('');
  document.querySelectorAll('.ledger').forEach(function(L){L.innerHTML=rows});
}

/* production dashboard: built from the posted production documents */
var NEWK={
 k_avg:['Daily average','Среднее в день','Kunlik o‘rtacha'],
 k_docs:['Documents','Документы','Hujjatlar'],
 k_low:['Below minimum stock','Ниже минимального остатка','Minimal qoldiqdan past'],
 k_types:['By product type','По видам продукции','Mahsulot turlari bo‘yicha'],
 dt_docs:['Documents','Документы','Hujjatlar'],
 dt_out:['Output','Выпуск','Ishlab chiqarish'],
 dt_active:['Days with output','Дней с выпуском','Ishlab chiqarilgan kunlar'],
 dt_empty:['No production documents in this period.','Нет документов производства за этот период.','Bu davrda ishlab chiqarish hujjatlari yo‘q.'],
 dash_note2:['Based on posted production documents.','По проведённым документам производства.','O‘tkazilgan ishlab chiqarish hujjatlari asosida.']
};
Object.keys(NEWK).forEach(function(k){T.en[k]=NEWK[k][0];T.ru[k]=NEWK[k][1];T.uz[k]=NEWK[k][2]});
['en','ru','uz'].forEach(function(l){T[l].dash_note=T[l].dash_note2});
function dayStart(d){var x=new Date(d);x.setHours(0,0,0,0);return x}
function prodDays(){
  var end=dayStart(new Date()),n=period*2,out=[],map={},i;
  for(i=n-1;i>=0;i--){var d=new Date(end);d.setDate(end.getDate()-i);var o={d:d,a:0,n:0};out.push(o);map[dayKey(d)]=o}
  plog.forEach(function(x){if(x.status!=='posted')return;var o=map[dayKey(x.date)];if(o){o.a+=docTotal(x);o.n++}});
  return out;
}
function cur(){var a=prodDays();return a.slice(period)}
function prev(){var a=prodDays();return a.slice(0,period)}
function sum(a,k){return a.reduce(function(s,x){return s+x[k]},0)}
function avg(a,k){return a.length?sum(a,k)/a.length:0}
function spark(vals,color){
  var w=88,h=28,mn=Math.min.apply(null,vals),mx=Math.max.apply(null,vals),r=mx-mn||1;
  var pts=vals.map(function(v,i){return [2+i*(w-8)/(vals.length-1),h-3-((v-mn)/r)*(h-8)]});
  var last=pts[pts.length-1];
  return '<svg width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'" aria-hidden="true"><polyline points="'+pts.map(function(p){return p[0].toFixed(1)+','+p[1].toFixed(1)}).join(' ')+'" fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/><circle cx="'+last[0].toFixed(1)+'" cy="'+last[1].toFixed(1)+'" r="3.5" fill="var(--s1)" stroke="var(--surface)" stroke-width="2"/></svg>';
}
function deltaHtml(diff,text,goodWhenUp){
  var up=diff>=0,good=(diff===0)?true:(up===goodWhenUp);
  var arrow=up?'<path d="M5 1.5l3.5 5h-7z" fill="currentColor"/>':'<path d="M5 8.5l-3.5-5h7z" fill="currentColor"/>';
  return '<span class="delta '+(good?'good':'bad')+'"><svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">'+arrow+'</svg>'+text+'</span>';
}
function sgn(n,dec,suf){return (n>=0?'+':'−')+Math.abs(n).toFixed(dec)+suf}
/* output of the shown period split by kind of product: slabs, trays, poles ... (kinds come from plants.js) */
function typesKpi(c){
  var keys={},kinds={};c.forEach(function(x){keys[dayKey(x.d)]=1});
  plog.forEach(function(v){if(v.status!=='posted'||!keys[dayKey(v.date)])return;
    v.rows.forEach(function(r){var k=window.ptype?window.ptype(PRODUCTS[r.p]):'other';kinds[k]=(kinds[k]||0)+r.q})});
  var ks=(window.PT_KEYS||['other']).filter(function(k){return kinds[k]>0});
  return ks.length?'<div class="ktypes">'+ks.map(function(k){return '<div><span>'+t('pl_t_'+k)+'</span><b class="mono">'+fmt(kinds[k])+'</b></div>'}).join('')+'</div>':'<div class="vs">—</div>';
}
function renderKpis(){
  var c=cur(),p=prev();
  var out=sum(c,'a'),outP=sum(p,'a'),av=avg(c,'a'),avP=avg(p,'a'),dn=sum(c,'n'),dnP=sum(p,'n'),low=lowItems().length;
  var pct=function(a,b){return b?(a/b-1)*100:0};
  var k=[
    {l:t('k_out'),v:fmt(out),u:t('unit'),s:c.map(function(x){return x.a}),dl:deltaHtml(out-outP,sgn(pct(out,outP),1,'%'),true)},
    {l:t('k_avg'),v:fmt(av),u:t('unit'),s:c.map(function(x){return x.a}),dl:deltaHtml(av-avP,sgn(pct(av,avP),1,'%'),true)},
    {l:t('k_docs'),v:fmt(dn),u:'',s:c.map(function(x){return x.n}),dl:deltaHtml(dn-dnP,sgn(dn-dnP,0,''),true)},
    {l:t('k_types'),html:typesKpi(c)}
  ];
  $('#kpis').innerHTML=k.map(function(x){if(x.html)return '<div class="kpi"><div class="lb">'+x.l+'</div>'+x.html+'</div>';
    return '<div class="kpi"><div class="lb">'+x.l+'</div><div class="val mono">'+x.v+(x.u?'<small>'+x.u+'</small>':'')+'</div><div class="row">'+x.dl+(x.s?spark(x.s):'')+'</div>'+(x.s?'<div class="vs">'+t('vs')+'</div>':'')+'</div>'}).join('');
}
function niceMax(v){
  var step=Math.pow(10,Math.floor(Math.log10(v/4))),m=[1,2,2.5,5,10];
  for(var i=0;i<m.length;i++){if(m[i]*step*4>=v)return m[i]*step*4}
  return v;
}
function drawDaily(){
  var el=$('#daily');if(!el||$('#view-dash').hidden)return;
  var c=cur(),n=c.length,W=Math.max(el.clientWidth,260),H=250,m={l:46,r:6,t:8,b:26};
  var pw=W-m.l-m.r,ph=H-m.t-m.b,mx=niceMax(Math.max(4,Math.max.apply(null,c.map(function(x){return x.a}))));
  var y=function(v){return m.t+ph-(v/mx)*ph},band=pw/n,bw=Math.min(18,Math.max(3,band*.58));
  var s='<svg width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'" role="img" aria-label="'+t('chart_daily')+'">';
  for(var i=0;i<=4;i++){var v=mx/4*i,yy=y(v);
    s+='<line class="'+(i===0?'g-axis':'g-line')+'" x1="'+m.l+'" x2="'+(W-m.r)+'" y1="'+yy+'" y2="'+yy+'"/>';
    s+='<text class="g-txt" x="'+(m.l-8)+'" y="'+(yy+4)+'" text-anchor="end">'+fmt(v)+'</text>';}
  s+='<rect class="hl" id="hl" x="0" y="'+m.t+'" width="'+band+'" height="'+ph+'"/>';
  var step=Math.max(1,Math.ceil(n/Math.floor(pw/48)));
  c.forEach(function(x,i){
    var cx=m.l+band*(i+.5),x0=cx-bw/2,yt=y(x.a),yb=y(0),r=Math.min(3,bw/2,Math.max(yb-yt,0));
    if(x.a>0)s+='<path class="b-act" d="M'+x0+','+yb+' V'+(yt+r)+' Q'+x0+','+yt+' '+(x0+r)+','+yt+' H'+(x0+bw-r)+' Q'+(x0+bw)+','+yt+' '+(x0+bw)+','+(yt+r)+' V'+yb+' Z"/>';
    if((n-1-i)%step===0)s+='<text class="g-txt" x="'+cx+'" y="'+(H-8)+'" text-anchor="middle">'+dm(x.d)+'</text>';
  });
  s+='<rect id="ov" x="'+m.l+'" y="'+m.t+'" width="'+pw+'" height="'+ph+'" fill="transparent"/></svg><div class="tip" id="tip"></div>';
  el.innerHTML=s;
  var tip=$('#tip'),hl=$('#hl'),ov=$('#ov');
  function show(ev){
    var r=ov.getBoundingClientRect(),i=Math.floor((ev.clientX-r.left)/band);i=Math.max(0,Math.min(n-1,i));
    var x=c[i];hl.setAttribute('x',m.l+band*i);hl.style.opacity=1;
    tip.innerHTML='<b>'+dfmt(x.d)+', '+wkd(x.d)+'</b><br>'+t('dt_out')+': <span class="mono">'+fmt(x.a)+'</span><br>'+t('dt_docs')+': <span class="mono">'+fmt(x.n)+'</span>';
    tip.style.opacity=1;
    var tw=tip.offsetWidth,cx=m.l+band*(i+.5),left=Math.max(0,Math.min(W-tw,cx-tw/2));
    tip.style.transform='translate('+left+'px,'+(m.t+4)+'px)';
  }
  function hide(){tip.style.opacity=0;hl.style.opacity=0}
  ov.addEventListener('pointermove',show);ov.addEventListener('pointerdown',show);ov.addEventListener('pointerleave',hide);
}
function wkd(d){return d.toLocaleDateString(LOC[lang],{weekday:'long'})}
function renderDataTable(){
  var c=cur(),act=c.filter(function(x){return x.a>0});
  if(!act.length){$('#dataTable').innerHTML='<p class="empty">'+t('dt_empty')+'</p>';return}
  var best=act.reduce(function(m,x){return x.a>m.a?x:m},act[0]),worst=act.reduce(function(m,x){return x.a<m.a?x:m},act[0]);
  var chip=function(l,v,sub){return '<div class="dt-chip"><span>'+l+'</span><b class="mono">'+v+'</b><small>'+sub+'</small></div>'};
  var top='<div class="dt-sum">'+chip(t('dt_active'),act.length+' / '+c.length,'')+chip(t('dt_best'),fmt(best.a),dfmt(best.d)+', '+wkd(best.d))+chip(t('dt_worst'),fmt(worst.a),dfmt(worst.d)+', '+wkd(worst.d))+'</div>';
  var mx=best.a||1;
  var rows=c.slice().reverse().map(function(x){
    var we=x.d.getDay()===0||x.d.getDay()===6;
    return '<tr><td class="dt-d"><b class="mono">'+dfmt(x.d)+'</b><small'+(we?' class="we"':'')+'>'+wkd(x.d)+'</small></td><td class="num">'+(x.n||'<span class="dt-z">—</span>')+'</td><td class="num">'+(x.a?fmt(x.a):'<span class="dt-z">—</span>')+'</td><td class="dt-bar"><div class="bar"><i style="width:'+Math.round(x.a/mx*100)+'%"></i></div></td></tr>';
  }).join('');
  var days=lang==='ru'?'дн.':lang==='uz'?'kun':'days';
  var foot='<tr><td class="dt-d"><b>'+t('dt_total')+'</b><small>'+c.length+' '+days+'</small></td><td class="num">'+fmt(sum(c,'n'))+'</td><td class="num">'+fmt(sum(c,'a'))+'</td><td></td></tr>';
  $('#dataTable').innerHTML=top+'<table class="dt"><thead><tr><th>'+t('c_date')+'</th><th class="num">'+t('dt_docs')+'</th><th class="num">'+t('dt_out')+'</th><th></th></tr></thead><tbody>'+rows+'</tbody><tfoot>'+foot+'</tfoot></table>';
}
function renderSites(){
  var c=plog.filter(function(x){return x.status==='posted'&&x.date>=dayStart(new Date(Date.now()-(period-1)*864e5))});
  var by=SITES.map(function(n,i){return c.reduce(function(s,x){return s+(x.site===i?docTotal(x):0)},0)}),mx=Math.max.apply(null,by.concat([0]));
  $('#sites').innerHTML=SITES.length?SITES.map(function(n,i){var v=by[i];return '<div class="site"><span class="nm">'+esc(n)+'</span><span class="v">'+fmt(v)+' '+t('unit')+'</span><div class="track"><div class="fill" style="width:'+(mx?v/mx*100:0).toFixed(1)+'%"></div></div></div>'}).join(''):'<p class="empty">'+t('it_empty')+'</p>';
}
function renderDash(){
  renderKpis();renderSites();renderDataTable();
  document.querySelectorAll('#periods button').forEach(function(b){b.textContent=t('p'+b.dataset.p);b.setAttribute('aria-pressed',String(+b.dataset.p===period))});
  drawDaily();
}
