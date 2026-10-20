/* toasts, activity and alerts */
var ACT=[],unseen=0,userAct=0,muteUntil=0;
function toast(txt,bad,quiet){
  var box=$('#toasts'),el=document.createElement('div');
  el.className='toast'+(bad?' bad':'');el.setAttribute('role',bad?'alert':'status');
  el.innerHTML='<span class="ti">'+svgi(bad?NI.warn:NI.ok,20)+'</span><span style="flex:1;min-width:0;overflow-wrap:anywhere"></span><button type="button" aria-label="OK">×</button><i style="animation-duration:'+(bad?7000:4500)+'ms"></i>';
  el.children[1].textContent=txt;
  var kill=function(){if(el.parentNode){el.classList.add('out');setTimeout(function(){if(el.parentNode)el.parentNode.removeChild(el)},230)}};
  el.children[2].addEventListener('click',kill);
  box.appendChild(el);while(box.children.length>4)box.removeChild(box.firstChild);
  setTimeout(kill,bad?7000:4500);
  if(!quiet){ACT.unshift({t:new Date(),x:txt,bad:!!bad});if(ACT.length>40)ACT.pop();unseen++;bellUpdate()}
}
var lastMsg=new WeakMap(),pendMsg=[];
function watchMsgs(){
  var mo=new MutationObserver(function(list){
    list.forEach(function(m){var n=m.target.nodeType===3?m.target.parentElement:m.target;if(!n||!n.closest)return;var el=n.closest('.msg[role="status"]');if(el&&pendMsg.indexOf(el)<0)pendMsg.push(el)});
    if(!pendMsg.length)return;
    setTimeout(function(){
      var els=pendMsg.splice(0);
      els.forEach(function(el){
        var x=el.textContent.trim();
        if(!x){lastMsg.delete(el);return}
        if(Date.now()>muteUntil&&(x!==lastMsg.get(el)||Date.now()-userAct<500)){toast(x,/(^| )bad( |$)/.test(el.className))}
        lastMsg.set(el,x);
      });
      busTick();
    },0);
  });
  mo.observe(document.body,{childList:true,characterData:true,subtree:true});
}
document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('button,a.btn');if(b&&!b.closest('.side,.top,#notif,#cmdk,#toasts'))userAct=Date.now()},true);
document.addEventListener('keydown',function(e){if(e.key==='Enter')userAct=Date.now()},true);
function today0(){var d=new Date(Math.max(base.getTime(),Date.now()));d.setHours(0,0,0,0);return d}
function itemGone(x){return x.fg?PGONE[PRODUCTS.indexOf(x.n)]:(MATS[x.m]&&MATS[x.m].deleted)}
function lowItems(){return ITEMS.filter(function(x){return !itemGone(x)&&x.min>0&&x.tot<x.min})}
function overdueOrders(){var d=today0();return ORD.filter(function(o){return o.status!=='deleted'&&o.due&&o.due<d&&ordState(o)!=='shipped'})}
function totalDebts(){var r=0,p=0;CUS.forEach(function(c,i){if(!c.gone){var d=custDebt(i);if(d>0)r+=d}});SUP.forEach(function(c,i){if(!c.gone){var d=supDebt(i);if(d>0)p+=d}});return {r:r,p:p}}
function alerts(){
  var a=[],lo=lowItems(),od=overdueOrders(),db=totalDebts();
  if(lo.length&&lvl('wh')>0)a.push({k:'bad',ic:NI.warn,x:tf('al_stock',{n:lo.length}),s:lo.slice(0,3).map(iname).join(', ')+(lo.length>3?'…':''),h:'#warehouse'});
  if(od.length&&lvl('ord')>0)a.push({k:'warn',ic:NI.ord,x:tf('al_over',{n:od.length}),s:od.slice(0,3).map(function(o){return o.no}).join(', '),h:'#orders'});
  if(db.r>0&&lvl('cus')>0)a.push({k:'warn',ic:NI.money,x:tf('al_debt',{m:money(db.r)}),s:'',h:'#customers'});
  if(db.p>0&&lvl('sup')>0)a.push({k:'warn',ic:NI.money,x:tf('al_pay',{m:money(db.p)}),s:'',h:'#suppliers'});
  return a;
}
function bellUpdate(){
  var b=$('#bellb');if(!b)return;
  var n=ME?alerts().length+unseen:0;
  b.hidden=!n;b.textContent=n>9?'9+':n;
  if(!$('#notif').hidden)renderNotif();
}
function renderNotif(){
  var al=alerts(),h='<h3>'+t('nt_h')+'</h3><div class="sub">'+t('nt_alerts')+'</div>';
  h+=al.length?al.map(function(x){return '<a class="it '+x.k+'" href="'+x.h+'"><span class="ic">'+svgi(x.ic)+'</span><span><span>'+esc(x.x)+'</span>'+(x.s?'<small>'+esc(x.s)+'</small>':'')+'</span></a>'}).join(''):'<div class="emp">'+t('nt_none')+'</div>';
  h+='<div class="sub" style="padding-top:12px;border-top:1px solid var(--line)">'+t('nt_act')+'</div>';
  h+=ACT.length?ACT.slice(0,12).map(function(x){return '<div class="it '+(x.bad?'bad':'good')+'"><span class="ic">'+svgi(x.bad?NI.warn:NI.ok)+'</span><span><span>'+esc(x.x)+'</span><small>'+pad2(x.t.getHours())+':'+pad2(x.t.getMinutes())+'</small></span></div>'}).join('')+'<div class="foot"><button type="button" class="link" id="actclr">'+t('nt_clear')+'</button></div>':'<div class="emp">'+t('nt_noact')+'</div>';
  $('#notif').innerHTML=h;
}
function toggleNotif(open){
  var p=$('#notif'),on=open===undefined?p.hidden:open;
  p.hidden=!on;$('#bell').setAttribute('aria-expanded',String(on));
  if(on){unseen=0;renderNotif();bellUpdate()}
}
$('#bell').addEventListener('click',function(e){e.stopPropagation();toggleNotif()});
$('#notif').addEventListener('click',function(e){e.stopPropagation();if(e.target.closest('#actclr')){ACT=[];renderNotif();return}if(e.target.closest('a'))toggleNotif(false)});
document.addEventListener('click',function(e){if(!$('#notif').hidden&&!e.target.closest('#notif'))toggleNotif(false)});

