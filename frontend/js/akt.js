/* reconciliation statement (akt sverka) */
var AX={
 ak_h:['Reconciliation statement','Акт сверки','Akt sverka'],
 ak_back:['Back to customers','К покупателям','Mijozlarga qaytish'],
 ak_from:['From','С даты','Boshlanishi'],
 ak_to:['To','По дату','Tugashi'],
 ak_all:['All time','За всё время','Barcha davr'],
 ak_open:['Opening balance','Сальдо на начало','Davr boshiga qoldiq'],
 ak_close:['Closing balance','Сальдо на конец','Davr oxiriga qoldiq'],
 ak_turn:['Turnover for the period','Обороты за период','Davr aylanmasi'],
 ak_deb:['Shipped (debit)','Отгружено (дебет)','Jo‘natilgan (debet)'],
 ak_cre:['Paid (credit)','Оплачено (кредит)','To‘langan (kredit)'],
 ak_bal:['Balance','Сальдо','Qoldiq'],
 ak_doc:['Document','Документ','Hujjat'],
 ak_inv:['Delivery note','Расходная накладная','Chiqim nakladnoyi'],
 ak_pay:['Payment','Оплата','To‘lov'],
 ak_owes:['The customer owes us','Покупатель должен нам','Mijoz bizga qarzdor'],
 ak_we:['We owe the customer (advance)','Мы должны покупателю (аванс)','Biz mijozga qarzdormiz (avans)'],
 ak_even:['Accounts are settled','Расчёты закрыты','Hisob-kitob teng'],
 ak_empty:['No documents in this period.','За этот период документов нет.','Bu davrda hujjat yo‘q.'],
 ak_copy:['Copy as text','Копировать текстом','Matn sifatida nusxalash'],
 ak_copied:['Copied to clipboard.','Скопировано в буфер обмена.','Nusxalandi.'],
 ak_copyfail:['Could not copy. Select the table and copy it by hand.','Не удалось скопировать. Выделите таблицу и скопируйте вручную.','Nusxalab bo‘lmadi. Jadvalni belgilab, qo‘lda nusxalang.']
};
Object.keys(AX).forEach(function(k){T.en[k]=AX[k][0];T.ru[k]=AX[k][1];T.uz[k]=AX[k][2]});

