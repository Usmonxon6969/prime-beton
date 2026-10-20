/* Work with several documents at once : every opened document form is a tab above the page.
   The forms keep their state in a few globals (OS, IS, RS, rows ...) and in their inputs. A tab stores a copy of both when
   you leave it and puts them back when you return, so unsaved work is never lost by opening another document.
   Also: "+ new customer / supplier" right inside the order, delivery note and receipt forms. */
var Tabs=(function(){
var X={
 tb_order:['Order','Заказ','Buyurtma'],tb_invoice:['Delivery note','Накладная','Chiqim'],tb_receipt:['Receipt','Поступление','Kirim'],tb_production:['Production','Производство','Ishlab chiqarish'],tb_bank:['Bank','Банк','Bank'],tb_cash:['Cash','Касса','Kassa'],
 tb_new:['new','новый','yangi'],tb_close:['Close tab','Закрыть вкладку','Yorliqni yopish'],tb_sure:['Close? Unsaved data will be lost','Закрыть? Данные не сохранены','Yopilsinmi? Saqlanmagan ma’lumot yo‘qoladi'],tb_label:['Open documents','Открытые документы','Ochiq hujjatlar'],
 qp_cus:['New customer','Новый покупатель','Yangi mijoz'],qp_sup:['New supplier','Новый поставщик','Yangi yetkazib beruvchi'],qp_name:['Name','Название','Nomi'],qp_phone:['Phone','Телефон','Telefon'],qp_save:['Add and select','Добавить и выбрать','Qo‘shish va tanlash'],qp_cancel:['Cancel','Отмена','Bekor qilish'],qp_err_name:['Enter the name.','Введите название.','Nomini kiriting.'],qp_err_dup:['This name already exists.','Такое название уже есть.','Bunday nom mavjud.']
};
Object.keys(X).forEach(function(k){T.en[k]=X[k][0];T.ru[k]=X[k][1];T.uz[k]=X[k][2]});

var S={list:[],cur:null,sw:null,seq:0,ask:null,askT:0};
function cl(o){return JSON.parse(JSON.stringify(o))}
function fieldsOf(box){
  var out={};
  box.querySelectorAll('input[id],select[id],textarea[id]').forEach(function(e){
    if(/\d+$/.test(e.id)||e.type==='file'||/^qp/.test(e.id))return;
    out[e.id]=e.type==='checkbox'?e.checked:e.value;
  });
  return out;
}
function setFields(f){Object.keys(f||{}).forEach(function(id){var e=document.getElementById(id);if(!e)return;if(e.type==='checkbox')e.checked=!!f[id];else e.value=f[id]})}

/* kind -> where its state lives */
var K={
 order:{box:'od-edit',who:'odcus',no:function(){return OS.no},get:function(){return cl(OS)},set:function(s){OS=cl(s)},render:function(){renderOdEd()}},
 invoice:{box:'iv-edit',who:'ivcus',no:function(){return IS.no},get:function(){return cl(IS)},set:function(s){IS=cl(s)},render:function(){renderIvEd()}},
 receipt:{box:'rc-edit',who:'rcsup',no:function(){return RS.no},get:function(){return cl(RS)},set:function(s){RS=cl(s)},render:function(){renderRcEd()}},
 production:{box:'prod-edit',who:null,no:function(){return editNo},
   get:function(){return cl({rows:rows,pcrew:pcrew,psite:psite,mats:mats,editNo:editNo,pmsg:pmsg,pdone:pdone,justPosted:justPosted})},
   set:function(s){s=cl(s);rows=s.rows;pcrew=s.pcrew||[];psite=s.psite;mats=s.mats;editNo=s.editNo;pmsg=s.pmsg;pdone=s.pdone;justPosted=s.justPosted},render:function(){renderProd()}},
 finance:{box:'fin-edit',who:null,no:function(){return FS.no},get:function(){return cl({FS:FS,fmode:fmode})},set:function(s){s=cl(s);FS=s.FS;fmode=s.fmode},render:function(){},
   fields:function(f){
     $('#facc').innerHTML=accList(fmode).map(function(i){return '<option value="'+i+'">'+esc(aname(i))+'</option>'}).join('');
     $('#fkind').innerHTML=['in','out','tr'].map(function(k){return '<option value="'+k+'">'+t('fk_'+k)+'</option>'}).join('');
     $('#fkind').value=f.fkind;$('#facc').value=f.facc;$('#fart').innerHTML='';fillArt();$('#fart').value=f.fart;fillTo();if(f.fto!=null)$('#fto').value=f.fto;toggleFin();
     setFields(f);
     $('#ftitle').textContent=FS.no?tf('fn_edit_h',{s:FS.no}):t('fn_new_'+f.fkind);$('#fback').setAttribute('href','#'+fmode);serr_f(FS.msg&&FS.msg.key,FS.msg&&FS.msg.a);
   }}
};
function kindOf(h){
  var m=/^(order|invoice|receipt|production)-(new|edit)$/.exec(h);if(m)return m[1];
  if(/^(bank|cash)-(new|edit)$/.test(h))return 'finance';
  return null;
}
function capture(tab){
  var k=K[tab.kind],box=document.getElementById(k.box);
  tab.st=k.get();tab.f=fieldsOf(box);tab.no=k.no();
  if(tab.kind==='finance')tab.mode=fmode;
  tab.who=k.who?(document.getElementById(k.who).value||''):(tab.kind==='finance'?(tab.f.famt||''):'');
  tab.dirty=isDirty(tab);
}
function isDirty(tab){
  var st=tab.st||{},r=st.rows||[];
  if(tab.kind==='finance')return !!(tab.f.famt||tab.f.fcom||tab.f.fparty||tab.f.fcus||tab.f.fsup);
  if(tab.who)return true;
  return r.some(function(x){return x&&(x.q>0||(x.p!=null&&x.p>-1)||(x.m!=null&&x.m>-1)||x.t)})||!!(tab.f.odcom||tab.f.ivcom||tab.f.rccom||tab.f.pcom);
}
function restore(tab){
  var k=K[tab.kind];
  k.set(tab.st);
  if(tab.kind==='finance'){k.fields(tab.f)}else{k.render();setFields(tab.f)}
  /* the date fields keep what the user typed; titles are re-rendered by render() */
  if(tab.kind==='production'&&mats)renderMats();
}
function label(tab){
  var base=t('tb_'+(tab.kind==='finance'?tab.mode||'bank':tab.kind));
  var s=base+(tab.no?' '+tab.no:' ('+t('tb_new')+')');
  if(tab.who&&tab.kind!=='finance')s+=' · '+tab.who;
  return s;
}
function current(){for(var i=0;i<S.list.length;i++)if(S.list[i].id===S.cur)return S.list[i];return null}
function save(){var c=current();if(c){capture(c)}}

function pre(h){            /* before the page changes: remember the form we are leaving */
  var c=current();
  if(c&&h!==c.hash){save();S.cur=null}
}
function post(h){           /* after the page changed */
  var kind=ME?kindOf(h):null;
  if(kind){
    var tab;
    if(S.sw){tab=S.sw;S.sw=null;restore(tab);S.cur=tab.id}
    else if(current()&&current().hash===h){tab=current()}
    else{
      var no=K[kind].no();
      tab=no?S.list.filter(function(x){return x.kind===kind&&x.no===no&&(kind!=='finance'||x.mode===fmode)})[0]:null;
      if(tab){restore(tab);S.cur=tab.id;if(typeof toast==='function')toast(label(tab),false,true)}
      else{tab={id:++S.seq,kind:kind,hash:h,st:null,f:{},no:no,who:'',dirty:false,mode:kind==='finance'?fmode:null};S.list.push(tab);S.cur=tab.id;
        /* state was set by the screen just before this call */
        setTimeout(function(){var c=current();if(c&&c.id===tab.id){capture(c);paint()}},0)}
    }
  }
  paint();
}
function goTo(tab){
  if(S.cur===tab.id)return;
  save();S.sw=tab;S.cur=null;
  K[tab.kind].set(tab.st);if(tab.kind==='finance')fmode=tab.mode||fmode;     /* so the route guards ("edit without a document") pass */
  if(location.hash==='#'+tab.hash){route()}else location.hash=tab.hash;
}
function close(id){
  var i=S.list.findIndex(function(x){return x.id===id});if(i<0)return;
  var tab=S.list[i],act=tab.id===S.cur;
  if(act)capture(tab);
  if(tab.dirty&&S.ask!==id){S.ask=id;clearTimeout(S.askT);S.askT=setTimeout(function(){S.ask=null;paint()},3500);paint();return}
  S.ask=null;S.list.splice(i,1);persistSoon();
  if(act){
    S.cur=null;S.sw=null;
    var nx=S.list[Math.min(i,S.list.length-1)];
    if(nx)goTo(nx);else location.hash=back(tab.kind,tab.mode)
  }else paint();
}
function back(kind,mode){return {order:'orders',invoice:'invoices',receipt:'receipts',production:'production',finance:mode||'bank'}[kind]}
function done(){            /* a save went through: the tab has served its purpose */
  var c=current();if(!c)return;
  S.list=S.list.filter(function(x){return x.id!==c.id});S.cur=null;S.sw=null;
}
function paint(){
  var el=document.getElementById('doctabs');
  if(!el)return;
  if(!ME||!S.list.length){el.hidden=true;el.innerHTML='';document.body.classList.remove('has-tabs');return}
  var c=current();if(c){c.who=K[c.kind].who&&document.getElementById(K[c.kind].who)?document.getElementById(K[c.kind].who).value:c.who}
  el.hidden=false;document.body.classList.add('has-tabs');
  el.setAttribute('aria-label',t('tb_label'));
  el.innerHTML=S.list.map(function(x){
    var on=x.id===S.cur,ask=S.ask===x.id;
    return '<div class="dtab'+(on?' on':'')+(x.dirty||(on&&true)?'':'')+'" role="tab" aria-selected="'+on+'" data-id="'+x.id+'"><button type="button" class="dt-main" data-act="go" data-id="'+x.id+'" title="'+esc(label(x))+'">'+(x.dirty?'<i class="dt-dot" aria-hidden="true"></i>':'')+'<span>'+esc(label(x))+'</span></button>'+
      '<button type="button" class="dt-x'+(ask?' ask':'')+'" data-act="x" data-id="'+x.id+'" aria-label="'+esc(ask?t('tb_sure'):t('tb_close'))+'" title="'+esc(ask?t('tb_sure'):t('tb_close'))+'">'+(ask?'?':'×')+'</button></div>';
  }).join('');
}

/* ---- quick add of a customer / supplier from inside a document ---- */
var QP={cus:{inputs:['odcus','ivcus'],sec:'cus',lbl:'qp_cus',path:'/customers',find:function(n){return cidx(n)},sel:'#clist'},
        sup:{inputs:['rcsup'],sec:'sup',lbl:'qp_sup',path:'/suppliers',find:function(n){return sidx(n)}}};
function qpInit(){
  Object.keys(QP).forEach(function(kind){
    QP[kind].inputs.forEach(function(id){
      var inp=document.getElementById(id);if(!inp)return;var field=inp.closest('.field');
      if(!field.querySelector('.qpadd')){
        var b=document.createElement('button');b.type='button';b.className='link qpadd';b.dataset.kind=kind;b.dataset.for=id;b.id='qpb_'+id;field.appendChild(b);
        var box=document.createElement('div');box.className='qpbox';box.id='qpbox_'+id;box.hidden=true;field.appendChild(box);
      }
      var btn=field.querySelector('.qpadd');btn.textContent='+ '+t(QP[kind].lbl);btn.hidden=lvl(QP[kind].sec)<2;
    });
  });
}
function qpOpen(id,kind){
  var inp=document.getElementById(id),box=document.getElementById('qpbox_'+id),q=QP[kind];
  var typed=(inp.value||'').trim();
  box.hidden=false;
  box.innerHTML='<div class="fgrid"><div class="field"><label for="qpn_'+id+'">'+t('qp_name')+'</label><input id="qpn_'+id+'" type="text" autocomplete="off" value="'+esc(typed)+'"></div>'+
   '<div class="field"><label for="qpp_'+id+'">'+t('qp_phone')+'</label><input id="qpp_'+id+'" data-phone type="text" inputmode="tel" autocomplete="off"></div></div>'+
   '<div class="pbtns"><button type="button" class="btn primary sm" data-act="qpsave" data-for="'+id+'" data-kind="'+kind+'">'+t('qp_save')+'</button><button type="button" class="btn ghost sm" data-act="qpcancel" data-for="'+id+'">'+t('qp_cancel')+'</button></div><p class="msg bad" id="qpe_'+id+'" role="alert"></p>';
  document.getElementById('qpn_'+id).focus();
}
function qpSave(id,kind){
  var q=QP[kind],name=document.getElementById('qpn_'+id).value.trim().replace(/\s+/g,' '),ph=Phone.out(document.getElementById('qpp_'+id).value),err=document.getElementById('qpe_'+id);
  if(!name){err.textContent=t('qp_err_name');return}
  if(ph===null){err.textContent=t('ph_bad');return}
  if(q.find(name)>-1){document.getElementById(id).value=name;qpClose(id);return}     /* already exists: just select it */
  srv(api('POST',q.path,{name:name,phone:ph,contact:''}),function(){
    document.getElementById(id).value=name;qpClose(id);
    var c=current();if(c)capture(c);paint();
  },function(e){err.textContent=apiErr(e)});
}
function qpClose(id){var b=document.getElementById('qpbox_'+id);if(b){b.hidden=true;b.innerHTML=''}}

document.addEventListener('click',function(e){
  var b=e.target.closest('[data-act],.qpadd');if(!b)return;
  var a=b.dataset.act;
  if(b.classList.contains('qpadd')){qpOpen(b.dataset.for,b.dataset.kind);return}
  var id=+b.dataset.id;
  if(a==='go'){var tab=S.list.filter(function(x){return x.id===id})[0];if(tab)goTo(tab)}
  else if(a==='x')close(id);
  else if(a==='qpsave')qpSave(b.dataset.for,b.dataset.kind);
  else if(a==='qpcancel')qpClose(b.dataset.for);
});
/* keep the tab caption and the dirty dot current while typing */
document.addEventListener('input',function(e){
  var c=current();if(!c||!e.target.closest('#'+K[c.kind].box))return;
  clearTimeout(S.it);S.it=setTimeout(function(){capture(c);paint();persistSoon()},250);
});
/* ---- drafts survive F5, a closed browser and a lost connection: open unsaved forms are kept in this browser, per user,
   and wiped on an explicit sign-out (a session that merely expires keeps them, so nobody loses work to a timeout) ---- */
var DK=function(){return ME?'pb-drafts:'+ME.u:null};
function persist(){
  var k=DK();if(!k)return;
  try{
    var c=current();if(c)capture(c);
    var keep=S.list.filter(function(x){return x.dirty}).map(function(x){return {id:x.id,kind:x.kind,hash:x.hash,st:x.st,f:x.f,no:x.no,who:x.who,dirty:true,mode:x.mode,at:x.at||Date.now()}});
    if(!keep.length){localStorage.removeItem(k);return}
    localStorage.setItem(k,JSON.stringify({seq:S.seq,cur:S.cur,list:keep}));
  }catch(e){}
}
var PT=null;function persistSoon(){clearTimeout(PT);PT=setTimeout(persist,400)}
function load(){
  var k=DK();if(!k||S.list.length)return;
  try{
    var raw=localStorage.getItem(k);if(!raw)return;
    var d=JSON.parse(raw),week=7*864e5,now=Date.now();
    S.list=(d.list||[]).filter(function(x){return K[x.kind]&&now-(x.at||now)<week});
    S.seq=Math.max(d.seq||0,S.list.reduce(function(m,x){return Math.max(m,x.id)},0));
    S.cur=null;S.sw=null;
    var h=(location.hash||'').replace('#','');
    var tab=S.list.filter(function(x){return x.hash===h&&(x.id===d.cur||!S.list.some(function(y){return y.hash===h&&y.id===d.cur}))})[0];
    if(tab){K[tab.kind].set(tab.st);if(tab.kind==='finance')fmode=tab.mode||fmode;S.sw=tab}   /* the page we reloaded on gets its form back */
  }catch(e){S.list=[]}
}
function wipe(){var k=DK();if(k){try{localStorage.removeItem(k)}catch(e){}}}
function reset(){S.list=[];S.cur=null;S.sw=null;S.ask=null}
return {pre:pre,post:post,done:function(){done();persistSoon()},paint:paint,qpInit:qpInit,reset:reset,load:load,wipe:wipe,persist:persist,state:S};
})();
window.addEventListener('pagehide',function(){try{Tabs.persist()}catch(e){}});
