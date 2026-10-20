/* specifications */
var DEF_NORMS=[];
var specSel=0,draft=[],vis=[],spmsg=null;
/* the unit a material is really counted in (kg, m3, pcs ...), not always kg */
function matUnit(j){var it=MAT_BY[j];return it?uname(iu(it)):t('kg')}
function specTotal(){var by={},order=[];draft.forEach(function(v,j){if(v>0){var u=matUnit(j);if(!(u in by)){by[u]=0;order.push(u)}by[u]+=v}});return order.length?order.map(function(u){return fmt(by[u]*100/100)+' '+u}).join(' + '):'0'}
function same(a,b){var n=Math.max(a.length,b.length);for(var i=0;i<n;i++){if((a[i]||0)!==(b[i]||0))return false}return true}
function norm(pi){var a=(NORMS[pi]||[]).slice();while(a.length<MATS.length)a.push(0);return a}
function isCustom(){return false}
function loadDraft(){draft=norm(specSel);vis=[];draft.forEach(function(v,j){if(v>0)vis.push(j)})}
loadDraft();
function renderSpecList(){
  var el=$('#splist'),keep=el.scrollTop;
  $('#spq').placeholder=t('p_search');$('#spq').setAttribute('aria-label',t('p_search'));
  var q=($('#spq').value||'').trim().toLowerCase().replace(/\./g,',');
  var h=PRODUCTS.map(function(n,i){return [n,i]}).filter(function(x){return !PGONE[x[1]]&&(!q||x[0].toLowerCase().replace(/\./g,',').indexOf(q)>-1)}).map(function(x){
    return '<button type="button" class="spitem" data-i="'+x[1]+'"'+(x[1]===specSel?' aria-current="true"':'')+'><span>'+x[0]+'</span>'+(isCustom(x[1])?'<span class="tag">'+t('sp_custom')+'</span>':'')+'</button>';
  }).join('');
  el.innerHTML=h||'<p class="empty" style="padding:10px">'+t('it_empty')+'</p>';
  el.scrollTop=keep;
}
function updateSpecState(){
  var st=$('#spstate'),sv=$('#spsave');if(!st||!sv)return;
  var dirty=!same(draft,NORMS[specSel]||[]);
  st.textContent=dirty?t('sp_unsaved'):'';sv.disabled=!dirty;
  $('#sptot').textContent=specTotal();
}
function renderSpecEditor(){
  var names=MATS.map(function(m,j){return mname(j)}),free=activeMats().filter(function(j){return vis.indexOf(j)<0});
  var rowsH=vis.length?vis.map(function(j){
    return '<tr><td>'+names[j]+'</td><td class="num"><input class="qin" id="sq'+j+'" data-j="'+j+'" type="number" min="0" step="any" inputmode="decimal" aria-label="'+names[j]+'" value="'+(draft[j]>0?draft[j]:'')+'"></td><td>'+matUnit(j)+'</td><td class="num"><button type="button" class="link" data-rmj="'+j+'" aria-label="'+t('p_rm')+'">×</button></td></tr>';
  }).join(''):'<tr><td class="empty" colspan="4">'+t('sp_none')+'</td></tr>';
  if(!PRODUCTS.length||PRODUCTS[specSel]==null){$('#spedit').innerHTML='<p class="empty">'+t('it_empty')+'</p>';return}
  $('#spedit').innerHTML=
    '<div class="sphead"><h2>'+PRODUCTS[specSel]+'</h2>'+(isCustom(specSel)?'<span class="tag">'+t('sp_custom')+'</span>':'')+'</div>'+
    '<div class="scroll"><table><thead><tr><th>'+t('p_mat')+'</th><th class="num">'+t('sp_perunit')+'</th><th></th><th></th></tr></thead><tbody>'+rowsH+'</tbody><tfoot><tr><td><b>'+t('sp_tot')+'</b></td><td class="num mono" id="sptot"></td><td></td><td></td></tr></tfoot></table></div>'+
    (free.length?'<div class="spadd"><select id="spnew" aria-label="'+t('p_mat')+'">'+free.map(function(j){return '<option value="'+j+'">'+names[j]+'</option>'}).join('')+'</select><button type="button" class="btn ghost sm" id="spadd">'+t('sp_addm')+'</button></div>':'')+
    '<div class="field"><label for="spsrc">'+t('sp_copyfrom')+'</label><div class="spadd"><input id="spsrc" type="text" data-pick="prod" role="combobox" aria-autocomplete="list" autocomplete="off" spellcheck="false" placeholder="'+t('p_search')+'"><button type="button" class="btn ghost sm" id="spcopy">'+t('m_copy')+'</button></div></div>'+
    '<div class="pbtns"><button type="button" class="btn primary sm" id="spsave">'+t('sp_save')+'</button>'+(isCustom(specSel)?'<button type="button" class="btn ghost sm" id="spreset">'+t('sp_reset')+'</button>':'')+'<span class="note" id="spstate" style="align-self:center"></span></div>'+
    '<p class="msg" id="spmsg" role="status"></p>';
  var m=$('#spmsg');
  if(spmsg){m.className='msg '+(spmsg.err?'bad':'ok');m.textContent=t(spmsg.key).replace('%s',spmsg.arg||'').replace('%m',spmsg.arg||'')}
  updateSpecState();
}
function renderSpecs(){renderSpecList();renderSpecEditor()}
$('#spq').addEventListener('input',renderSpecList);
$('#splist').addEventListener('click',function(e){var b=e.target.closest('.spitem');if(!b)return;specSel=+b.dataset.i;loadDraft();spmsg=null;renderSpecs()});
$('#spedit').addEventListener('input',function(e){
  if(!e.target.classList.contains('qin'))return;
  var v=parseFloat(e.target.value);draft[+e.target.dataset.j]=v>0?Math.round(v*100)/100:0;
  var m=$('#spmsg');if(m){m.textContent='';m.className='msg'}spmsg=null;updateSpecState();
});
$('#spedit').addEventListener('click',function(e){
  var b=e.target.closest('button');if(!b)return;
  if(b.dataset.rmj!==undefined){var j=+b.dataset.rmj;vis=vis.filter(function(x){return x!==j});draft[j]=0;spmsg=null;renderSpecEditor();return}
  if(b.id==='spadd'){var j2=+$('#spnew').value;vis.push(j2);vis.sort();spmsg=null;renderSpecEditor();var inp=$('#sq'+j2);if(inp)inp.focus();return}
  if(b.id==='spsave'){
    var pid=PRID[specSel];
    srv(api('PUT','/specifications/'+pid,{norms:MATID.map(function(id,j){return {material_id:id,qty:draft[j]||0}}).filter(function(x){return x.qty>0})}),
      function(){loadDraft();spmsg={key:'sp_saved'};renderSpecs()},
      function(e){spmsg={key:'api_raw',arg:apiErr(e),err:true};renderSpecEditor()});
    return}
  if(b.id==='spcopy'){
    var name=$('#spsrc').value.trim(),idx=pidx(name);
    if(idx<0){spmsg={key:'err_prod',err:true}}
    else{draft=norm(idx);vis=[];draft.forEach(function(v,j){if(v>0)vis.push(j)});spmsg={key:'sp_copied',arg:name}}
    renderSpecEditor();
  }
});