var AX2={
 ak_period_all:['in UZS, all time','в UZS за все время','so\u2018mda, barcha davr'],
 ak_period:['in UZS, %a \u2013 %b','в UZS за период %a \u2013 %b','so\u2018mda, %a \u2013 %b davri'],
 ak_up:['Debt increase','Увеличение долга','Qarz oshishi'],
 ak_down:['Debt decrease','Уменьшение долга','Qarz kamayishi'],
 ak_cur_owes:['The customer owes us at the moment','Долг контрагента перед нами на текущий момент','Mijozning bizdan qarzi hozirgi holatda'],
 ak_cur_we:['We owe the customer at the moment (advance)','Наш долг перед контрагентом на текущий момент (аванс)','Bizning mijoz oldidagi qarzimiz hozirgi holatda (avans)'],
 ak_chg:['Change of the customer debt','Изменение долга контрагента','Mijoz qarzining o\u2018zgarishi'],
 ak_incr:['increase','увеличение','oshish'],
 ak_decr:['decrease','уменьшение','kamayish'],
 ak_dated:['dated','от','sana'],
 ak_rcpt_bank:['Bank receipt','Поступление на счет','Bank hisobiga kirim'],
 ak_rcpt_cash:['Cash receipt','Поступление в кассу','Kassaga kirim'],
 ak_openb:['Debt at the start of the period','Долг на начало периода','Davr boshidagi qarz']
};
Object.keys(AX2).forEach(function(k){T.en[k]=AX2[k][0];T.ru[k]=AX2[k][1];T.uz[k]=AX2[k][2]});
var AK={cus:-1,sup:false,text:'',msg:null};
function sgnM(n){return n<0?'− '+money(-n):money(n)}
function aktDocs(c){
  var a=[];
  INV.forEach(function(v){if(v.status==='posted'&&v.cus===c)a.push({d:v.date,k:'inv',no:v.no,amt:rsum(v.rows),rows:v.rows,note:v.ord||''})});
  FIN.forEach(function(f){if(f.status==='posted'&&f.kind==='in'&&f.art==='cust'&&f.cus===c)a.push({d:f.date,k:ACC[f.acc].t==='cash'?'cash':'bank',no:f.no,amt:f.amt,note:aname(f.acc)+(f.comment?' · '+f.comment:'')})});
  return a.sort(function(x,y){return x.d-y.d||(x.k==='inv'?-1:1)});
}
function openAkt(c){
  AK.cus=c;AK.sup=false;AK.msg=null;
  $('#akfrom').value='';$('#akto').value=toDay(new Date());
  location.hash='customer-akt';
}
function renderAkt(){
  if(AK.cus<0||$('#cu-akt').hidden)return;
  var c=AK.sup?SUP[AK.cus]:CUS[AK.cus],from=pday($('#akfrom').value),to=pday($('#akto').value),end=to?new Date(to.getTime()+86400000):null;
  var all=AK.sup?supDocs(AK.cus):aktDocs(AK.cus),rows=[],up=0,down=0,open=0;
  all.forEach(function(x){
    var delta=x.k==='inv'?x.amt:-x.amt;
    if(from&&x.d<from){open+=delta;return}
    if(end&&x.d>=end)return;
    rows.push(x);
    if(x.k==='inv')up+=x.amt;else down+=x.amt;
  });
  var cur=open+up-down,today=pday(toDay(new Date()));
  var allTime=!from&&(!to||to>=today);
  var per=allTime?t('ak_period_all'):t('ak_period').replace('%a',from?dfmt(from):'…').replace('%b',to?dfmt(to):'…');
  $('#aktitle').textContent=t('ak_h')+': '+c.n;
  $('#aksub').textContent=[c.ph,c.ct].filter(Boolean).join(' · ');
  $('#akfrom-l').textContent=t('ak_from');$('#akto-l').textContent=t('ak_to');
  var curLabel=t(AK.sup?(cur>=0?'ak_cur_sup':'ak_cur_supadv'):(cur>=0?'ak_cur_owes':'ak_cur_we')),curAmt=Math.abs(cur);
  var sum='<div class="akper">'+esc(per)+'</div>';
  if(!allTime&&from)sum+='<div class="akl"><span>'+t('ak_openb')+'</span><b>'+sgnM(open)+'</b></div>';
  sum+='<div class="akl"><span>'+t('ak_up')+'</span><b>'+money(up)+'</b></div>'+
       '<div class="akl"><span>'+t('ak_down')+'</span><b>'+money(down)+'</b></div>'+
       '<div class="akl last"><span>'+curLabel+'</span><b class="amt '+(cur>0?'out':cur<0?'in':'')+'">'+money(curAmt)+'</b></div>';
  $('#aksum').innerHTML=sum;
  $('#akhd').textContent=t(AK.sup?'ak_chg_sup':'ak_chg');var bk=document.querySelector('#cu-akt .back');bk.setAttribute('href',AK.sup?'#suppliers':'#customers');bk.textContent=t(AK.sup?'ak_back_sup':'ak_back');
  var head='<thead><tr><th>'+t('ak_doc')+'</th><th></th><th class="num">'+t('ak_incr')+'</th><th class="num">'+t('ak_decr')+'</th></tr></thead>';
  var body='',L=['\t'+t(AK.sup?'ak_chg_sup':'ak_chg'),[t('ak_doc'),'',t('ak_incr'),t('ak_decr')].join('\t')];
  rows.forEach(function(x){
    var inv=x.k==='inv',ttl=t(x.lbl||(inv?'ak_inv':x.k==='cash'?'ak_rcpt_cash':'ak_rcpt_bank'))+' '+x.no+' '+t('ak_dated')+' '+dfmt(x.d);
    body+='<tr class="akd"><td colspan="2" class="wrap">'+esc(ttl)+'</td><td class="num" data-l="'+t('ak_incr')+'">'+(inv?money(x.amt):'')+'</td><td class="num" data-l="'+t('ak_decr')+'">'+(inv?'':money(x.amt))+'</td></tr>';
    L.push([ttl,'',inv?money(x.amt):'',inv?'':money(x.amt)].join('\t'));
    if(inv){
      (x.items||x.rows.map(function(r){return {n:PRODUCTS[r.p],q:r.q,pr:r.pr,u:uname(punit(r.p))}})).forEach(function(r){
        var det=fmt(r.q)+' '+r.u+' x '+money(r.pr)+' '+t('cur');
        body+='<tr class="aki"><td>'+esc(r.n)+'</td><td class="mono">'+esc(det)+'</td><td class="num">'+money(r.q*r.pr)+'</td><td></td></tr>';
        L.push([r.n,det,money(r.q*r.pr),''].join('\t'));
      });
    }else{
      body+='<tr class="aki"><td colspan="2">'+esc(x.note)+'</td><td></td><td class="num">'+money(x.amt)+'</td></tr>';
    }
  });
  if(!rows.length)body='<tr><td class="empty" colspan="4">'+t('ak_empty')+'</td></tr>';
  $('#aktbl').innerHTML=head+'<tbody>'+body+'</tbody>';
  AK.text=[t('ak_h')+': '+c.n,per,t('ak_up')+'\t\t\t'+money(up),t('ak_down')+'\t\t\t'+money(down),curLabel+'\t\t\t'+money(curAmt),''].concat(L).join('\n');
  var m=$('#akmsg');m.className='msg'+(AK.msg?(AK.msg.err?' bad':' ok'):'');m.textContent=AK.msg?t(AK.msg.key):'';
}
function copyAkt(){
  var done=function(ok){AK.msg={key:ok?'ak_copied':'ak_copyfail',err:!ok};renderAkt()};
  try{
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(AK.text).then(function(){done(true)},function(){done(false)});return}
  }catch(e){}
  try{
    var ta=document.createElement('textarea');ta.value=AK.text;ta.setAttribute('readonly','');ta.style.cssText='position:fixed;opacity:0;top:0;left:0';
    document.body.appendChild(ta);ta.select();var ok=document.execCommand('copy');document.body.removeChild(ta);done(!!ok);
  }catch(e2){done(false)}
}
$('#akfrom').addEventListener('change',renderAkt);
$('#akto').addEventListener('change',renderAkt);
$('#akall').addEventListener('click',function(){$('#akfrom').value='';$('#akto').value='';renderAkt()});
$('#akcopy').addEventListener('click',copyAkt);

