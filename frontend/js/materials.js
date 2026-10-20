/* materials */
var mform=null,mmsg=null,mdel=null;
function esc(x){return String(x).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;')}
function matUsage(j){var n=0;for(var pi=0;pi<NORMS.length;pi++){if((NORMS[pi][j]||0)>0)n++}return n}
function renderMatMsg(){
  var e=$('#mtmsg');
  if(!mmsg){e.className='msg';e.textContent='';return}
  e.className='msg '+(mmsg.err?'bad':'ok');
  e.textContent=t(mmsg.key).replace('%m',mmsg.m||'').replace('%n',mmsg.n||'');
}
function renderMatForm(){
  var el=$('#mtform');
  if(!mform){el.hidden=true;el.innerHTML='';return}
  el.hidden=false;
  el.innerHTML='<h2>'+t(mform.mode==='new'?'mt_new_h':'mt_edit_h')+'</h2>'+
    '<div class="fgrid"><div class="field"><label for="mtname">'+t('mt_name')+'</label><input id="mtname" data-k="name" type="text" autocomplete="off" value="'+esc(mform.name)+'"></div>'+
    '<div class="field"><label for="mtu">'+t('st_unit')+'</label><select id="mtu" data-k="u">'+unitOpts(mform.u)+'</select></div>'+
    '<div class="field"><label for="mtmin">'+t('mt_min')+'</label><input id="mtmin" data-k="min" type="number" min="0" step="any" inputmode="decimal" value="'+(mform.min>0?mform.min:'')+'"></div></div>'+
    '<div class="pbtns"><button type="button" class="btn primary sm" id="mtsave">'+t('sp_save')+'</button><button type="button" class="btn ghost sm" id="mtcancel">'+t('m_cancel')+'</button></div>'+
    '<p class="msg bad" id="mtferr" role="alert">'+(mform.err?t(mform.err).replace('%m',mform.errm||''):'')+'</p>';
}
function renderMatPage(){
  $('#mtq').placeholder=t('p_search');$('#mtq').setAttribute('aria-label',t('p_search'));
  var q=($('#mtq').value||'').trim().toLowerCase();
  var list=activeMats().filter(function(j){return !q||mname(j).toLowerCase().indexOf(q)>-1});
  var head='<thead><tr><th>'+t('mt_name')+'</th><th class="num">'+t('c_min')+'</th><th class="num">'+t('c_stock')+'</th><th>'+t('c_status')+'</th><th class="num">'+t('mt_used')+'</th><th><span class="vh">'+t('m_actions')+'</span></th></tr></thead>';
  var body=list.length?list.map(function(j){
    var it=MAT_BY[j];
    var acts=kebabHtml('mt',j,mname(j));
    return '<tr><td>'+esc(mname(j))+'</td><td class="num">'+(it.min>0?fmt(it.min):'–')+' '+uname(iu(it))+'</td><td class="num"><b>'+fmt(it.tot)+'</b> '+uname(iu(it))+'</td><td>'+pill(it.s,'stk_'+it.s)+'</td><td class="num">'+matUsage(j)+'</td><td class="act">'+acts+'</td></tr>';
  }).join(''):'<tr><td class="empty" colspan="6">'+t('it_empty')+'</td></tr>';
  $('#mttbl').innerHTML=head+'<tbody>'+body+'</tbody>';
}
function refreshAfterMat(){renderMatForm();renderMatPage();renderMatMsg();refreshStock();renderSpecs()}
function openMatForm(j){
  mmsg=null;mdel=null;
  if(j===undefined){mform={mode:'new',j:-1,name:'',min:0,u:Math.max(0,UNITS.findIndex(function(x){return x.n.uz==='kg'})),err:null}}
  else{var it=MAT_BY[j];mform={mode:'edit',j:j,name:mname(j),min:it.min,u:iu(it),err:null}}
  renderMatForm();renderMatPage();renderMatMsg();
  var f=$('#mtname');if(f)f.focus();
}
function saveMat(){
  var nm=mform.name.trim();
  if(!nm){mform.err='mt_err_name';renderMatForm();return}
  var dup=activeMats().some(function(j){return j!==mform.j&&mname(j).toLowerCase()===nm.toLowerCase()});
  if(dup){mform.err='mt_err_dup';renderMatForm();return}
  var min=mform.min>0?mform.min:0,uid=UNID[mform.u];
  if(uid==null){mform.err='st_err_name';renderMatForm();return}
  var call=mform.mode==='new'
    ?api('POST','/items',{kind:'material',name_uz:nm,name_ru:nm,name_en:nm,unit_id:uid,min_stock:min})
    :api('PATCH','/items/'+MATID[mform.j],{name_uz:nm,name_ru:nm,name_en:nm,unit_id:uid,min_stock:min});
  srv(call,function(){
    mmsg={key:'mt_saved',m:nm};mform=null;
    refreshAfterMat();
  },function(e){mform.err='api_raw';mform.errm=apiErr(e);renderMatForm()});
}
function deleteMat(j){
  mdel=null;var nm=mname(j);
  srv(api('DELETE','/items/'+MATID[j]),function(){
    mmsg={key:'mt_deleted',m:nm};refreshAfterMat();
  },function(e){mmsg={key:'api_raw',m:apiErr(e),err:true};renderMatPage();renderMatMsg()});
}
$('#mtq').addEventListener('input',renderMatPage);
$('#mtnew').addEventListener('click',function(){openMatForm()});
$('#mtform').addEventListener('input',function(e){
  if(!mform)return;var k=e.target.dataset.k;if(!k)return;
  if(k==='u'){mform.u=+e.target.value;return}
  if(k==='name')mform.name=e.target.value;
  else if(k==='min'){var v=parseFloat(e.target.value);mform.min=v>0?v:0}
});
$('#mtform').addEventListener('click',function(e){
  var b=e.target.closest('button');if(!b)return;
  if(b.id==='mtsave')saveMat();
  else if(b.id==='mtcancel'){mform=null;renderMatForm()}
});

