'use strict';
const {fields, autoMapping, chooseHeader, dateLabel} = FieldMapping;
const state = {files:{},result:null,filter:'전체',page:0,busy:false,customer:null,recordId:null};
const $ = id => document.getElementById(id);
const confirmation = document.querySelector('#confirm')?.parentElement;
if (confirmation) confirmation.lastChild.textContent = ' 이 담당자의 직급과 위 정보가 최신임을 확인했습니다.';
function el(tag, text, className) { const node = document.createElement(tag); if(text!==undefined) node.textContent=text; if(className)node.className=className; return node; }
function message(text) { $('message').textContent=text; $('message').hidden=!text; }
async function api(path, payload, blob=false) {
  const res=await fetch('/api/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-Session-Token':document.querySelector('meta[name=session-token]').content},body:JSON.stringify(payload)});
  if(!res.ok) {const error=await res.json(); throw new Error(error.error || '요청을 처리하지 못했습니다.');}
  return blob?res.blob():res.json();
}
async function busy(work) {
  if(state.busy)return;
  state.busy=true; message('자료를 처리하고 있습니다…'); document.querySelectorAll('button,input,select').forEach(n=>n.disabled=true);
  try {await work(); message('');}catch(e){message(e.message);}finally{state.busy=false;document.querySelectorAll('button,input,select').forEach(n=>n.disabled=false);}
}
function invalidate(){state.result=null;$('results').hidden=true;$('empty').hidden=false;}
function initializeFile(slot, data, name) {
  const sheet=data.sheets[0];const header=chooseHeader(sheet, slot);
  state.files[slot]={...data,name,sheet:sheet.name,header,mapping:autoMapping(sheet.preview[header-1]||[], slot)};
  renderFiles();
}
function renderFiles() {
  $('files').replaceChildren();
  ['1','2'].forEach(slot=>{
    const file=state.files[slot], card=el('article',undefined,'file-card'),head=el('div',undefined,'file-head');
    head.append(el('b','자료 '+slot),el('p',file?file.name:'프로그램에서 내려받은 엑셀 파일'));
    const picker=el('input');picker.type='file';picker.accept='.xlsx,.xlsm';picker.setAttribute('aria-label','자료 '+slot+' 엑셀 파일');
    picker.onchange=()=>busy(async()=>{
      const input=picker.files[0];if(!input)return;invalidate();delete state.files[slot];
      if(input.size>30*1024*1024)throw new Error('파일당 최대 30MB까지 지원합니다.');
      const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=()=>reject(new Error('파일을 읽지 못했습니다.'));reader.readAsDataURL(input);});
      try{const info=await api('inspect',{slot,name:input.name,data});initializeFile(slot,info,input.name);}finally{renderFiles();}
    });
    head.append(picker);card.append(head);
    if(!file){card.append(el('div','파일을 선택하면 시트와 열 연결 항목이 나타납니다.','unloaded'));}
    else{
      const mapping=el('div',undefined,'mapping'),options=el('div',undefined,'sheet-options');
      const sheetLabel=el('label','사용할 시트'),select=el('select');select.setAttribute('aria-label','자료 '+slot+' 시트');
      file.sheets.forEach(s=>{const option=el('option',s.name);option.value=s.name;select.append(option);});select.value=file.sheet;
      select.onchange=()=>{file.sheet=select.value;const s=file.sheets.find(s=>s.name===file.sheet);file.header=chooseHeader(s, slot);file.mapping=autoMapping(s.preview[file.header-1]||[], slot);invalidate();renderFiles();};
      sheetLabel.append(select);const headerLabel=el('label','제목 행'),header=el('input');header.type='number';header.min=1;header.max=30;header.value=file.header;header.setAttribute('aria-label','자료 '+slot+' 제목 행');
      header.onchange=()=>{file.header=Math.max(1,Math.min(30,parseInt(header.value)||1));const s=file.sheets.find(s=>s.name===file.sheet);file.mapping=autoMapping(s.preview[file.header-1]||[], slot);invalidate();renderFiles();};headerLabel.append(header);options.append(sheetLabel,headerLabel);
      mapping.append(options,el('p','항목 이름이 같으면 자동 연결됩니다. 반드시 원본 열을 확인하세요.','mapping-hint'));
      const grid=el('div',undefined,'map-grid'),sheet=file.sheets.find(s=>s.name===file.sheet),headers=sheet.preview[file.header-1]||[];
      Object.entries(fields).forEach(([key,baseLabel])=>{
        const label=key==='updated'?dateLabel(slot)+' (최신 비교 기준)':baseLabel;
        const wrap=el('label',label+(key==='customer_id'?' *':'')),input=el('select');input.setAttribute('aria-label','자료 '+slot+' '+label);
        const none=el('option','연결 안 함');none.value='';input.append(none);
        headers.forEach((h,index)=>{const option=el('option',`${index+1}열 · ${h||'(제목 없음)'}`);option.value=String(index);input.append(option);});input.value=file.mapping[key]===null?'':String(file.mapping[key]);
        input.onchange=()=>{file.mapping[key]=input.value===''?null:Number(input.value);invalidate();};wrap.append(input);grid.append(wrap);
      });mapping.append(grid);card.append(mapping);
    }
    $('files').append(card);
  });
}
function renderResults() {
  const result=state.result;if(!result)return;
  $('results').hidden=false;$('empty').hidden=true;
  $('total').textContent=result.customers.length;
  const ready=result.customers.filter(c=>c.status==='설문 대상').length;
  $('ready').textContent=ready;$('review').textContent=result.customers.length-ready;$('rejected').textContent=result.rejected.length;
  const query=$('search').value.toLowerCase();
  const filtered=result.customers.filter(c=>(state.filter==='전체'||c.status===state.filter)&&[c.customer_id,c.company,c.name].join(' ').toLowerCase().includes(query));
  state.page=Math.min(state.page,Math.max(0,Math.ceil(filtered.length/50)-1));
  $('rows').replaceChildren();
  filtered.slice(state.page*50,(state.page+1)*50).forEach(c=>{
    const row=el('tr'),status=el('td');status.append(el('span',c.status,'badge'+(c.status==='확인 필요'?' review':'')));status.append(el('small',c.priority < 3 ? c.priority+'순위' : '확인 필요'));row.append(status);
    [[c.customer_id,c.company],[[c.name||'담당자 미확인',c.position].filter(Boolean).join(' · '),c.address],[['전화: '+(c.phone||'—'),'휴대폰: '+(c.mobile||'—')].join(' / '),c.email||'이메일 없음']].forEach(values=>{const td=el('td',values[0]);td.append(el('small',values[1]));td.className='contact-detail';row.append(td);});
    row.append(el('td',String(c.machine?c.machine.split('\n').length:0)),el('td',c.region||'—'),el('td',c.reasons.join(' / ')||(c.manual?'사용자 확인 완료':'최신 정보 기준 선정'),'reason'));
    const action=el('td'),button=el('button','검토','secondary');button.onclick=()=>openReview(c);action.append(button);row.append(action);$('rows').append(row);
  });
  if(!filtered.length){const row=el('tr'),td=el('td','조건에 맞는 고객이 없습니다.');td.colSpan=8;row.append(td);$('rows').append(row);}
  $('page-info').textContent=`${filtered.length}명 · ${state.page+1} / ${Math.max(1,Math.ceil(filtered.length/50))} 페이지`;
  $('rejected-note').textContent=result.rejected.length?`고객번호가 없는 ${result.rejected.length}개 원본 행은 연결하지 않았습니다. 저장 파일의 ‘확인 필요’ 시트에서 원본 위치를 확인하세요.`:'';
}
const editKeys=['company','last_name','first_name','phone','mobile','email','region','address','position'];
function fillReview(c){editKeys.forEach(k=>$('edit-'+k).value=c[k]||'');$('confirm').checked=false;}
function openReview(c){
  state.customer=c;state.recordId=null;$('dialog-title').textContent=`${c.company||'고객사 미확인'} · ${c.customer_id}`;
  $('dialog-reasons').textContent=c.reasons.join('\n')||'선정된 담당자와 연락처를 확인하세요.';$('dialog-error').textContent='';
  $('candidate').replaceChildren();const current=el('option','현재 선정 정보');current.value='';$('candidate').append(current);
  c.candidates.forEach(r=>{const option=el('option',`${r.name||'이름 없음'} · ${r.position||'직급 없음'} · ${r.address||'현재 주소 없음'} · ${r.updated||'날짜 없음'} · ${r.email||'이메일 없음'}`);option.value=r.record_id;$('candidate').append(option);});
  $('edit-fields').replaceChildren();editKeys.forEach(k=>{const label=el('label',fields[k]),input=el('input');input.id='edit-'+k;input.setAttribute('aria-label','확인 '+fields[k]);label.append(input);$('edit-fields').append(label);});
  fillReview(c);$('candidate-source').textContent=c.source;$('review-dialog').showModal();
}
$('candidate').onchange=()=>{const id=$('candidate').value;state.recordId=id===''?null:Number(id);const row=state.customer.candidates.find(r=>r.record_id===state.recordId)||state.customer;fillReview({...state.customer,...row});$('candidate-source').textContent=row.source;};
$('close-dialog').onclick=()=>$('review-dialog').close();
$('review-form').onsubmit=async event=>{
  event.preventDefault();$('dialog-error').textContent='';
  if(!$('confirm').checked){$('dialog-error').textContent='최신 정보와 담당자 직급을 확인한 뒤 체크해 주세요.';return;}
  const values=Object.fromEntries(editKeys.map(k=>[k,$('edit-'+k).value]));
  await busy(async()=>{try{state.result=await api('approve',{customer_id:state.customer.customer_id,record_id:state.recordId,values,confirmed:true});$('review-dialog').close();renderResults();}catch(e){$('dialog-error').textContent=e.message;throw e;}});
};
$('exclude').onclick=()=>busy(async()=>{state.result=await api('exclude',{customer_id:state.customer.customer_id});$('review-dialog').close();renderResults();});
$('demo').onclick=()=>busy(async()=>{invalidate();const files=await api('demo',{});files.forEach(f=>initializeFile(f.slot,f,f.name));});
$('build').onclick=()=>busy(async()=>{
  invalidate();if(Object.keys(state.files).length!==2)throw new Error('엑셀 파일 2개를 먼저 선택해 주세요.');
  const inputs=Object.entries(state.files).map(([slot,f])=>({slot,sheet:f.sheet,header:f.header,mapping:f.mapping}));
  state.result=await api('build',{inputs,keywords:$('keywords').value.split(',').map(s=>s.trim()).filter(Boolean)});state.page=0;renderResults();$('results').scrollIntoView({behavior:'smooth',block:'start'});
});
$('keywords').oninput=invalidate;
$('export').onclick=()=>busy(async()=>{const blob=await api('export',{result:state.result},true),url=URL.createObjectURL(blob),anchor=el('a');anchor.href=url;anchor.download=`설문대상_고객리스트_${new Date().toLocaleDateString('sv-SE')}.xlsx`;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),10000);});
document.querySelectorAll('[data-filter]').forEach(button=>button.onclick=()=>{state.filter=button.dataset.filter;state.page=0;document.querySelectorAll('[data-filter]').forEach(b=>b.classList.toggle('active',b===button));renderResults();});
$('search').oninput=()=>{state.page=0;renderResults();};$('prev').onclick=()=>{state.page=Math.max(0,state.page-1);renderResults();};$('next').onclick=()=>{state.page++;renderResults();};
window.addEventListener('beforeunload',event=>{if(state.result){event.preventDefault();event.returnValue='';}});
renderFiles();
