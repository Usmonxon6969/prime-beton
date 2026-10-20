/* cash and bank */
var FX={
 nav_bank:['Bank','Банк','Bank'],
 nav_cash:['Cash desk','Касса','Kassa'],
 fin_h_bank:['Bank','Банк','Bank'],
 fin_h_cash:['Cash desk','Касса','Kassa'],
 fin_note_bank:['Receipts and payments on bank accounts. Customer payments reduce what the customer owes.','Поступления и списания по банковским счетам. Оплаты покупателей уменьшают их долг.','Bank hisoblari bo‘yicha kirim va chiqimlar. Mijoz to‘lovlari uning qarzini kamaytiradi.'],
 fin_note_cash:['Cash receipts and payments. A cash desk cannot go below zero.','Приходные и расходные кассовые операции. Остаток кассы не может быть отрицательным.','Kassa kirim va chiqimlari. Kassa qoldig‘i noldan kam bo‘la olmaydi.'],
 fk_in:['Income','Приход','Kirim'],
 fk_out:['Expense','Расход','Chiqim'],
 fk_tr:['Transfer','Перемещение','O‘tkazma'],
 fn_new_in:['New income','Новый приход','Yangi kirim'],
 fn_new_out:['New expense','Новый расход','Yangi chiqim'],
 fn_new_tr:['New transfer','Новое перемещение','Yangi o‘tkazma'],
 fn_edit_h:['Edit document %s','Редактирование документа %s','%s hujjatini tahrirlash'],
 fa_cust:['Payment from customer','Оплата от покупателей','Mijoz to‘lovi'],
 fa_oin:['Other income','Прочий приход','Boshqa kirim'],
 fa_sup:['Payment to supplier','Оплата поставщику','Yetkazib beruvchiga to‘lov'],
 fa_sal:['Salary','Зарплата','Ish haqi'],
 fa_tax:['Taxes','Налоги','Soliqlar'],
 fa_fee:['Bank fees','Банковское обслуживание','Bank xizmati'],
 fa_oout:['Other expense','Прочий расход','Boshqa chiqim'],
 fa_tr:['Transfer between accounts','Перемещение между счетами','Hisoblar o‘rtasida o‘tkazma'],
 f_acc:['Account','Счёт / касса','Hisob / kassa'],
 f_art:['Cash flow item','Статья ДДС','Moddasi'],
 f_party:['Counterparty','Контрагент','Kontragent'],
 f_to:['To account','На счёт / кассу','Qaysi hisobga'],
 f_amt:['Amount, UZS','Сумма, сум','Summa, so‘m'],
 f_bal:['Balance','Остаток','Qoldiq'],
 f_allacc:['All accounts','Все счета','Barcha hisoblar'],
 f_type:['Type','Вид','Turi'],
 fn_saved:['Document %m saved.','Документ %m сохранён.','%m hujjati saqlandi.'],
 fn_deleted:['Document %m deleted. The balance is restored.','Документ %m удалён. Остаток восстановлен.','%m hujjati o‘chirildi. Qoldiq tiklandi.'],
 fn_restored:['Document %m restored.','Документ %m восстановлен.','%m hujjati tiklandi.'],
 fn_err_amt:['Enter an amount greater than zero.','Укажите сумму больше нуля.','Summani noldan katta kiriting.'],
 fn_err_acc:['Choose a different destination account.','Выберите другой счёт назначения.','Boshqa hisobni tanlang.'],
 fn_err_neg:['This would make the balance of %m negative.','Остаток по «%m» станет отрицательным.','“%m” qoldig‘i manfiy bo‘lib qoladi.'],
 fn_del_q:['Delete this document? It stays in the journal as Deleted and the balance is restored.','Удалить документ? Он останется в журнале со статусом Удалён, остаток будет восстановлен.','Hujjat o‘chirilsinmi? U jurnalda “o‘chirilgan” holatida qoladi, qoldiq tiklanadi.'],
 cu_debt:['Debt (+) / advance (−), UZS','Долг (+) / аванс (−), сум','Qarz (+) / avans (−), so‘m']
};
Object.keys(FX).forEach(function(k){T.en[k]=FX[k][0];T.ru[k]=FX[k][1];T.uz[k]=FX[k][2]});
var ACC=[];
function aname(i){return ACC[i].n[lang]}
var ART={'in':['cust','oin'],out:['sup','sal','tax','fee','oout'],tr:['tr']};
var FIN=[],fmode='bank',fKind='in',fPreset=null,fCopy=null,FM=null,fkf='all',FS={no:null,msg:null};
function finSort(){}
function findF(no){for(var i=0;i<FIN.length;i++){if(FIN[i].no===no)return FIN[i]}return null}
function accList(mode){var a=[];ACC.forEach(function(x,i){if(!x.gone&&(!mode||x.t===mode))a.push(i)});return a}
function accBal(i){return ACC[i]?(ACC[i].bal||0):0}
function custPaid(i){return FIN.reduce(function(s,d){return s+(d.status==='posted'&&d.kind==='in'&&d.art==='cust'&&d.cus===i?d.amt:0)},0)}
/* what customer i owes by lateness: payments go to the oldest delivery notes; a note is due on its pay-by date (or the delivery day) */
function custAging(i,now){
  now=now||new Date();var today=new Date(now.getFullYear(),now.getMonth(),now.getDate()).getTime(),left=custPaid(i),r={overdue:0,current:0,advance:0,oldest:0};
  INV.filter(function(v){return v.status==='posted'&&v.cus===i}).sort(function(a,b){return a.date-b.date||a.id-b.id}).forEach(function(v){
    var amt=rsum(v.rows),cover=Math.min(left,amt);left-=cover;var rest=amt-cover;if(rest<=0)return;
    var d=v.pay||v.date,due=new Date(d.getFullYear(),d.getMonth(),d.getDate()).getTime(),late=Math.round((today-due)/864e5);
    if(late>0){r.overdue+=rest;if(late>r.oldest)r.oldest=late}else r.current+=rest;
  });
  r.advance=left;return r;
}
function custDebt(i){return INV.reduce(function(s,v){return s+(v.status==='posted'&&v.cus===i?rsum(v.rows):0)},0)-custPaid(i)}
function finFlow(d){
  if(d.kind==='in')return 1;if(d.kind==='out')return -1;
  var a=ACC[d.acc].t===fmode,b=ACC[d.to].t===fmode;
  return (a&&b)?0:(a?-1:1);
}

