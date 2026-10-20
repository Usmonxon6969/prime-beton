/* row action menu */
function menuHtml(no){
  if(MENUS[menuKind])return MENUS[menuKind].html(no);
  if(menuKind==='gn')return '<button type="button" role="menuitem" data-act="spec">'+ICO.spec+t('nav_specs')+'</button><button type="button" role="menuitem" data-act="edit">'+ICO.edit+t('m_edit')+'</button><button type="button" role="menuitem" data-act="del" class="del">'+ICO.del+t('m_del')+'</button>';
  if(menuKind==='mt')return '<button type="button" role="menuitem" data-act="edit">'+ICO.edit+t('m_edit')+'</button><button type="button" role="menuitem" data-act="del" class="del">'+ICO.del+t('m_del')+'</button>';
  if(menuKind==='gm')return '<button type="button" role="menuitem" data-act="mats">'+ICO.spec+t('p_mats')+'</button>';
  var d=findDoc(no),dead=d&&d.status==='deleted';
  return (dead?'':'<button type="button" role="menuitem" data-act="edit">'+ICO.edit+t('m_edit')+'</button>')+
    '<button type="button" role="menuitem" data-act="copy">'+ICO.copy+t('m_copy')+'</button>'+
    (dead?'<button type="button" role="menuitem" data-act="restore">'+ICO.restore+t('m_restore')+'</button>':'<button type="button" role="menuitem" data-act="del" class="del">'+ICO.del+t('m_del')+'</button>');
}
function confirmHtml(no){return '<div class="mconf"><p>'+(MENUS[menuKind]?MENUS[menuKind].q(no):menuKind==='gn'?t('pd_del_q'):menuKind==='mt'?t('mt_del_q'):t('del_q').replace('%s',no))+'</p><div class="mrow"><button type="button" data-act="cancel">'+t('m_cancel')+'</button><button type="button" class="danger" data-act="confirmdel">'+t('m_del')+'</button></div></div>'}
function placeMenu(){
  var m=$('#pmenu');if(!menuBtn)return;
  var r=menuBtn.getBoundingClientRect(),w=m.offsetWidth,h=m.offsetHeight;
  var left=Math.max(8,Math.min(window.innerWidth-w-8,r.right-w)),top=r.bottom+4;
  if(top+h>window.innerHeight-8)top=Math.max(8,r.top-h-4);
  m.style.left=left+'px';m.style.top=top+'px';
}
function openMenu(btn){
  closeMenu();menuBtn=btn;menuNo=btn.dataset.no;menuKind=btn.dataset.kind||'doc';
  var m=$('#pmenu');m.setAttribute('role','menu');m.innerHTML=menuHtml(menuNo);
  if(document.body.getAttribute('data-ro')==='1'){m.querySelectorAll('[data-act]').forEach(function(x){if(/^(edit|del|copy|restore|inv|confirmdel)$/.test(x.dataset.act))x.parentNode.removeChild(x)});if(!m.querySelector('button')){menuBtn=null;return}}
  m.hidden=false;
  btn.setAttribute('aria-expanded','true');placeMenu();m.querySelector('button').focus();
}
function closeMenu(restore){
  var m=$('#pmenu');if(!m)return;
  m.hidden=true;
  if(menuBtn){menuBtn.setAttribute('aria-expanded','false');if(restore)menuBtn.focus()}
  menuBtn=null;menuNo=null;
}
$('#plog').addEventListener('click',function(e){var b=e.target.closest('.kebab');if(!b)return;if(menuBtn===b)closeMenu(true);else openMenu(b)});
$('#pmenu').addEventListener('click',function(e){
  var b=e.target.closest('[data-act]');if(!b)return;
  e.stopPropagation();
  var act=b.dataset.act,no=menuNo,m=$('#pmenu');
  if(MENUS[menuKind]){
    var M=MENUS[menuKind];
    if(act==='cancel'){closeMenu(true)}
    else if(act==='del'){m.setAttribute('role','dialog');m.innerHTML=confirmHtml(no);placeMenu();m.querySelector('[data-act="cancel"]').focus()}
    else{closeMenu();M.act(act,no)}
    return;
  }
  if(menuKind!=='doc'){
    var kind=menuKind;
    if(act==='cancel'){closeMenu(true)}
    else if(act==='del'){m.setAttribute('role','dialog');m.innerHTML=confirmHtml(no);placeMenu();m.querySelector('[data-act="cancel"]').focus()}
    else if(act==='spec'){closeMenu();specSel=+no;loadDraft();spmsg=null;location.hash='specifications'}
    else if(act==='mats'){closeMenu();location.hash='materials'}
    else if(act==='edit'){closeMenu();if(kind==='gn')openGnForm(+no);else openMatForm(+no)}
    else if(act==='confirmdel'){closeMenu();if(kind==='gn')deleteGn(+no);else deleteMat(+no)}
    return;
  }
  if(act==='edit'){closeMenu();openEdit(no)}
  else if(act==='copy'){closeMenu();copyDoc(no)}
  else if(act==='del'){m.setAttribute('role','dialog');m.innerHTML=confirmHtml(no);placeMenu();m.querySelector('[data-act="cancel"]').focus()}
  else if(act==='cancel'){closeMenu(true)}
  else if(act==='restore'){closeMenu();var d1=findDoc(no);if(d1&&d1.status==='deleted')srv(api('POST','/production/'+d1.id+'/restore'),function(){pdone={key:'res_msg',no:no};renderLog();renderMsg()},function(e){pdone=apiMsg(e);renderLog();renderMsg()})}
  else if(act==='confirmdel'){closeMenu();var d=findDoc(no);if(d&&d.status==='posted')srv(api('DELETE','/production/'+d.id),function(){pdone={key:'del_msg',no:no};renderLog();renderMsg()},function(e){pdone=apiMsg(e);renderLog();renderMsg()})}
});
$('#pmenu').addEventListener('keydown',function(e){
  if(e.key!=='ArrowDown'&&e.key!=='ArrowUp')return;
  var bs=[].slice.call(this.querySelectorAll('button')),i=bs.indexOf(document.activeElement);
  i=e.key==='ArrowDown'?(i+1)%bs.length:(i-1+bs.length)%bs.length;bs[i].focus();e.preventDefault();
});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!$('#pmenu').hidden)closeMenu(true)});
document.addEventListener('click',function(e){if(!$('#pmenu').hidden&&!e.target.closest('#pmenu')&&!e.target.closest('.kebab'))closeMenu()});
window.addEventListener('scroll',function(){if(!$('#pmenu').hidden)closeMenu()},true);
window.addEventListener('resize',function(){if(!$('#pmenu').hidden)closeMenu()});
/* document form */
$('#prows').addEventListener('input',function(e){
  var i=e.target.dataset.i;if(i===undefined)return;
  if(e.target.dataset.k==='p'){rows[+i].p=pidx(e.target.value);rows[+i].t=e.target.value;touch()}
  else if(e.target.type==='number'){var v=parseInt(e.target.value,10);rows[+i][e.target.dataset.k==='s'?'s':'q']=v>0?v:0;touch()}
});
$('#prows').addEventListener('click',function(e){var b=e.target.closest('[data-rm]');if(b&&rows.length>1){rows.splice(+b.dataset.rm,1);renderRows();touch()}});
$('#pcrew').addEventListener('change',function(e){var w=+e.target.dataset.w;if(!w)return;var k=pcrew.indexOf(w);if(e.target.checked&&k<0)pcrew.push(w);else if(!e.target.checked&&k>-1)pcrew.splice(k,1);touch()});
$('#padd').addEventListener('click',function(){rows.push({p:-1,q:0,s:0,t:''});renderRows();touch();var l=$('#pr'+(rows.length-1));if(l)l.focus()});
$('#psite').addEventListener('change',function(){psite=+this.value;renderKv();touch()});
$('#pfill').addEventListener('click',fillMats);
$('#ppost').addEventListener('click',postDoc);

