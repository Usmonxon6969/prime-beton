/* Live updates: the server says "something changed" and this page reloads its lists (Server-Sent Events).
   A fetch stream is used instead of EventSource so the sign-in token travels in a header, not in the address. */
var Live={ctl:null,tm:null,t:null,fails:0,on:false,had:false,pend:false};

Live.start=function(){
  if(Live.on)return;
  Live.on=true;Live.fails=0;Live.had=false;Live.open();
};
Live.stop=function(){
  Live.on=false;Live.pend=false;clearTimeout(Live.tm);clearTimeout(Live.t);
  if(Live.ctl){try{Live.ctl.abort()}catch(e){}Live.ctl=null}
  document.body.removeAttribute('data-live');
};
Live.open=function(){
  if(!Live.on)return;
  if(!API.token){Live.tm=setTimeout(Live.open,500);return}
  if(/^demo\./.test(API.token)){Live.on=false;return}                 /* the offline demo has no server */
  if(typeof AbortController==='undefined'||!window.ReadableStream){Live.on=false;return}
  var ctl=new AbortController();Live.ctl=ctl;
  fetch(API.base+'/events',{headers:{Authorization:'Bearer '+API.token,Accept:'text/event-stream'},signal:ctl.signal,cache:'no-store'}).then(function(r){
    if(r.status===401||r.status===403){Live.on=false;return}            /* signed out: the normal calls deal with it */
    if(!r.ok||!r.body)throw new Error('live');
    Live.fails=0;document.body.setAttribute('data-live','1');
    if(Live.had)Live.changed();                                          /* the line dropped for a while: catch up once */
    Live.had=true;
    var rd=r.body.getReader(),dec=new TextDecoder(),buf='';
    function pump(){
      return rd.read().then(function(x){
        if(x.done)throw new Error('live');
        buf+=dec.decode(x.value,{stream:true}).replace(/\r/g,'');
        var parts=buf.split('\n\n');buf=parts.pop();
        parts.forEach(Live.msg);
        return pump();
      });
    }
    return pump();
  }).catch(function(){}).then(function(){
    document.body.removeAttribute('data-live');
    if(Live.ctl===ctl)Live.ctl=null;
    if(!Live.on)return;
    Live.tm=setTimeout(Live.open,Math.min(30000,1000*Math.pow(2,Live.fails++)));
  });
};
Live.msg=function(block){
  var ev='message';
  block.split('\n').forEach(function(l){if(l.indexOf('event:')===0)ev=l.slice(6).trim()});
  if(ev==='changed')Live.changed();
  else if(ev==='bye'){Live.on=false;if(Live.ctl){try{Live.ctl.abort()}catch(e){}}}
};
/* several changes in a row make one reload */
Live.changed=function(){clearTimeout(Live.t);Live.t=setTimeout(Live.refresh,300)};
/* "editing" = a field in the page has the cursor AND something was typed or chosen in the last minute.
   A field that was only clicked and then left alone must not freeze the page for ever. */
Live.lastInput=0;
['input','change','keydown'].forEach(function(n){document.addEventListener(n,function(){Live.lastInput=Date.now()},true)});
Live.editing=function(){
  var a=document.activeElement;
  return !!(a&&/^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)&&a.closest('main,[role=dialog],.modal')&&Date.now()-Live.lastInput<60000);
};
/* pages that load their own data (reports, journal, pay statement) refresh after the store */
Live.extra=function(){['repRefresh','audRefresh','payRefresh'].forEach(function(n){try{if(window[n])window[n]()}catch(e){if(window.console)console.error(e)}})};
Live.refresh=function(){
  if(!Live.on||!ME)return;
  if(document.hidden){Live.pend=true;return}                             /* a hidden tab reloads when it is shown again */
  if(Live.editing()){Live.t=setTimeout(Live.refresh,3000);return}        /* never redraw under someone who is typing */
  Live.pend=false;
  Store.load().then(Live.extra,function(){});
};
document.addEventListener('visibilitychange',function(){if(!document.hidden&&Live.pend)Live.changed()});

/* follow the sign-in */
(function(){
  var was=setMe,gone=sessionExpired;
  setMe=function(u){was(u);if(u)Live.start();else Live.stop()};
  sessionExpired=function(){Live.stop();gone()};
})();
