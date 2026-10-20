/* warehouse + products */
var WH=[],WHGONE=[];function whIdx(){var a=[];WH.forEach(function(n,i){if(!WHGONE[i])a.push(i)});return a}
var UNITS=[];
function uname(u){var x=UNITS[u]||UNITS[0];return x?(x.n[lang]||x.n.en):''}
function iu(x){return x.u!=null?x.u:(x.fg?0:1)}
function punit(p){var it=p>=0?ITEM_BY[PRODUCTS[p]]:null;return it?iu(it):0}
function unitOpts(sel){return UNITS.map(function(x,i){return x.gone&&i!==sel?'':'<option value="'+i+'"'+(i===sel?' selected':'')+'>'+esc(uname(i))+'</option>'}).join('')}
var ITEMS=[];
function recalcItem(x){x.tot=x.st.reduce(function(a,b){return a+b},0);x.s=x.tot<=0?'out':(x.tot<x.min?'low':'ok')}
var ITEM_BY={},MAT_BY={};
function refreshStock(){renderWh();renderItems()}
var wf='all',ic='all',ws=-1;
function iname(x){return x.fg?x.n:mname(x.m)}
function iunit(x){return uname(iu(x))}
function renderWh(){
  var sel=$('#wsite');
  sel.innerHTML='<option value="-1"></option>'+whIdx().map(function(j){return '<option value="'+j+'">'+esc(WH[j])+'</option>'}).join('');
  sel.options[0].textContent=t('w_allsites');sel.value=String(ws);
  var site=ws>=0;
  var fgT=0,inN=0,lowN=0,am=activeMats(),shown=am.length>1?[am[0],am[am.length-1]]:am,mt={};
  ITEMS.forEach(function(x){
    var b=site?x.st[ws]:x.tot;
    if(b>0)inN++;
    if(x.fg)fgT+=b;else mt[x.m]=b;
    if(x.min>0&&x.s!=='ok')lowN++;
  });
  var tiles=[[t('w_k1'),fmt(fgT),t('unit')]];
  shown.forEach(function(j){var it=MAT_BY[j];tiles.push([mname(j),fmt(mt[j]||0),it?uname(iu(it)):t('kg')])});
  tiles.push([t('w_k5'),fmt(inN),'']);
  $('#wkpis').innerHTML=tiles.map(function(x){return '<div class="kpi"><div class="lb">'+x[0]+'</div><div class="val mono">'+x[1]+(x[2]?'<small>'+x[2]+'</small>':'')+'</div></div>'}).join('');
  $('#whf').parentNode.hidden=site;
  document.querySelectorAll('#whf button').forEach(function(b){var low=b.dataset.w==='low';b.textContent=low?t('w_low')+' ('+lowN+')':t('w_all');b.setAttribute('aria-pressed',String(b.dataset.w===wf))});
  $('#wq').placeholder=t('it_search');$('#wq').setAttribute('aria-label',t('it_search'));
  var q=($('#wq').value||'').trim().toLowerCase().replace(/\./g,',');
  var list=ITEMS.filter(function(x){
    if(q&&iname(x).toLowerCase().replace(/\./g,',').indexOf(q)<0)return false;
    if(site)return x.st[ws]>0;
    return (x.tot>0||x.min>0)&&(wf==='all'||(x.min>0&&x.s!=='ok'));
  });
  var head,body,cols;
  if(site){
    cols=3;
    head='<thead><tr><th>'+t('c_prod')+'</th><th>'+t('c_unit')+'</th><th class="num">'+t('c_stock')+'</th></tr></thead>';
    body=list.map(function(x){return '<tr><td>'+iname(x)+'</td><td>'+iunit(x)+'</td><td class="num"><b>'+fmt(x.st[ws])+'</b></td></tr>'}).join('');
  }else{
    cols=whIdx().length+5;
    head='<thead><tr><th>'+t('c_prod')+'</th><th>'+t('c_unit')+'</th>'+whIdx().map(function(i){return '<th class="num">'+esc(WH[i])+'</th>'}).join('')+'<th class="num">'+t('c_total')+'</th><th class="num">'+t('c_min')+'</th><th>'+t('c_level')+'</th></tr></thead>';
    body=list.map(function(x){
      var pct=x.min>0?Math.min(100,x.tot/(x.min*2)*100):0;
      return '<tr><td>'+iname(x)+'</td><td>'+iunit(x)+'</td>'+whIdx().map(function(i){var v=x.st[i];return '<td class="num">'+(v?fmt(v):'–')+'</td>'}).join('')+
        '<td class="num"><b>'+fmt(x.tot)+'</b></td><td class="num">'+(x.min>0?fmt(x.min):'–')+'</td>'+
        '<td><div class="lvl">'+(x.min>0?'<span class="gauge'+(x.s==='low'?' low':'')+'" aria-hidden="true"><i style="width:'+pct.toFixed(0)+'%"></i><b></b></span>':'')+pill(x.s,'stk_'+x.s)+'</div></td></tr>';
    }).join('');
  }
  if(!list.length)body='<tr><td class="empty" colspan="'+cols+'">'+t('it_empty')+'</td></tr>';
  $('#wtbl').innerHTML=head+'<tbody>'+body+'</tbody>';
}
function renderItems(){
  var q=($('#itq').value||'').trim().toLowerCase().replace(/\./g,',');
  $('#itq').placeholder=t('it_search');$('#itq').setAttribute('aria-label',t('it_search'));
  document.querySelectorAll('#itc button').forEach(function(b){b.textContent=t({all:'f_all',fg:'cat_fg',mat:'cat_mat',stock:'it_instock'}[b.dataset.c]);b.setAttribute('aria-pressed',String(b.dataset.c===ic))});
  var list=ITEMS.filter(function(x){
    if(ic==='fg'&&!x.fg)return false;
    if(ic==='mat'&&x.fg)return false;
    if(ic==='stock'&&!(x.tot>0))return false;
    return !q||iname(x).toLowerCase().replace(/\./g,',').indexOf(q)>-1;
  });
  var head='<thead><tr><th>'+t('c_prod')+'</th><th>'+t('c_cat')+'</th><th>'+t('c_unit')+'</th><th class="num">'+t('c_stock')+'</th><th>'+t('c_status')+'</th><th><span class="vh">'+t('m_actions')+'</span></th></tr></thead>';
  var body=list.length?list.map(function(x){
    return '<tr><td>'+iname(x)+'</td><td>'+t(x.fg?'cat_fg':'cat_mat')+'</td><td>'+iunit(x)+'</td><td class="num">'+fmt(x.tot)+'</td><td>'+pill(x.s,'stk_'+x.s)+'</td><td class="act">'+(x.fg?gnActs(x):kebabHtml('gm',x.m,iname(x)))+'</td></tr>';
  }).join(''):'<tr><td class="empty" colspan="6">'+t('it_empty')+'</td></tr>';
  $('#itbl').innerHTML=head+'<tbody>'+body+'</tbody>';
  renderGnForm();renderGnMsg();
}
document.querySelectorAll('#whf button').forEach(function(b){b.addEventListener('click',function(){wf=b.dataset.w;renderWh()})});
document.querySelectorAll('#itc button').forEach(function(b){b.addEventListener('click',function(){ic=b.dataset.c;renderItems()})});
$('#itq').addEventListener('input',renderItems);
$('#wsite').addEventListener('change',function(){ws=+this.value;if(ws>=0)wf='all';renderWh()});
$('#wq').addEventListener('input',renderWh);

