const assert = require('node:assert/strict');
const {autoMapping, chooseHeader, dateLabel} = require('../web/mapping.js');
const both=['고객번호','정보수정일','설치날짜','기입날짜'];
assert.equal(autoMapping(both, '1').updated, 3);
assert.equal(autoMapping(both, '2').updated, 2);
assert.equal(autoMapping(['고객번호','설치날짜'], '1').updated, null);
assert.equal(autoMapping(['고객번호','기입날짜'], '2').updated, null);
assert.equal(autoMapping(['고객번호','기입 일자'], '1').updated, 1);
assert.equal(autoMapping(['고객번호','설치일'], '2').updated, 1);
assert.equal(chooseHeader({preview:[['자료'],['고객번호','설치날짜']]}, '2'), 2);
assert.equal(dateLabel('1'), '기입날짜');
assert.equal(dateLabel('2'), 'Install Date');
assert.equal(autoMapping(['고객번호','Install Date'], '2').updated, 1);
assert.equal(autoMapping(['고객번호','install_date'], '2').updated, 1);
assert.equal(autoMapping(['고객번호','설치날짜','Install Date'], '2').updated, 2);
assert.equal(autoMapping(['고객번호','Install Date'], '1').updated, null);
for(const slot of ['1','2']) {
  assert.equal(autoMapping(['Last Name','First Name'], slot).last_name, 0);
  assert.equal(autoMapping(['Last Name','First Name'], slot).first_name, 1);
  assert.equal(autoMapping(['성','이름'], slot).last_name, 0);
  assert.equal(autoMapping(['성','이름'], slot).first_name, 1);
  assert.equal(autoMapping(['성명'], slot).first_name, null);
}
console.log('Mapping: 23 assertions passed');
