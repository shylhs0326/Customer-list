(function(global){
  'use strict';
  const MAX_BYTES = 30 * 1024 * 1024;
  const MAX_ROWS = 100000;
  const MAX_COLS = 300;
  function assertFile(file){
    if(!file || typeof file.arrayBuffer !== 'function') throw new Error('엑셀 파일을 읽을 수 없습니다.');
    if(file.size > MAX_BYTES) throw new Error('파일당 최대 30MB까지 지원합니다.');
  }
  async function readBook(file){
    assertFile(file);
    const bytes = await file.arrayBuffer();
    const book = global.XLSX.read(bytes, {type:'array', cellDates:false, raw:false});
    return book;
  }
  function sheetRows(book, name){
    const sheet = book.Sheets[name];
    if(!sheet) throw new Error(`시트를 찾을 수 없습니다: ${name}`);
    const rows = global.XLSX.utils.sheet_to_json(sheet, {header:1, raw:false, defval:''});
    if(rows.length > MAX_ROWS + 30) throw new Error('시트당 최대 100,000행까지 지원합니다.');
    if(rows.some(row => row.length > MAX_COLS)) throw new Error('시트당 최대 300열까지 지원합니다.');
    return rows;
  }
  async function inspect(file){
    const book = await readBook(file);
    return {sheets: book.SheetNames.map(name => {
      const rows = sheetRows(book, name);
      return {name, rows: Math.max(0, rows.length - 1), preview: rows.slice(0, 30)};
    })};
  }
  async function readRows(file, options){
    const opts = options || {};
    const book = await readBook(file);
    const name = opts.sheet || book.SheetNames[0];
    const rows = sheetRows(book, name);
    const headerIndex = Math.max(1, Number(opts.header || 1)) - 1;
    const headers = (rows[headerIndex] || []).map((v,i) => String(v == null ? '' : v).trim() || `열${i+1}`);
    const values = rows.slice(headerIndex + 1);
    const result = values.filter(row => row.some(v => String(v ?? '').trim() !== '')).map((row, rowIndex) => {
      const item = {};
      headers.forEach((header, i) => { item[header] = String(row[i] ?? '').trim(); });
      item.__row = headerIndex + rowIndex + 2;
      if(opts.source) item.source = opts.source;
      return item;
    });
    return {headers, rows:result, sheet:name};
  }
  async function exportWorkbook(sheets){
    if(!Array.isArray(sheets) || !sheets.length) throw new Error('저장할 결과가 없습니다.');
    const book = global.XLSX.utils.book_new();
    sheets.forEach((entry, index) => {
      const name = String(entry.name || `Sheet${index+1}`).slice(0,31);
      const rows = Array.isArray(entry.rows) ? entry.rows : [];
      const ws = global.XLSX.utils.json_to_sheet(rows);
      global.XLSX.utils.book_append_sheet(book, ws, name || `Sheet${index+1}`);
    });
    const bytes = global.XLSX.write(book, {bookType:'xlsx', type:'array'});
    return new Blob([bytes], {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
  }
  global.XlsxAdapter = {MAX_BYTES, inspect, readRows, exportWorkbook};
  if(typeof module !== 'undefined') module.exports = global.XlsxAdapter;
})(typeof globalThis !== 'undefined' ? globalThis : window);
