/* theme */
function effTheme(){var a=document.documentElement.getAttribute('data-theme');return a||(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}
function themeIcon(){$('#themebtn').innerHTML=svgi(NI.palette||NI.moon);var l=lang==='ru'?'Тема':lang==='uz'?'Mavzu':'Theme';$('#themebtn').setAttribute('aria-label',l);$('#themebtn').title=l}
$('#themebtn').addEventListener('click',function(){var n=effTheme()==='dark'?'light':'dark';document.documentElement.setAttribute('data-theme',n);try{localStorage.setItem('daybook-theme',n)}catch(e){}themeIcon();if(location.hash==='#dashboard'){drawDaily();renderBiz()}});
try{var th=localStorage.getItem('daybook-theme');if(/^(dark|light|okean|orman|binafsha)$/.test(th))document.documentElement.setAttribute('data-theme',th)}catch(e){}

/* shell */
$('#hamb').addEventListener('click',function(){var o=!document.body.classList.contains('nav-open');document.body.classList.toggle('nav-open',o);this.setAttribute('aria-expanded',String(o));$('#scrim').hidden=!o});
$('#scrim').addEventListener('click',function(){document.body.classList.remove('nav-open');$('#hamb').setAttribute('aria-expanded','false');this.hidden=true});
$('#side').addEventListener('click',function(e){if(e.target.closest('a')){document.body.classList.remove('nav-open');$('#scrim').hidden=true;$('#hamb').setAttribute('aria-expanded','false')}});
function relLang(){
  muteUntil=Date.now()+400;
  buildSide();renderDemo();themeIcon();
  $('#cmdtxt').textContent=t('srch');$('#cmdbtn').setAttribute('aria-label',t('srch'));
  $('#bell').setAttribute('aria-label',t('nt_h'));$('#hamb').setAttribute('aria-label',t('menu'));
  $('#rochip').textContent=t('ro_note');
  var hm=$('#nav-home');if(hm)hm.setAttribute('href','#'+(ME?homeHash():'overview'));
  if(!$('#notif').hidden)renderNotif();
  bellUpdate();if(location.hash==='#dashboard')renderBiz();
}
function route(){
  var h=(location.hash||'').replace('#',''),sec=secOf(h);
  if(!ME&&sec){location.hash='login';return}
  if(ME&&(h===''||h==='login')){location.hash=homeHash();return}
  if(ME&&sec){
    var l=lvl(sec);
    if(l<1){toast(t('noaccess'),true,true);location.hash=homeHash();return}
    if(l<2&&/-(new|edit)$/.test(h)){location.hash=SECHASH[sec];return}
  }
  Tabs.pre(h);
  routeCore();
  Tabs.post(h);Tabs.qpInit();
  var app=!!ME&&h!=='overview'&&h!=='login';
  document.body.classList.toggle('app',app);
  if(!app){document.body.classList.remove('nav-open');$('#scrim').hidden=true}
  if(sec&&sec!=='dash'&&lvl(sec)===1)document.body.setAttribute('data-ro','1');else document.body.removeAttribute('data-ro');
  var hm=$('#nav-home');if(hm)hm.setAttribute('href','#'+(ME?homeHash():'overview'));
  var pd=$('#pdsec');if(pd)pd.hidden=!(lvl('prod')>0);
  var v=document.querySelector('main > div:not([hidden])');
  if(v){v.classList.remove('view-in','rows-in');void v.offsetWidth;v.classList.add('view-in','rows-in');setTimeout(function(){v.classList.remove('view-in','rows-in')},900)}
  if(h==='dashboard')renderBiz();
  bellUpdate();
}


document.addEventListener('click',function(e){if(e.target.closest&&e.target.closest('#themebtn2'))$('#themebtn').click()});

document.addEventListener('click',function(e){if(e.target.closest&&e.target.closest('#signout'))signOut()});
