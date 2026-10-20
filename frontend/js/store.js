/* Store: loads everything from the server and rebuilds the lists the pages read.
   The pages work with positions in these lists (WH[i], PRODUCTS[p], CUS[c] ...), so the lists are
   refilled in place, and the id of each server record is kept next to it (.id, WHID[i], PRID[p] ...). */
var WHID=[],PRID=[],MATID=[],UNID=[];
var WH_IDX={},PR_IDX={},MAT_IDX={},UN_IDX={},CU_IDX={},SU_IDX={},AC_IDX={};
var ITEM_NAME={};
function itemNameById(id){return ITEM_NAME[id]||''}
function refill(arr,list){arr.length=0;for(var i=0;i<list.length;i++)arr.push(list[i])}
function clearObj(o){Object.keys(o).forEach(function(k){delete o[k]})}
function byDateDesc(a,b){return (b.date-a.date)||(b.id-a.id)}

var Store={busy:null,again:false,demo:false};

Store.fetchAll=function(){
  function get(p){return api('GET',p).catch(function(e){if(e.status===403)return null;throw e})}
  return Promise.all([
    get('/units'),get('/warehouses'),get('/items'),get('/specifications'),get('/customers'),get('/suppliers'),
    get('/orders'),get('/invoices'),get('/receipts'),get('/production'),get('/accounts'),
    get('/finance?kind=bank'),get('/finance?kind=cash'),get('/crew-workers')
  ]).then(function(r){
    return {units:r[0]||[],whs:r[1]||[],items:r[2]||[],specs:r[3]||{},cus:r[4]||[],sup:r[5]||[],ord:r[6]||[],inv:r[7]||[],
      rec:r[8]||[],prod:r[9]||[],acc:r[10]||[],fin:(r[11]||[]).concat(r[12]||[]),workers:r[13]||[]};
  });
};

