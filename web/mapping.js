'use strict';
const FieldMapping = (()=>{
const fields = {machine:'기계번호',model:'모델명',customer_id:'고객번호',company:'고객사명',last_name:'성',first_name:'이름',phone:'전화',mobile:'휴대폰',email:'이메일',region:'지역',address:'현재 주소',position:'직급',updated:'정보수정일'};
const aliases = {machine:['기계번호','제조번호','시리얼번호','serial','serialnumber','sn'],model:['모델명','모델','기종','model'],customer_id:['고객번호','고객코드','거래처코드','customerno','customerid'],company:['고객사명','고객명','회사명','업체명','거래처명'],last_name:['성','Last Name','Surname','Family Name'],first_name:['이름','First Name','Given Name'],phone:['전화','전화번호','유선전화','Telephone','Phone','연락처','담당자연락처'],mobile:['휴대폰','휴대전화','휴대폰번호','핸드폰','Mobile','Mobile Phone','Cell Phone'],email:['이메일','이메일주소','메일','email','e-mail'],region:['지역','시도','소재지역'],address:['현재 주소','현재주소','주소','설치주소','소재지','address'],position:['직급','담당자직급','직급명','직위','position','jobtitle'],updated:['정보수정일','수정일','수정일자','최종수정일','갱신일','확인일','updatedat']};
const dateAliases = {'1':['기입날짜','기입일','기입일자'], '2':['Install Date','설치날짜','설치일','설치일자']};
const dateLabel = slot => String(slot)==='1'?'기입날짜':'Install Date';
const norm=s=>String(s||'').toLowerCase().replace(/[\s_\-()]/g,'');
function autoMapping(headers, slot) {
  const used=new Set(), mapping={};
  Object.keys(fields).forEach(key=>{
    const names=key==='updated'?dateAliases[String(slot)]||[]:aliases[key];
    let i=-1;
    for(const name of names){i=headers.findIndex((h,j)=>!used.has(j)&&norm(name)===norm(h));if(i>=0)break;}
    mapping[key]=i<0?null:i;if(i>=0)used.add(i);
  });
  return mapping;
}
function chooseHeader(sheet, slot) {let best=0,score=-1;sheet.preview.forEach((r,i)=>{const n=Object.values(autoMapping(r, slot)).filter(v=>v!==null).length;if(n>score){score=n;best=i;}});return best+1;}
return {fields, autoMapping, chooseHeader, dateLabel};
})();
if(typeof module !== 'undefined') module.exports = FieldMapping;
