/* Titles for the phone card view: each cell gets its column title (see css/cards.css). */
(function(){
'use strict';
function label(tbl){
  if(tbl.classList.contains('nocards'))return;
  var heads=[];
  var hr=tbl.querySelector('thead tr:last-child');
  if(!hr)return;
  hr.querySelectorAll('th').forEach(function(th){
    var n=th.colSpan||1,txt=(th.textContent||'').trim();
    if(th.querySelector('.vh'))txt='';
    for(var i=0;i<n;i++)heads.push(txt);
  });
  tbl.classList.add('cardy');
  tbl.querySelectorAll('tbody tr, tfoot tr').forEach(function(tr){
    var c=0;
    Array.prototype.forEach.call(tr.children,function(td){
      var span=td.colSpan||1;
      if(span===1&&td.getAttribute('data-label')!==(heads[c]||''))td.setAttribute('data-label',heads[c]||'');
      c+=span;
    });
  });
}
var timer=null;
function run(){
  var m=document.querySelector('main');if(!m)return;
  m.querySelectorAll('table').forEach(label);
}
function soon(){clearTimeout(timer);timer=setTimeout(run,60)}
function start(){
  var m=document.querySelector('main');if(!m)return;
  new MutationObserver(soon).observe(m,{childList:true,subtree:true});
  run();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
