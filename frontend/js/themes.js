/* Colour themes: the header theme button opens a picker. 'light' = Prime, 'dark' = Tungi (see theme.css); the rest are in themes.css. */
var THEMES=[
 {id:'light',n:['Prime','Prime','Prime'],c:['#f1f2f3','#ffffff','#0f1012']},
 {id:'okean',n:['Ocean','Океан','Okean'],c:['#eaf2f9','#ffffff','#0b5cad']},
 {id:'orman',n:['Forest','Лес','O‘rmon'],c:['#e9f3ec','#ffffff','#1b6b42']},
 {id:'binafsha',n:['Violet','Фиалка','Binafsha'],c:['#f0ecf9','#ffffff','#5b32c4']},
 {id:'dark',n:['Night','Ночь','Tungi'],c:['#0e0f11','#17191c','#f2f3f4']}
];
(function(){
  var ttl=['Theme','Тема','Mavzu'];
  function li(){return lang==='ru'?1:lang==='uz'?2:0}
  function cur(){var a=document.documentElement.getAttribute('data-theme');return a||(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}
  function close(){var p=document.getElementById('thpick');if(p)p.remove()}
  function apply(id){
    document.documentElement.setAttribute('data-theme',id);
    try{localStorage.setItem('daybook-theme',id)}catch(e){}
    if(typeof themeIcon==='function')themeIcon();
    if(location.hash==='#dashboard'){try{drawDaily();renderBiz()}catch(e){}}
  }
  function open(anchor){
    close();
    var p=document.createElement('div');p.id='thpick';p.className='thpick';p.setAttribute('role','dialog');p.setAttribute('aria-label',ttl[li()]);
    var h='<h3>'+ttl[li()]+'</h3><div class="grid">',c=cur();
    THEMES.forEach(function(x){h+='<button type="button" data-th="'+x.id+'" aria-pressed="'+(x.id===c)+'"><span class="sw"><i style="background:'+x.c[0]+'"></i><i style="background:'+x.c[1]+'"></i><i style="background:'+x.c[2]+'"></i></span>'+x.n[li()]+'</button>'});
    p.innerHTML=h+'</div>';document.body.appendChild(p);
    var r=anchor.getBoundingClientRect(),w=p.offsetWidth;
    p.style.top=Math.min(r.bottom+6,innerHeight-p.offsetHeight-8)+'px';
    p.style.left=Math.max(16,Math.min(r.right-w,innerWidth-w-16))+'px';
    var b=p.querySelector('[aria-pressed="true"]')||p.querySelector('button');b.focus();
  }
  document.addEventListener('click',function(e){
    var tb=e.target.closest&&e.target.closest('#themebtn,#themebtn2');
    if(tb){e.stopPropagation();e.preventDefault();if(document.getElementById('thpick'))close();else open(tb);return}
    var o=e.target.closest&&e.target.closest('#thpick [data-th]');
    if(o){apply(o.getAttribute('data-th'));close();return}
    if(!(e.target.closest&&e.target.closest('#thpick')))close();
  },true);
  document.addEventListener('keydown',function(e){if(e.key==='Escape')close()});
  window.addEventListener('hashchange',close);
})();
