import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';
const context={console,Blob,TextDecoder,TextEncoder,Uint8Array,ArrayBuffer,Date};vm.createContext(context);
vm.runInContext(await fs.readFile('web/vendor/xlsx.full.min.js','utf8'),context);
vm.runInContext(await fs.readFile('web/xlsx-adapter.js','utf8'),context);
vm.runInContext(await fs.readFile('web/core.js','utf8'),context);
const wb=context.XLSX.utils.book_new();const ws=context.XLSX.utils.aoa_to_sheet([
 ['기계번호','모델명','고객번호','고객사명','이름','전화','이메일','지역','현재 주소','직급','기입날짜'],
 ['M1','X','C1','테스트','홍길동','010-1111-2222','a@example.com','서울','서울 총무팀','대리','2026-01-01'],
 ['M2','Y','C2','제외사','김대표','010-3333-4444','b@example.com','부산','부산','대표','2026-02-01']
]);context.XLSX.utils.book_append_sheet(wb,ws,'자료');const bytes=context.XLSX.write(wb,{type:'array',bookType:'xlsx'});const file=new Blob([bytes]);
const parsed=await context.XlsxAdapter.readRows(file,{sheet:'자료',header:1});assert.equal(parsed.rows.length,2);
const records=parsed.rows.map(r=>({machine:r['기계번호'],model:r['모델명'],customer_id:r['고객번호'],company:r['고객사명'],name:r['이름'],phone:r['전화'],email:r['이메일'],region:r['지역'],address:r['현재 주소'],position:r['직급'],updated:r['기입날짜'],source:'자료1'}));
const result=context.CustomerCore.buildResult(records,['총무'],[{customer_id:'C2',company:'제외사',reason:'중복 조사'}]);assert.equal(result.customers.find(c=>c.customer_id==='C1').status,'설문 대상');assert.equal(result.customers.find(c=>c.customer_id==='C2').status,'설문 제외');
const out=await context.XlsxAdapter.exportWorkbook([{name:'설문 제외',rows:[{'고객명':'제외사','고객번호':'C2','제외사유':'중복 조사'}]}]);const outBytes=new Uint8Array(await out.arrayBuffer());const outBook=context.XLSX.read(outBytes,{type:'array'});const outRows=context.XLSX.utils.sheet_to_json(outBook.Sheets['설문 제외'],{header:1});assert.deepEqual(Array.from(outRows[0]),['고객명','고객번호','제외사유']);console.log('PASS browser flow');