function renderFinMsg(){renderMsgEl('#fmsg',FM)}
function renderFin(){
  closeMenu();
  var mode=fmode;
  $('#fin-h').textContent=t('fin_h_'+mode);$('#fin-note').textContent=t('fin_note_'+mode);
  var sel=$('#facf'),cur=sel.value;
  sel.innerHTML='<option value="">'+t('f_allacc')+'</option>'+accList(mode).map(function(i){return '<option value="'+i+'">'+esc(aname(i))+'</option>'}).join('');
  sel.value=accList(mode).some(function(i){return String(i)===cur})?cur:'';
  var cards=accList(mode).map(function(i){return '<div class="fcard"><span>'+esc(aname(i))+'</span><b>'+money(accBal(i))+'</b></div>'}).join('');
  var tot=accList(mode).reduce(function(s,i){return s+accBal(i)},0);
  $('#fcards').innerHTML=cards+'<div class="fcard tot"><span>'+t('c_total')+'</span><b>'+money(tot)+'</b></div>';
  document.querySelectorAll('#fkf button').forEach(function(b){b.textContent=b.dataset.k==='all'?t('f_all'):t('fk_'+b.dataset.k);b.setAttribute('aria-pressed',String(b.dataset.k===fkf))});
  $('#fq').placeholder=t('p_search');$('#fq').setAttribute('aria-label',t('p_search'));
  var q=($('#fq').value||'').trim().toLowerCase(),af=sel.value===''?-1:+sel.value;
  var list=FIN.filter(function(d){
    if(!(ACC[d.acc].t===mode||(d.kind==='tr'&&ACC[d.to].t===mode)))return false;
    if(af>-1&&d.acc!==af&&d.to!==af)return false;
    if(fkf!=='all'&&d.kind!==fkf)return false;
    return !q||(d.no+' '+aname(d.acc)+' '+t('fa_'+d.art)+' '+t('fk_'+d.kind)+' '+(d.cus>-1?CUS[d.cus].n:d.sup>-1?SUP[d.sup].n:d.party)+' '+d.comment).toLowerCase().indexOf(q)>-1;
  });
  var si=0,so=0;
  var head='<thead><tr><th>'+t('c_no')+'</th><th>'+t('c_dt')+'</th><th>'+t('f_acc')+'</th><th>'+t('f_art')+'</th><th class="num">'+t('f_amt')+'</th><th>'+t('c_status')+'</th><th><span class="vh">'+t('m_actions')+'</span></th></tr></thead>';
  var body=list.length?list.map(function(d){
    var fl=finFlow(d),who=d.cus>-1?CUS[d.cus].n:d.sup>-1?SUP[d.sup].n:d.party;
    if(d.status==='posted'){if(fl>0)si+=d.amt;else if(fl<0)so+=d.amt}
    var acc=d.kind==='tr'?esc(aname(d.acc))+' → '+esc(aname(d.to)):esc(aname(d.acc));
    return '<tr class="'+(d.status==='deleted'?'is-deleted':'')+'"><td class="mono">'+d.no+'</td><td class="mono">'+dtf(d.date)+'</td><td class="fw">'+acc+'</td><td class="fw">'+t('fa_'+d.art)+([who,d.comment].filter(Boolean).length?'<div class="note">'+esc([who,d.comment].filter(Boolean).join(' \u00b7 '))+'</div>':'')+'</td><td class="num amt '+(fl>0?'in':fl<0?'out':'')+'">'+(fl>0?'+ ':fl<0?'− ':'↔ ')+money(d.amt)+'</td><td>'+pill(d.status)+'</td><td class="act">'+kebabHtml('fn',d.no,d.no)+'</td></tr>';
  }).join(''):'<tr><td class="empty" colspan="7">'+t('em_doc')+'</td></tr>';
  $('#ftbl').innerHTML=head+'<tbody>'+body+'</tbody>';
  $('#fsum').textContent=t('fk_in')+': '+money(si)+' '+t('cur')+'  ·  '+t('fk_out')+': '+money(so)+' '+t('cur');
  renderFinMsg();
}
function fillArt(){
  var k=$('#fkind').value,cur=$('#fart').value,arts=ART[k];
  $('#fart').innerHTML=arts.map(function(a){return '<option value="'+a+'">'+t('fa_'+a)+'</option>'}).join('');
  $('#fart').value=arts.indexOf(cur)>-1?cur:arts[0];
  fillTo();toggleFin();
}
function fillTo(){
  var acc=+$('#facc').value,cur=$('#fto').value;
  var ids=accList().filter(function(i){return i!==acc});
  $('#fto').innerHTML=ids.map(function(i){return '<option value="'+i+'">'+esc(aname(i))+'</option>'}).join('');
  if(ids.some(function(i){return String(i)===cur}))$('#fto').value=cur;
}
function fillOrd(){
  var on=$('#fart').value==='cust'&&$('#fkind').value==='in',w=$('#ford-w');w.hidden=!on;if(!on)return;
  var c=cidx($('#fcus').value),cur=$('#ford').value||(FS.ord||''),h='<option value="">'+t('f_order_none')+'</option>';
  ORD.forEach(function(o){if(o.status==='deleted'||(c>-1&&o.cus!==c)||(c<0))return;h+='<option value="'+o.id+'">'+o.no+' · '+money(rsum(o.rows))+'</option>'});
  $('#ford').innerHTML=h;$('#ford').value=String(cur);if($('#ford').value!==String(cur))$('#ford').value='';
}
function fillWork(){
  var on=$('#fart').value==='sal'&&$('#fkind').value==='out',w=$('#fwork-w');w.hidden=!on;if(!on)return;
  var cur=$('#fwork').value||(FS.wid||'');
  $('#fwork').innerHTML='<option value="">'+t('f_worker_none')+'</option>'+WORKERS.map(function(x){return '<option value="'+x.id+'">'+esc(x.name)+'</option>'}).join('');
  $('#fwork').value=String(cur);if($('#fwork').value!==String(cur))$('#fwork').value='';
}
function toggleFin(){
  var k=$('#fkind').value,a=$('#fart').value;
  $('#fto-w').hidden=k!=='tr';$('#fcus-w').hidden=a!=='cust';fillOrd();fillWork();$('#fsup-w').hidden=a!=='sup';$('#fparty-w').hidden=(k==='tr'||a==='cust'||a==='sup');
}
function fillFin(d){
  var mode=fmode;
  $('#facc').innerHTML=accList(mode).map(function(i){return '<option value="'+i+'">'+esc(aname(i))+'</option>'}).join('');
  $('#fkind').innerHTML=['in','out','tr'].map(function(k){return '<option value="'+k+'">'+t('fk_'+k)+'</option>'}).join('');
  $('#fkind').value=d.kind;$('#facc').value=String(d.acc);
  $('#fart').innerHTML='';fillArt();
  $('#fart').value=d.art;fillTo();if(d.to!=null)$('#fto').value=String(d.to);toggleFin();
  $('#fcus').value=d.cus>-1?CUS[d.cus].n:'';$('#fsup').value=d.sup>-1?SUP[d.sup].n:'';$('#fparty').value=d.party||'';
  $('#famt').value=d.amt>0?money(d.amt):'';$('#fcom').value=d.comment||'';
  $('#fdate').value=toLocal(d.date);FS.ord=d.oid||'';$('#ford').innerHTML='';fillOrd();FS.wid=d.wid||'';$('#fwork').innerHTML='';fillWork();
  $('#ftitle').textContent=FS.no?tf('fn_edit_h',{s:FS.no}):t('fn_new_'+d.kind);
  $('#fback').setAttribute('href','#'+fmode);
  serr_f(null);
}
function serr_f(key,a){FS.msg=key?{key:key,a:a}:null;$('#ferr').textContent=key?tf(key,a):''}
function renderFinEd(){
  if(!$('#fin-edit').hidden||$('#facc').options.length){
    var d=FS.no?findF(FS.no):null;
    var keep={kind:$('#fkind').value||'in',art:$('#fart').value,acc:$('#facc').value};
    $('#facc').innerHTML=accList(fmode).map(function(i){return '<option value="'+i+'">'+esc(aname(i))+'</option>'}).join('');
    if(keep.acc)$('#facc').value=keep.acc;
    $('#fkind').innerHTML=['in','out','tr'].map(function(k){return '<option value="'+k+'">'+t('fk_'+k)+'</option>'}).join('');
    $('#fkind').value=keep.kind;
    var cur=$('#fart').value;fillArt();if(cur)$('#fart').value=cur;
    $('#ftitle').textContent=FS.no?tf('fn_edit_h',{s:FS.no}):t('fn_new_'+$('#fkind').value);
    if(FS.msg)$('#ferr').textContent=tf(FS.msg.key,FS.msg.a);
  }
}
function newFin(){
  var c=fCopy,k=fPreset||'in';fCopy=null;fPreset=null;FS.no=null;
  var base=c?{kind:c.kind,acc:c.acc,art:c.art,cus:c.cus,sup:c.sup>-1?c.sup:-1,party:c.party,to:c.to,amt:c.amt,comment:c.comment}:{kind:k,acc:accList(fmode)[0],art:ART[k][0],cus:-1,sup:-1,party:'',to:null,amt:0,comment:''};
  base.date=new Date();fillFin(base);
}
function openFinEdit(no){
  var d=findF(no);if(!d||d.status==='deleted')return;
  FS.no=no;fmode=ACC[d.acc].t;fillFin(d);location.hash=fmode+'-edit';
}
function saveFin(){
  var dt=new Date($('#fdate').value),acc=+$('#facc').value,kind=$('#fkind').value,art=$('#fart').value,amt=parseMoney($('#famt').value),to=null,cus=-1,party='',sup=-1;
  if(isNaN(dt.getTime())){serr_f('err_date');return}
  if(!(amt>0)){serr_f('fn_err_amt');return}
  if(kind==='tr'){to=+$('#fto').value;if(isNaN(to)||to===acc){serr_f('fn_err_acc');return}}
  if(art==='cust'){cus=cidx($('#fcus').value);if(cus<0){serr_f('od_err_cus');return}}
  else if(art==='sup'){sup=sidx($('#fsup').value);if(sup<0){serr_f('rc_err_sup');return}}else if(kind!=='tr')party=$('#fparty').value.trim();
  var old=FS.no?findF(FS.no):null;
  var body={date:isoLocal(dt),kind:kind,account_id:ACC[acc].id,to_account_id:kind==='tr'?ACC[to].id:null,article:art,
    customer_id:cus>-1?CUS[cus].id:null,supplier_id:sup>-1?SUP[sup].id:null,order_id:(art==='cust'&&kind==='in'&&$('#ford').value)?+$('#ford').value:null,worker_id:(art==='sal'&&kind==='out'&&$('#fwork').value)?+$('#fwork').value:null,party:party,amount:amt,comment:$('#fcom').value};
  srv(old?api('PUT','/finance/'+old.id,body):api('POST','/finance',body),function(r){
    FM={key:'fn_saved',m:r.number};FS.no=null;fmode=ACC[acc].t;Tabs.done();location.hash=fmode;
  },function(e){serr_f('api_raw',{m:apiErr(e)})});
}
function setFinStatus(no,st,key){
  var d=findF(no);
  srv(st==='deleted'?api('DELETE','/finance/'+d.id):api('POST','/finance/'+d.id+'/restore'),function(){FM={key:key,m:no};renderFin()},function(e){FM=apiMsg(e);renderFin()});
}
$('#fsave').addEventListener('click',saveFin);
$('#fkind').addEventListener('change',function(){fillArt();fillOrd();fillWork();$('#ftitle').textContent=FS.no?tf('fn_edit_h',{s:FS.no}):t('fn_new_'+this.value);serr_f(null)});
$('#fart').addEventListener('change',function(){toggleFin();serr_f(null)});
$('#fcus').addEventListener('input',function(){fillOrd()});
$('#fcus').addEventListener('change',function(){fillOrd()});
$('#facc').addEventListener('change',function(){fillTo();serr_f(null)});
$('#famt').addEventListener('input',function(){moneyType(this);serr_f(null)});
$('#famt').addEventListener('focusout',function(){var v=parseMoney(this.value);this.value=v>0?money(v):''});
$('#fq').addEventListener('input',renderFin);
$('#facf').addEventListener('change',renderFin);
document.querySelectorAll('#fkf button').forEach(function(b){b.addEventListener('click',function(){fkf=b.dataset.k;renderFin()})});
document.querySelectorAll('#fnew button').forEach(function(b){b.addEventListener('click',function(){fPreset=b.dataset.k;location.hash=fmode+'-new'})});
$('#ftbl').addEventListener('click',kebabClick);
MENUS.fn={
  html:function(no){
    var d=findF(no),dead=d.status==='deleted';
    return (dead?'':mi('edit',ICO.edit,t('m_edit')))+mi('copy',ICO.copy,t('m_copy'))+(dead?mi('restore',ICO.restore,t('m_restore')):mi('del',ICO.del,t('m_del'),'del'));
  },
  q:function(){return t('fn_del_q')},
  act:function(a,no){
    if(a==='edit')openFinEdit(no);
    else if(a==='copy'){fCopy=findF(no);fPreset=null;fmode=ACC[fCopy.acc].t;location.hash=fmode+'-new'}
    else if(a==='confirmdel')setFinStatus(no,'deleted','fn_deleted');
    else if(a==='restore')setFinStatus(no,'posted','fn_restored');
  }
};

