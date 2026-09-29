import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const context={console, Date, Intl}; vm.createContext(context); vm.runInContext(fs.readFileSync('web/core.js','utf8'), context);
const core=context.CustomerCore; assert.ok(core);
const records=[
 {customer_id:'C1',company:'가나다',machine:'M1',model:'X',last_name:'김',first_name:'철수',name:'김철수',phone:'02-1234-5678',email:'c1@example.com',region:'서울',address:'서울 강남구 총무팀',position:'대리',updated:'2026-01-01',source:'자료1'},
 {customer_id:'C1',company:'가나다',machine:'M1',model:'X',last_name:'이',first_name:'영희',name:'이영희',phone:'010-1234-5678',email:'y@example.com',region:'서울',address:'부산',position:'팀장',updated:'2026-02-01',source:'자료2'},
 {customer_id:'C2',company:'다라마',machine:'M2',model:'Y',name:'박대표',phone:'010-2222-3333',email:'p@example.com',region:'부산',address:'부산',position:'대표',updated:'2026-03-01',source:'자료1'},
 {customer_id:'C3',company:'누락',machine:'M3',model:'Z',name:'',phone:'',email:'',region:'서울',address:'서울',position:'',updated:'2026-04-01',source:'자료1'}
];
const result=core.buildResult(records,['총무'],[{customer_id:'C2',company:'다라마',reason:'중복 제외'}]);
assert.equal(result.customers.length,3);
assert.equal(result.customers.find(c=>c.customer_id==='C1').name,'김철수');
assert.equal(result.customers.find(c=>c.customer_id==='C1').priority,1);
assert.equal(result.customers.find(c=>c.customer_id==='C2').status,'설문 제외');
assert.equal(result.customers.find(c=>c.customer_id==='C3').status,'확인 필요');
const approved=core.approveCustomer(result,'C3',{name:'최담당',phone:'010-4444-5555',email:'c3@example.com',address:'서울',position:'팀장',company:'누락',region:'서울',model:'Z'});
assert.equal(approved.status,'설문 대상');
console.log('PASS core');
