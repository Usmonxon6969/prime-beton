/* Voice input for the AI assistant and the "document from text" box, using the browser's own speech recognition.
   Nothing is sent to our server except the text you confirm; the browser vendor may process the audio. */
(function(){
'use strict';
var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
var X={vo_start:['Speak','Говорить','Gapirish'],vo_stop:['Stop','Стоп','To‘xtatish'],vo_listen:['Listening… tap to stop','Слушаю… нажмите, чтобы остановить','Tinglayapman… to‘xtatish uchun bosing'],
 vo_err:['Could not use the microphone. Allow access in the browser and try again.','Не удалось использовать микрофон. Разрешите доступ в браузере и повторите.','Mikrofondan foydalanib bo‘lmadi. Brauzerda ruxsat bering va qayta urinib ko‘ring.']};
Object.keys(X).forEach(function(k){T.en[k]=X[k][0];T.ru[k]=X[k][1];T.uz[k]=X[k][2]});
var LANG={uz:'uz-UZ',ru:'ru-RU',en:'en-US'};
var cur=null;
function stop(){if(cur){try{cur.rec.stop()}catch(e){}}}
function toggle(ta,btn){
  if(cur&&cur.ta===ta){stop();return}
  stop();
  var rec=new SR(),base=ta.value?ta.value.replace(/\s*$/,' '):'',fin='';
  rec.lang=LANG[lang]||'en-US';rec.interimResults=true;rec.continuous=true;
  rec.onresult=function(e){
    var interim='';
    for(var i=e.resultIndex;i<e.results.length;i++){var r=e.results[i];if(r.isFinal)fin+=r[0].transcript+' ';else interim+=r[0].transcript}
    ta.value=(base+fin+interim).trim();ta.dispatchEvent(new Event('input',{bubbles:true}));
  };
  rec.onerror=function(e){if(e.error==='not-allowed'||e.error==='service-not-allowed')toast(t('vo_err'),true)};
  rec.onend=function(){if(cur&&cur.rec===rec)cur=null;paint(btn,false)};
  cur={rec:rec,ta:ta};paint(btn,true);
  try{rec.start()}catch(e){cur=null;paint(btn,false)}
}
function paint(btn,on){
  btn.setAttribute('aria-pressed',String(on));btn.classList.toggle('rec',on);
  btn.textContent=t(on?'vo_stop':'vo_start');btn.title=t(on?'vo_listen':'vo_start');
}
function attach(){
  if(!SR)return;
  ['ai-in','dr-text'].forEach(function(id){
    var ta=document.getElementById(id);if(!ta||ta.dataset.mic)return;
    var bar=ta.parentElement.querySelector('.aibtns,.pbtns');if(!bar)return;
    ta.dataset.mic='1';
    var b=document.createElement('button');b.type='button';b.className='btn ghost sm mic';b.setAttribute('aria-pressed','false');paint(b,false);
    b.addEventListener('click',function(){toggle(ta,b)});
    bar.insertBefore(b,bar.firstChild);
  });
}
var tm=null;
new MutationObserver(function(){clearTimeout(tm);tm=setTimeout(attach,80)}).observe(document.querySelector('main'),{childList:true,subtree:true});
document.addEventListener('click',function(e){if(e.target.closest('[data-lang]'))setTimeout(function(){document.querySelectorAll('.mic').forEach(function(b){paint(b,b.classList.contains('rec'))})},0)});
attach();
})();
