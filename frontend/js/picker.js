/* picker: a wide, searchable list for product and customer fields */
T.en.pk_more='%n more. Keep typing to narrow the list.';T.ru.pk_more='Ещё %n. Продолжайте ввод, чтобы сузить список.';T.uz.pk_more='Yana %n ta. Qidiruvni aniqlashtiring.';
T.en.pk_none='Nothing found';T.ru.pk_none='Ничего не найдено';T.uz.pk_none='Hech narsa topilmadi';
var pk={el:null,items:[],act:0,q:'',open:false,silent:false};
function nrm(s){return String(s).toLowerCase().replace(/\./g,',')}
function pkTok(q){return nrm(q).trim().split(/[\s*×]+/).filter(Boolean)}
function pkSource(el){
  var a=[],inv=/^iv/.test(el.id);
  if(el.dataset.pick==='sup'){SUP.forEach(function(c){if(!c.gone)a.push({v:c.n,meta:c.ph||'',dim:false})});return a}
  if(el.dataset.pick==='item'){
    activeMats().forEach(function(j){var it=MAT_BY[j];a.push({v:mname(j),meta:t('cat_mat')+' \u00b7 '+fmt(it?it.st[RS.site]:0)+' '+uname(it?iu(it):1),dim:false})});
    PRODUCTS.forEach(function(n,i){if(PGONE[i])return;var it=ITEM_BY[n];a.push({v:n,meta:t('cat_fg')+' \u00b7 '+fmt(it?it.st[RS.site]:0)+' '+uname(it?iu(it):0),dim:false})});
    return a}
  if(el.dataset.pick==='rpitem'){
    Object.keys(ITEM_NAME).sort(function(x,y){return String(ITEM_NAME[x]).localeCompare(String(ITEM_NAME[y]))}).forEach(function(id){
      var n=ITEM_NAME[id],it=ITEM_BY[n],isM=false;try{isM=activeMats().some(function(j){return mname(j)===n})}catch(_){}
      a.push({v:n,meta:(isM?t('cat_mat'):t('cat_fg'))+(it?' \u00b7 '+fmt(it.tot)+' '+uname(iu(it)):''),dim:false})});
    return a}
  if(el.dataset.pick==='cus'){CUS.forEach(function(c){if(!c.gone)a.push({v:c.n,meta:c.ph||'',dim:false})});return a}
  PRODUCTS.forEach(function(n,i){
    if(PGONE[i])return;
    var it=ITEM_BY[n],have=it?(inv?it.st[IS.site]:it.tot):0;
    a.push({v:n,dim:inv&&have<=0,meta:fmt(have)+' '+uname(it?iu(it):0)});
  });
  return a;
}
function pkFilter(src,q){
  var toks=pkTok(q),qn=nrm(q).trim();
  if(!toks.length)return src.map(function(x,i){return [x.dim?1:0,i,x]}).sort(function(a,b){return a[0]-b[0]||a[1]-b[1]}).map(function(x){return x[2]});
  var star=toks.join('*'),out=[];
  src.forEach(function(x,i){
    var h=nrm(x.v);
    if(!toks.every(function(k){return h.indexOf(k)>-1}))return;
    out.push([h.indexOf(qn)===0?0:(h.indexOf(qn)>-1||h.indexOf(star)>-1)?1:2,i,x]);
  });
  return out.sort(function(a,b){return a[0]-b[0]||a[1]-b[1]}).map(function(x){return x[2]});
}
function pkHl(name){
  var toks=pkTok(pk.q);if(!toks.length)return esc(name);
  var h=nrm(name),mk=[],out='',on=false,j;
  toks.forEach(function(k){var i=h.indexOf(k);if(i>-1)for(j=i;j<i+k.length;j++)mk[j]=1});
  for(j=0;j<name.length;j++){
    if(mk[j]&&!on){out+='<mark>';on=true}
    if(!mk[j]&&on){out+='</mark>';on=false}
    out+=esc(name.charAt(j));
  }
  return on?out+'</mark>':out;
}
function pkRender(){
  var n=Math.min(pk.items.length,60),h='',i;
  for(i=0;i<n;i++){var x=pk.items[i];h+='<div class="o'+(x.dim?' dim':'')+'" role="option" id="pko'+i+'" data-i="'+i+'" aria-selected="'+(i===pk.act)+'"><span class="n">'+pkHl(x.v)+'</span><span class="m">'+esc(x.meta)+'</span></div>'}
  if(pk.items.length>n)h+='<div class="more">'+tf('pk_more',{n:pk.items.length-n})+'</div>';
  if(!pk.items.length)h='<div class="more">'+t('pk_none')+'</div>';
  $('#pk').innerHTML=h;
}
function pkPlace(){
  if(!pk.open||!pk.el)return;
  var p=$('#pk'),r=pk.el.getBoundingClientRect(),vw=window.innerWidth,vh=window.innerHeight;
  var w=Math.min(vw-16,Math.max(r.width,420)),left=Math.max(8,Math.min(r.left,vw-w-8));
  var below=vh-r.bottom-12,above=r.top-12,up=below<220&&above>below,room=Math.max(140,up?above:below);
  p.style.width=w+'px';p.style.left=left+'px';p.style.maxHeight=Math.min(380,room)+'px';
  if(up){p.style.top='';p.style.bottom=(vh-r.top+4)+'px'}else{p.style.bottom='';p.style.top=(r.bottom+4)+'px'}
}
function pkSetAct(i,scroll){
  var items=$('#pk').querySelectorAll('.o');if(!items.length)return;
  pk.act=Math.max(0,Math.min(items.length-1,i));
  items.forEach(function(o,k){o.setAttribute('aria-selected',String(k===pk.act))});
  var cur=items[pk.act];pk.el.setAttribute('aria-activedescendant',cur.id);
  if(scroll&&cur.scrollIntoView)cur.scrollIntoView({block:'nearest'});
}
function pkOpen(el,typed){
  var src=pkSource(el),v=el.value,exact=-1,i;
  for(i=0;i<src.length;i++){if(src[i].v===v||nrm(src[i].v)===nrm(v)){exact=i;break}}
  pk.el=el;pk.q=(typed||exact<0)?v:'';pk.items=pkFilter(src,pk.q);pk.act=0;
  if(!typed&&exact>-1){for(i=0;i<pk.items.length;i++){if(pk.items[i].v===src[exact].v){pk.act=i;break}}}
  pk.open=true;pkRender();$('#pk').hidden=false;pkPlace();
  el.setAttribute('aria-expanded','true');el.setAttribute('aria-controls','pk');
  pkSetAct(pk.act,true);
}
function pkClose(){
  if(!pk.open)return;
  pk.open=false;$('#pk').hidden=true;
  if(pk.el){pk.el.setAttribute('aria-expanded','false');pk.el.removeAttribute('aria-activedescendant')}
}
function pkChoose(i){
  var x=pk.items[i],el=pk.el;if(!x||!el)return;
  pk.silent=true;el.value=x.v;el.dispatchEvent(new Event('input',{bubbles:true}));pk.silent=false;
  pkClose();
  if(el.dataset.k==='p'||el.dataset.k==='m'){var q=el.parentElement.querySelector('input[type=number]');if(q)q.focus()}
}
['#odcus','#ivcus'].forEach(function(s){var e=$(s);e.setAttribute('data-pick','cus')});
document.addEventListener('focusout',function(e){var el=e.target;if(el.dataset&&el.dataset.k==='pr'&&el.closest&&el.closest('.srow')){var v=parseMoney(el.value);el.value=v>0?money(v):''}});
document.addEventListener('focusin',function(e){if(e.target.dataset&&e.target.dataset.pick&&!pk.silent)pkOpen(e.target,false)});
document.addEventListener('input',function(e){if(e.target.dataset&&e.target.dataset.pick&&!pk.silent)pkOpen(e.target,true)});
document.addEventListener('click',function(e){if(e.target.dataset&&e.target.dataset.pick&&!pk.open)pkOpen(e.target,false)});
document.addEventListener('focusout',function(e){if(e.target.dataset&&e.target.dataset.pick){setTimeout(function(){if(document.activeElement!==pk.el)pkClose()},120)}});
document.addEventListener('keydown',function(e){
  var el=e.target;if(!el.dataset||!el.dataset.pick)return;
  if(!pk.open){if(e.key==='ArrowDown'){pkOpen(el,false);e.preventDefault()}return}
  if(e.key==='ArrowDown'){pkSetAct(pk.act+1,true);e.preventDefault()}
  else if(e.key==='ArrowUp'){pkSetAct(pk.act-1,true);e.preventDefault()}
  else if(e.key==='Enter'){if(pk.items.length){pkChoose(pk.act);e.preventDefault()}}
  else if(e.key==='Escape'){pkClose();e.stopPropagation()}
  else if(e.key==='Tab'){if(pk.items.length&&pk.q.trim())pkChoose(pk.act);else pkClose()}
});
$('#pk').addEventListener('mousedown',function(e){e.preventDefault()});
$('#pk').addEventListener('click',function(e){var o=e.target.closest('.o');if(o)pkChoose(+o.dataset.i)});
window.addEventListener('scroll',pkPlace,true);
window.addEventListener('resize',pkPlace);

function renderSales(){renderCus();renderOrders();renderInvs();renderOdEd();renderIvEd();if(IS.view&&!$('#iv-view').hidden)renderInvView()}

