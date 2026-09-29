import assert from 'node:assert/strict';
import fs from 'node:fs';
const files=['web/index.html','web/app.js','web/core.js','web/xlsx-adapter.js','web/mapping.js'];
const source=files.map(f=>fs.readFileSync(f,'utf8')).join('\n');
assert.ok(!source.includes("fetch('/api/"));
assert.ok(!source.includes('X-Session-Token'));
assert.ok(!source.includes('__TOKEN__'));
assert.ok(!source.includes('base64'));
const config=JSON.parse(fs.readFileSync('vercel.json','utf8'));
assert.ok(!JSON.stringify(config).includes('/api'));
assert.ok(fs.existsSync('web/vendor/xlsx.full.min.js'));
assert.ok(fs.existsSync('web/sample1.xlsx')&&fs.existsSync('web/sample2.xlsx'));
console.log('PASS static deploy checks');

