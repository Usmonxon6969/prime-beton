/* language + routing */
function applyLang(){
  document.documentElement.lang=lang;
  document.querySelectorAll('[data-i18n]').forEach(function(el){el.textContent=t(el.dataset.i18n)});
  document.querySelectorAll('[data-lang]').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.lang===lang))});
  renderSlips();renderDash();renderProd();renderWh();renderItems();renderSpecs();renderMatForm();renderMatPage();renderMatMsg();renderSales();renderPur();renderSet();renderFin();renderFinEd();renderAkt();updateTg();relLang();
}
function routeCore(){
  var h=(location.hash||'').replace('#','');
  var map={dashboard:'dash',login:'login',production:'prod','production-new':'prod','production-edit':'prod',warehouse:'wh',products:'items',specifications:'specs',materials:'mats',customers:'cus','customer-akt':'cus','supplier-akt':'cus',suppliers:'pur',settings:'set',receipts:'pur','receipt-new':'pur','receipt-edit':'pur',orders:'ord','order-new':'ord','order-edit':'ord',invoices:'inv','invoice-new':'inv','invoice-edit':'inv','invoice-view':'inv',bank:'fin','bank-new':'fin','bank-edit':'fin',cash:'fin','cash-new':'fin','cash-edit':'fin'},v0=map[h]||'home';
  ['home','dash','login','prod','wh','items','specs','mats','cus','ord','inv','pur','set','fin'].forEach(function(v){$('#view-'+v).hidden=(v!==v0)});
  document.querySelectorAll('.nav a,.side a').forEach(function(l){l.removeAttribute('aria-current')});
  var navId={home:'#nav-home',dash:'#nav-dash',prod:'#nav-prod',wh:'#nav-wh',items:'#nav-items',specs:'#nav-specs',mats:'#nav-mats',cus:'#nav-cus',ord:'#nav-ord',inv:'#nav-inv',pur:'#nav-'+(/^receipt/.test(h)?'rec':'sup'),set:'#nav-set',fin:'#nav-'+(/^cash/.test(h)?'cash':'bank')}[v0];
  if(h==='supplier-akt')navId='#nav-sup';
  if(navId)$(navId).setAttribute('aria-current','page');
  closeMenu();
  if(v0==='prod'){var isNew=h==='production-new',isEdit=h==='production-edit';if(isEdit&&!editNo){location.hash='production';return}
    $('#prod-list').hidden=isNew||isEdit;$('#prod-edit').hidden=!(isNew||isEdit);if(isNew&&prevH!=='production-new')newDoc()}
  if(v0==='fin'){fmode=/^cash/.test(h)?'cash':'bank';var fnw=/-new$/.test(h),fed=/-edit$/.test(h);if(fed&&!FS.no){location.hash=fmode;return}
    $('#fin-list').hidden=fnw||fed;$('#fin-edit').hidden=!(fnw||fed);
    if(fnw&&!/-new$/.test(prevH))newFin();else if(!fnw&&!fed)renderFin()}
  if(v0==='cus'){var sk=h==='supplier-akt',ak=h==='customer-akt'||sk;if(ak&&(AK.cus<0||AK.sup!==sk)){location.hash=sk?'suppliers':'customers';return}$('#cu-list').hidden=ak;$('#cu-akt').hidden=!ak;if(ak)renderAkt();else renderCus()}
  if(v0==='pur'){var rn=h==='receipt-new',rd=h==='receipt-edit';if(rd&&!RS.no){location.hash='receipts';return}
    $('#su-list').hidden=/^receipt/.test(h);$('#rc-list').hidden=h!=='receipts';$('#rc-edit').hidden=!(rn||rd);
    if(rn&&prevH!=='receipt-new')newRec();else if(h==='receipts')renderRecs();else if(h==='suppliers')renderSup()}
  if(v0==='ord'){var on=h==='order-new',oe=h==='order-edit';if(oe&&!OS.no){location.hash='orders';return}
    $('#od-list').hidden=on||oe;$('#od-edit').hidden=!(on||oe);if(on&&prevH!=='order-new')newOrder();else if(!on&&!oe)renderOrders()}
  if(v0==='inv'){var inn=h==='invoice-new',ie=h==='invoice-edit',iw=h==='invoice-view';if((ie&&!IS.no)||(iw&&!findI(IS.view))){location.hash='invoices';return}
    $('#iv-list').hidden=inn||ie||iw;$('#iv-edit').hidden=!(inn||ie);$('#iv-view').hidden=!iw;
    if(inn&&prevH!=='invoice-new')newInv();else if(iw)renderInvView();else if(!inn&&!ie)renderInvs()}
  if(v0==='set')renderSet();
  if(v0==='specs'){renderSpecs();var cur=$('#splist .spitem[aria-current]');if(cur)cur.scrollIntoView({block:'nearest'})}
  if(v0==='mats'){renderMatPage()}
  if(v0==='prod'&&mats){mats=calcMats(rows);renderMats()}
  prevH=h;
  if(v0==='dash'){window.scrollTo(0,0);drawDaily()}
  else if(v0!=='home'){window.scrollTo(0,0)}
  else if(h==='how'){var el=document.getElementById('how');if(el)el.scrollIntoView()}
  else window.scrollTo(0,0);
}
document.querySelectorAll('[data-lang]').forEach(function(b){b.addEventListener('click',function(){lang=b.dataset.lang;try{localStorage.setItem('daybook-lang',lang)}catch(e){}applyLang()})});
document.querySelectorAll('#periods button').forEach(function(b){b.addEventListener('click',function(){period=+b.dataset.p;renderDash()})});
document.querySelectorAll('#filters button').forEach(function(b){b.addEventListener('click',function(){flt=b.dataset.f;renderDash()})});
function updateTg(){var p=$('#pw'),g=$('#tg');if(!p||!g)return;var hid=p.type==='password';g.textContent=t(hid?'show':'hide');g.setAttribute('aria-pressed',String(!hid))}
function setErr(eid,iid,key){var e=$(eid),i=$(iid);if(key){e.setAttribute('data-i18n',key);e.textContent=t(key);i.setAttribute('aria-invalid','true')}else{e.removeAttribute('data-i18n');e.textContent='';i.removeAttribute('aria-invalid')}}
$('#tg').addEventListener('click',function(){var p=$('#pw');p.type=p.type==='password'?'text':'password';updateTg()});
$('#fg').addEventListener('click',function(){$('#fgmsg').hidden=false});
$('#loginForm').addEventListener('submit',function(ev){
  ev.preventDefault();
  var u=$('#u').value.trim(),p=$('#pw').value;
  setErr('#eu','#u',u?'':'err_user');setErr('#ep','#pw',p?'':'err_pass');
  if(u&&p){doLogin(u,p,$('#rm').checked)}
  else{(u?$('#pw'):$('#u')).focus()}
});
window.addEventListener('hashchange',route);
var rt;window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(drawDaily,80)});
