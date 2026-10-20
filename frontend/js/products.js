/* product management */
var gform=null,gmsg=null,gdel=null;
function kebabHtml(kind,no,name){return '<div class="racts"><button type="button" class="kebab" data-kind="'+kind+'" data-no="'+no+'" aria-haspopup="menu" aria-expanded="false" aria-label="'+t('m_actions')+' '+esc(name)+'">'+ICO.dots+'</button></div>'}
function gnActs(x){var i=PRODUCTS.indexOf(x.n);return kebabHtml('gn',i,x.n)}
function renderGnMsg(){
  var e=$('#gnmsg');
  if(!gmsg){e.className='msg';e.textContent='';return}
  e.className='msg '+(gmsg.err?'bad':'ok');
  e.textContent=t(gmsg.key).replace('%m',gmsg.m||'');
}
function renderGnForm(){
  var el=$('#gnform');
  if(!gform){el.hidden=true;el.innerHTML='';return}
  el.hidden=false;
  el.innerHTML='<h2>'+t(gform.mode==='new'?'pd_new_h':'pd_edit_h')+'</h2>'+
    '<div class="fgrid"><div class="field"><label for="gnname">'+t('pd_name')+'</label><input id="gnname" data-k="name" type="text" autocomplete="off" spellcheck="false" value="'+esc(gform.name)+'"></div>'+
    '<div class="field"><label for="gnu">'+t('st_unit')+'</label><select id="gnu" data-k="u">'+unitOpts(gform.u)+'</select></div>'+
    '<div class="field"><label for="gnmin">'+t('pd_min')+'</label><input id="gnmin" data-k="min" type="number" min="0" step="1" inputmode="numeric" value="'+(gform.min>0?gform.min:'')+'"></div>'+
    (gform.mode==='new'?'<div class="field"><label for="gncopy">'+t('pd_copy')+'</label><input id="gncopy" data-k="copy" type="text" data-pick="prod" role="combobox" aria-autocomplete="list" autocomplete="off" spellcheck="false" placeholder="'+t('p_search')+'" value="'+esc(gform.copy)+'"></div>':'')+'</div>'+
    '<div class="pbtns"><button type="button" class="btn primary sm" id="gnsave">'+t('sp_save')+'</button><button type="button" class="btn ghost sm" id="gncancel">'+t('m_cancel')+'</button></div>'+
    '<p class="msg bad" id="gnferr" role="alert">'+(gform.err?t(gform.err).replace('%m',gform.errm||''):'')+'</p>';
}
function openGnForm(i){
  gmsg=null;gdel=null;
  if(i===undefined)gform={mode:'new',i:-1,name:'',min:0,copy:'',u:Math.max(0,UNITS.findIndex(function(x){return x.n.uz==='dona'})),err:null};
  else{var it=ITEM_BY[PRODUCTS[i]];gform={mode:'edit',i:i,name:PRODUCTS[i],min:it.min,copy:'',u:iu(it),err:null}}
  renderItems();
  var f=$('#gnname');if(f)f.focus();
}
function gnFail(e){gform.err='api_raw';gform.errm=apiErr(e);renderGnForm()}
function saveGn(){
  var nm=gform.name.trim().replace(/\./g,',').replace(/\s+/g,' ');
  if(!nm){gform.err='mt_err_name';renderGnForm();return}
  if(nm.indexOf('"')>-1||nm.indexOf('<')>-1){gform.err='pd_err_chars';renderGnForm();return}
  var ex=Math.max(pidx(nm),pidx(gform.name));
  if(ex>-1&&ex!==gform.i){gform.err='pd_err_dup';renderGnForm();return}
  var min=gform.min>0?gform.min:0,uid=UNID[gform.u];
  if(uid==null){gform.err='st_err_name';renderGnForm();return}
  var call;
  if(gform.mode==='new'){
    var spec=null;
    if(gform.copy.trim()){var ci=pidx(gform.copy);if(ci<0){gform.err='err_prod';renderGnForm();return}spec=norm(ci)}
    call=api('POST','/items',{kind:'product',name_uz:nm,name_ru:nm,name_en:nm,unit_id:uid,min_stock:min}).then(function(r){
      if(!spec)return r;
      return api('PUT','/specifications/'+r.id,{norms:MATID.map(function(id,j){return {material_id:id,qty:spec[j]||0}}).filter(function(x){return x.qty>0})}).then(function(){return r});
    });
  }else{
    call=api('PATCH','/items/'+PRID[gform.i],{name_uz:nm,name_ru:nm,name_en:nm,unit_id:uid,min_stock:min});
  }
  srv(call,function(){
    gmsg={key:'pd_saved',m:nm};gform=null;$('#itq').value='';
    renderItems();renderSpecs();
  },gnFail);
}
function deleteGn(i){
  gdel=null;var nm=PRODUCTS[i];
  srv(api('DELETE','/items/'+PRID[i]),function(){
    if(specSel>=PRODUCTS.length)specSel=0;loadDraft();
    gmsg={key:'pd_deleted',m:nm};renderItems();renderSpecs();
  },function(e){gmsg={key:'api_raw',m:apiErr(e),err:true};renderItems()});
}
$('#gnnew').addEventListener('click',function(){openGnForm()});
$('#gnform').addEventListener('input',function(e){
  if(!gform)return;var k=e.target.dataset.k;if(!k)return;
  if(k==='u'){gform.u=+e.target.value;return}
  if(k==='name'||k==='copy')gform[k]=e.target.value;
  else if(k==='min'){var v=parseFloat(e.target.value);gform.min=v>0?v:0}
});
$('#gnform').addEventListener('click',function(e){
  var b=e.target.closest('button');if(!b)return;
  if(b.id==='gnsave')saveGn();
  else if(b.id==='gncancel'){gform=null;renderGnForm()}
});
function kebabClick(e){var b=e.target.closest('.kebab');if(!b)return;if(menuBtn===b)closeMenu(true);else openMenu(b)}
$('#itbl').addEventListener('click',kebabClick);
$('#mttbl').addEventListener('click',kebabClick);