Store.build=function(d){
  var i;
  /* units */
  clearObj(UN_IDX);UNID.length=0;
  refill(UNITS,d.units.map(function(u,k){UN_IDX[u.id]=k;UNID[k]=u.id;return {id:u.id,n:{uz:u.name,ru:u.name_ru||u.name,en:u.name_en||u.name}}}));
  /* warehouses: workshops first, then the other stores */
  var ws=d.whs.filter(function(w){return w.is_workshop}),others=d.whs.filter(function(w){return !w.is_workshop}),all=ws.concat(others);
  clearObj(WH_IDX);WHID.length=0;
  refill(WH,all.map(function(w,k){WH_IDX[w.id]=k;WHID[k]=w.id;return w.name}));
  refill(SITES,ws.map(function(w){return w.name}));
  WHGONE.length=0;
  /* materials and products */
  var mats=d.items.filter(function(x){return x.kind==='material'}),prods=d.items.filter(function(x){return x.kind==='product'});
  clearObj(MAT_IDX);clearObj(PR_IDX);clearObj(ITEM_NAME);MATID.length=0;PRID.length=0;PGONE.length=0;
  refill(MATS,mats.map(function(m,j){MAT_IDX[m.id]=j;MATID[j]=m.id;ITEM_NAME[m.id]=m['name_'+lang]||m.name_en;return {id:m.id,names:{uz:m.name_uz,ru:m.name_ru,en:m.name_en}}}));
  refill(PRODUCTS,prods.map(function(p,k){PR_IDX[p.id]=k;PRID[k]=p.id;ITEM_NAME[p.id]=p.name_uz;return p.name_uz}));
  refill(NORMS,prods.map(function(p){
    var sp=d.specs[p.id]||{};
    return mats.map(function(m){return +(sp[m.id]||0)});
  }));
  refill(DEF_NORMS,NORMS.map(function(a){return a.slice()}));
  if(specSel<0||specSel>=PRODUCTS.length)specSel=0;
  if(typeof loadDraft==='function')loadDraft();
  /* stock table */
  function stock(x){return WHID.map(function(id){return +((x.stock||{})[id]||0)})}
  clearObj(ITEM_BY);clearObj(MAT_BY);
  var items=[];
  prods.forEach(function(p,k){var it={id:p.id,n:p.name_uz,fg:1,min:+p.min_stock,st:stock(p),u:UN_IDX[p.unit_id]};recalcItem(it);ITEM_BY[it.n]=it;items.push(it)});
  mats.forEach(function(m,j){var it={id:m.id,m:j,fg:0,min:+m.min_stock,st:stock(m),u:UN_IDX[m.unit_id]};recalcItem(it);MAT_BY[j]=it;items.push(it)});
  refill(ITEMS,items);
  /* partners */
  clearObj(CU_IDX);clearObj(SU_IDX);
  refill(CUS,d.cus.map(function(c,k){CU_IDX[c.id]=k;return {id:c.id,n:c.name,ph:c.phone||'',ct:c.contact||'',pd:c.pay_days||0}}));
  refill(SUP,d.sup.map(function(c,k){SU_IDX[c.id]=k;return {id:c.id,n:c.name,ph:c.phone||'',ct:c.contact||''}}));
  /* money accounts */
  clearObj(AC_IDX);
  refill(ACC,d.acc.map(function(a,k){AC_IDX[a.id]=k;return {id:a.id,t:a.kind,n:{uz:a.name_uz,ru:a.name_ru,en:a.name_en},open:+a.opening_balance,num:a.number||'',bal:+a.balance}}));
  /* documents */
  function prow(r){return {p:PR_IDX[r.item_id],q:+r.qty,pr:+r.price}}
  var ordNo={};d.ord.forEach(function(o){ordNo[o.id]=o.number});
  refill(ORD,d.ord.map(function(o){return {id:o.id,no:o.number,date:fromIso(o.date),adv:+o.advance||0,due:fromIso(o.due_date),cus:CU_IDX[o.customer_id],rows:o.rows.map(prow),comment:o.comment||'',status:o.status==='deleted'?'deleted':'open'}}).sort(byDateDesc));
  refill(INV,d.inv.map(function(v){return {id:v.id,no:v.number,date:fromIso(v.date),cus:CU_IDX[v.customer_id],pay:fromIso(v.pay_due),ord:v.order_id?(ordNo[v.order_id]||''):'',site:WH_IDX[v.warehouse_id],rows:v.rows.map(prow),comment:v.comment||'',driver:v.driver||'',vehicle:v.vehicle||'',status:v.status}}).sort(byDateDesc));
  refill(REC,d.rec.map(function(v){return {id:v.id,no:v.number,date:fromIso(v.date),sup:SU_IDX[v.supplier_id],site:WH_IDX[v.warehouse_id],comment:v.comment||'',status:v.status,
    rows:v.rows.map(function(r){var m=MAT_IDX[r.item_id],p=PR_IDX[r.item_id];return {m:m!=null?m:-1,p:p!=null?p:-1,q:+r.qty,pr:+r.price}})}}).sort(byDateDesc));
  refill(WORKERS,(d.workers||[]).map(function(w){return {id:w.id,name:w.name}}));
  refill(plog,d.prod.map(function(v){
    var mm=MATS.map(function(){return 0});
    v.consumption.forEach(function(c){var j=MAT_IDX[c.material_id];if(j!=null)mm[j]+=+c.qty});
    return {id:v.id,no:v.number,date:fromIso(v.date),site:WH_IDX[v.warehouse_id],status:v.status,comment:v.comment||'',rows:v.rows.map(function(r){return {p:PR_IDX[r.item_id],q:+r.qty,s:+r.scrap||0}}),crew:v.worker_ids||[],mats:mm};
  }).sort(byDateDesc));
  refill(FIN,d.fin.filter(function(f){return AC_IDX[f.account_id]!=null&&(f.to_account_id==null||AC_IDX[f.to_account_id]!=null)}).map(function(f){return {id:f.id,no:f.number,date:fromIso(f.date),kind:f.kind,acc:AC_IDX[f.account_id],to:f.to_account_id!=null?AC_IDX[f.to_account_id]:null,
    oid:f.order_id||null,wid:f.worker_id||null,art:f.article,cus:f.customer_id!=null?CU_IDX[f.customer_id]:-1,sup:f.supplier_id!=null?SU_IDX[f.supplier_id]:-1,party:f.party||'',amt:+f.amount,comment:f.comment||'',status:f.status}}).sort(byDateDesc));
};

/* one load at a time; a request that arrives while loading triggers one more pass */
Store.load=function(){
  if(!ME)return Promise.resolve();
  if(Store.busy){Store.again=true;return Store.busy}
  Store.busy=Store.fetchAll().then(function(d){
    Store.build(d);Store.paint();
  }).then(function(){
    Store.busy=null;
    if(Store.again){Store.again=false;return Store.load()}
  },function(e){Store.busy=null;Store.again=false;throw e});
  return Store.busy;
};

/* redraw every data page after the lists changed */
Store.paint=function(){
  var f=[renderWh,renderItems,renderSpecs,renderMatPage,renderCus,renderSup,renderOrders,renderInvs,renderRecs,renderFin,renderSet,renderLog,renderDash,renderBiz,bellUpdate,renderAkt];
  f.forEach(function(fn){try{fn()}catch(e){if(window.console)console.error(e)}});
};
