/* command palette */
var CK={items:[],act:0,open:false,prev:null};
function ckLabel(x){return x}
function ckSource(){
  var a=[],i;
  NAV.forEach(function(g){g.i.forEach(function(x){if(lvl(x[0])>0)a.push({g:'cg_pages',x:t(x[2]),m:'',h:'#'+x[1],ic:NI[x[0]]})})});
  [['ord','order-new','cmd_ord'],['inv','invoice-new','cmd_inv'],['rec','receipt-new','cmd_rec'],['prod','production-new','cmd_prod']].forEach(function(c){if(lvl(c[0])>1)a.push({g:'cg_new',x:t(c[2]),m:'',h:'#'+c[1],ic:NI.plus})});
  if(lvl('cus')>0)CUS.forEach(function(c){if(!c.gone)a.push({g:'nav_cus',x:c.n,m:c.ph||'',h:'#customers',s:'#cuq',v:c.n,ic:NI.cus})});
  if(lvl('sup')>0)SUP.forEach(function(c){if(!c.gone)a.push({g:'nav_sup',x:c.n,m:c.ph||'',h:'#suppliers',s:'#suq',v:c.n,ic:NI.sup})});
  if(lvl('ord')>0)ORD.forEach(function(o){a.push({g:'nav_ord',x:o.no+' · '+CUS[o.cus].n,m:money(rsum(o.rows)),h:'#orders',s:'#odq',v:o.no,ic:NI.ord})});
  if(lvl('inv')>0)INV.forEach(function(o){a.push({g:'nav_inv',x:o.no+' · '+CUS[o.cus].n,m:money(rsum(o.rows)),h:'#invoices',s:'#ivq',v:o.no,ic:NI.inv})});
  if(lvl('rec')>0)REC.forEach(function(o){a.push({g:'nav_rec',x:o.no+' · '+SUP[o.sup].n,m:money(rsum(o.rows)),h:'#receipts',s:'#rcq',v:o.no,ic:NI.rec})});
  if(lvl('items')>0)PRODUCTS.forEach(function(n,j){if(!PGONE[j])a.push({g:'nav_items',x:n,m:'',h:'#products',s:'#itq',v:n,ic:NI.items})});
  if(lvl('mats')>0)activeMats().forEach(function(j){a.push({g:'p_mats',x:mname(j),m:'',h:'#materials',s:'#mtq',v:mname(j),ic:NI.mats})});
  return a;
}
function ckFilter(q){
  var src=ckSource(),toks=nrm(q).trim().split(/\s+/).filter(Boolean);
  if(!toks.length)return src.filter(function(x){return x.g==='cg_pages'||x.g==='cg_new'}).slice(0,16);
  var out=[];
  src.forEach(function(x){var h=nrm(x.x+' '+x.m);if(toks.every(function(k){return h.indexOf(k)>-1}))out.push(x)});
  return out.slice(0,40);
}
function ckRender(){
  var h='',g='';
  CK.items.forEach(function(x,i){
    if(x.g!==g){g=x.g;h+='<div class="cg">'+t(g)+'</div>'}
    h+='<div class="co" role="option" id="cko'+i+'" data-i="'+i+'" aria-selected="'+(i===CK.act)+'">'+svgi(x.ic,17)+'<span>'+esc(x.x)+'</span><span class="m">'+esc(x.m)+'</span></div>';
  });
  if(!CK.items.length)h='<div class="cg">'+t('srch_none')+'</div>';
  $('#cklist').innerHTML=h;
  var cur=$('#cko'+CK.act);if(cur){$('#ckin').setAttribute('aria-activedescendant',cur.id);if(cur.scrollIntoView)cur.scrollIntoView({block:'nearest'})}
}
function ckOpen(){
  if(!ME)return;
  CK.prev=document.activeElement;CK.open=true;$('#cmdk').hidden=false;
  $('#ckin').value='';$('#ckin').placeholder=t('srch_ph');$('#ckhint').textContent=t('srch_hint');
  CK.items=ckFilter('');CK.act=0;ckRender();$('#ckin').focus();
}
function ckClose(){if(!CK.open)return;CK.open=false;$('#cmdk').hidden=true;if(CK.prev&&CK.prev.focus)CK.prev.focus()}
function ckGo(i){
  var x=CK.items[i];if(!x)return;ckClose();
  var same=location.hash===x.h;location.hash=x.h;
  var apply=function(){if(x.s){var el=$(x.s);if(el){el.value=x.v;el.dispatchEvent(new Event('input',{bubbles:true}))}}};
  if(same){route();apply()}else setTimeout(apply,80);
}
$('#ckin').addEventListener('input',function(){CK.items=ckFilter(this.value);CK.act=0;ckRender()});
$('#ckin').addEventListener('keydown',function(e){
  if(e.key==='ArrowDown'){CK.act=Math.min(CK.items.length-1,CK.act+1);ckRender();e.preventDefault()}
  else if(e.key==='ArrowUp'){CK.act=Math.max(0,CK.act-1);ckRender();e.preventDefault()}
  else if(e.key==='Enter'){ckGo(CK.act);e.preventDefault()}
  else if(e.key==='Escape'){ckClose();e.stopPropagation()}
});
$('#cklist').addEventListener('click',function(e){var o=e.target.closest('.co');if(o)ckGo(+o.dataset.i)});
$('#cmdk').addEventListener('mousedown',function(e){if(e.target===this)ckClose()});
$('#cmdbtn').addEventListener('click',ckOpen);
document.addEventListener('keydown',function(e){
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();CK.open?ckClose():ckOpen()}
  else if(e.key==='Escape'){if(!$('#notif').hidden)toggleNotif(false);document.body.classList.remove('nav-open');$('#hamb').setAttribute('aria-expanded','false')}
});

