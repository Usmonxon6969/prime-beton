/* Dashboard: one card per plant (workshop warehouse) with today's output, a 14-day output strip and the number of products in stock. */
(function(){
var X={
 pl_h:['Plants','Заводы','Zavodlar'],pl_today:['Made today','Выпущено сегодня','Bugun ishlab chiqarildi'],
 pl_14:['Last 14 days','Последние 14 дней','Oxirgi 14 kun'],pl_month:['Made this month','Выпущено за месяц','Shu oyda ishlab chiqarildi'],pl_prev:['Last month','Прошлый месяц','O‘tgan oy'],pl_ofprev:['of last month','от прошлого месяца','o‘tgan oydan'],pl_more:['more than last month','больше прошлого месяца','o‘tgan oydan ko‘p'],pl_noprev:['No output last month','В прошлом месяце выпуска не было','O‘tgan oy ishlab chiqarish bo‘lmagan'],pl_stock:['Products in stock','Продукции на складе','Omborda mahsulot'],
 pl_t_slab:['Slabs','Плиты','Plita'],pl_t_tray:['Trays','Лотки','Lotok'],pl_t_pole:['Poles','Опоры','Stolba'],pl_t_block:['Blocks','Блоки','Blok'],pl_t_other:['Other','Прочее','Boshqa'],
 pl_none:['No production yet','Пока нет выпуска','Hali ishlab chiqarish yo‘q'],pl_pcs:['pcs','шт','dona'],
 pl_empty:['No plants yet. Create a plant in Settings.','Заводов пока нет. Создайте завод в настройках.','Hali zavod yo‘q. Sozlamalarda zavod yarating.']
};
Object.keys(X).forEach(function(k){T.en[k]=X[k][0];T.ru[k]=X[k][1];T.uz[k]=X[k][2]});
function key(d){return d.getFullYear()*10000+(d.getMonth()+1)*100+d.getDate()}
var MN={uz:['Yanvar','Fevral','Mart','Aprel','May','Iyun','Iyul','Avgust','Sentabr','Oktabr','Noyabr','Dekabr'],
 ru:['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'],
 en:['January','February','March','April','May','June','July','August','September','October','November','December']};
function mname(m){return (MN[lang]||MN.en)[m]}
/* what kind of product a name is: 2ПК slab, tray, pole (Опора / стойка / столб), FBS block, anything else */
function ptype(n){n=(n||'').toLowerCase();
  if(/(^|\s)2\s*(п|p)(к|k)|плит|plita/.test(n))return 'slab';
  if(/лот(о)?к|lotok|tray/.test(n))return 'tray';
  if(/опор|стойк|столб|ustun|stolba|pole/.test(n))return 'pole';
  if(/фбс|fbs|блок|blok/.test(n))return 'block';
  return 'other'}
var PT=['slab','tray','pole','block','other'];
window.ptype=ptype;window.PT_KEYS=PT;
function plantCards(){
  var end=today0(),y=end.getFullYear(),m=end.getMonth(),tk=key(end),pm=m?m-1:11,py=m?y:y-1;
  return SITES.map(function(name,s){
    var by={},today=0,cur=0,prev=0,kinds={};
    for(var d=1;d<=end.getDate();d++)by[key(new Date(y,m,d))]=0;
    plog.forEach(function(v){
      if(v.status==='deleted'||v.site!==s)return;
      var q=0;v.rows.forEach(function(r){q+=r.q});
      var dt=v.date,k=key(dt);
      if(dt.getFullYear()===y&&dt.getMonth()===m){v.rows.forEach(function(r){var k2=ptype(PRODUCTS[r.p]);kinds[k2]=(kinds[k2]||0)+r.q});cur+=q;if(k in by)by[k]+=q;if(k===tk)today+=q}
      else if(dt.getFullYear()===py&&dt.getMonth()===pm)prev+=q;
    });
    var inStock=0;
    ITEMS.forEach(function(x){if(!itemGone(x)&&x.fg&&x.st&&x.st[s]>0)inStock++});
    var days=Object.keys(by).sort();
    var mx=Math.max.apply(null,days.map(function(k){return by[k]}))||1;
    var bars=days.map(function(k){var h=by[k]?Math.max(10,Math.round(by[k]/mx*100)):4;return '<i class="'+(by[k]?'on':'')+'" style="height:'+h+'%"></i>'}).join('');
    var types=PT.filter(function(k){return kinds[k]>0}).map(function(k){return '<span><i>'+t('pl_t_'+k)+'</i> <b class="mono">'+fmt(kinds[k])+'</b></span>'}).join('');
    var pct=prev>0?Math.round(cur/prev*100):null;
    var cmp='<div class="pcmp"><div class="pcl"><span>'+t('pl_prev')+' · '+mname(pm)+'</span><b class="mono">'+fmt(prev)+' <small>'+t('pl_pcs')+'</small></b></div>'+
      (prev>0?'<div class="ptrack" role="img" aria-label="'+pct+'%"><i class="'+(cur>=prev?'ahead':'')+'" style="width:'+Math.min(100,pct)+'%"></i></div><div class="pcs">'+(cur>=prev?'<b class="up">+'+(pct-100)+'%</b> ':'<b>'+pct+'%</b> ')+t(cur>=prev?'pl_more':'pl_ofprev')+'</div>':'<div class="pcs">'+t('pl_noprev')+'</div>')+'</div>';
    return '<a class="plant'+(SITES.length===1?' wide':'')+'" href="#production"><div class="ph"><b>'+esc(name)+'</b></div>'+
      '<div class="pm"><span>'+t('pl_month')+' · '+mname(m)+'</span><b class="mono">'+fmt(cur)+' <small>'+t('pl_pcs')+'</small></b></div>'+
      (types?'<div class="ptp">'+types+'</div>':'')+
      '<div class="pbars" role="img" aria-label="'+mname(m)+'">'+bars+'</div>'+
      cmp+
      '<div class="pf"><span>'+t('pl_today')+': <b class="mono">'+fmt(today)+'</b></span><span>'+t('pl_stock')+': <b class="mono">'+inStock+'</b></span></div></a>';
  }).join('');
}
var _rb=renderBiz;
renderBiz=function(){
  _rb();
  var box=$('#biz');if(!box||!ME||lvl('prod')<=0)return;
  var old=box.querySelector('.plants');if(old)old.remove();
  var html='<section class="plants"><h2>'+t('pl_h')+'</h2>'+(SITES.length?'<div class="plgrid'+(SITES.length===1?' one':'')+'">'+plantCards()+'</div>':'<p class="note">'+t('pl_empty')+'</p>')+'</section>';
  var tiles=box.querySelector('.btiles');
  if(tiles)tiles.insertAdjacentHTML('afterend',html);
};
})();
