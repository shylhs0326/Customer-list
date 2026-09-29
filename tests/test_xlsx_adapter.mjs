import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';
const root = process.cwd();
const xlsxCode = await fs.readFile(path.join(root,'web/vendor/xlsx.full.min.js'),'utf8');
const adapterCode = await fs.readFile(path.join(root,'web/xlsx-adapter.js'),'utf8');
const context = { console, Blob, TextDecoder, TextEncoder, Uint8Array, ArrayBuffer, setTimeout };
vm.createContext(context);
vm.runInContext(xlsxCode, context);
vm.runInContext(adapterCode, context);
assert.ok(context.XlsxAdapter, 'adapter should be available');
const wb = context.XLSX.utils.book_new();
const ws = context.XLSX.utils.aoa_to_sheet([
  ['기계번호','고객번호','고객사명','기입날짜'],
  ['M-1','C-1','테스트','2026-01-02'],
]);
context.XLSX.utils.book_append_sheet(wb, ws, '자료');
const bytes = context.XLSX.write(wb, {type:'array', bookType:'xlsx'});
const file = new Blob([bytes], {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
file.name = '자료1.xlsx';
const info = await context.XlsxAdapter.inspect(file);
assert.equal(info.sheets[0].name, '자료');
assert.equal(info.sheets[0].preview[1][1], 'C-1');
const parsed = await context.XlsxAdapter.readRows(file, {sheet:'자료', header:1});
assert.equal(parsed.headers[0], '기계번호');
assert.equal(parsed.rows[0]['고객번호'], 'C-1');
const out = await context.XlsxAdapter.exportWorkbook([{name:'설문 대상', rows:[{고객번호:'C-1'}]}]);
assert.ok(out.size > 0);
console.log('PASS adapter');

