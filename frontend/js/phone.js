/* Phone numbers: one fixed format, +998-90-123-45-67. The person types only the digits after +998; separators appear by themselves.
   Any input marked data-phone gets this behaviour (customers, suppliers, workers, quick-add). */
var PHX={ph_bad:['Enter the full phone number: +998-XX-XXX-XX-XX.','Введите номер полностью: +998-XX-XXX-XX-XX.','Telefon raqamini to‘liq kiriting: +998-XX-XXX-XX-XX.']};
Object.keys(PHX).forEach(function(k){T.en[k]=PHX[k][0];T.ru[k]=PHX[k][1];T.uz[k]=PHX[k][2]});

var Phone={PRE:'+998-'};
/* the nine digits after +998, from whatever was typed or pasted (+998 90 123 45 67, 998901234567, 90-123-45-67, 8 90 123 45 67) */
Phone.local=function(s){
  var d=String(s||'').replace(/\D/g,'');
  if(d.indexOf('998')===0)return d.slice(3,12);
  if(d==='9'||d==='99')return '';                          /* the +998 prefix was being erased */
  return (d.length>9?d.slice(-9):d);
};
Phone.fmt=function(l){
  return Phone.PRE+l.slice(0,2)+(l.length>2?'-'+l.slice(2,5):'')+(l.length>5?'-'+l.slice(5,7):'')+(l.length>7?'-'+l.slice(7,9):'');
};
/* what to save: '' for an empty field, the formatted number when complete, null when it is half-typed */
Phone.out=function(v){
  var l=Phone.local(v);
  if(!l)return '';
  return l.length<9?null:Phone.fmt(l);
};
Phone.is=function(el){return !!(el&&el.getAttribute&&el.getAttribute('data-phone')!==null&&el.tagName==='INPUT')};
Phone.apply=function(el,keepCaret){
  var v=el.value,pos=el.selectionStart,intact=v.indexOf('+998')===0;
  var before=v.slice(0,pos==null?v.length:pos).replace(/\D/g,'');
  var cnt=Math.max(0,before.length-(intact?3:0)),l=Phone.local(v),s=Phone.fmt(l);
  if(el.value!==s)el.value=s;
  if(keepCaret&&el.setSelectionRange){
    var p=Phone.PRE.length,seen=0;
    while(seen<Math.min(cnt,l.length)&&p<s.length){if(/\d/.test(s.charAt(p)))seen++;p++}
    try{el.setSelectionRange(p,p)}catch(e){}
  }
};
document.addEventListener('focusin',function(e){
  var el=e.target;if(!Phone.is(el))return;
  Phone.apply(el,false);
  if(el.setSelectionRange){var n=el.value.length;try{el.setSelectionRange(n,n)}catch(x){}}
},true);
document.addEventListener('input',function(e){if(Phone.is(e.target))Phone.apply(e.target,true)},true);   /* capture: runs before the forms read the value */
document.addEventListener('focusout',function(e){
  var el=e.target;if(!Phone.is(el))return;
  if(!Phone.local(el.value))el.value='';
},true);
document.addEventListener('keydown',function(e){
  var el=e.target;if(!Phone.is(el)||e.key!=='Backspace')return;
  if(el.selectionStart===el.selectionEnd&&el.selectionStart<=Phone.PRE.length)e.preventDefault();         /* the prefix stays */
},true);
