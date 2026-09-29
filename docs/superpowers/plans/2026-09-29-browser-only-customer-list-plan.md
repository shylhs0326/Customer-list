# 브라우저 전용 고객 리스트 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 고객 엑셀 데이터와 제외 대상 파일을 브라우저 안에서만 처리하는 정적 Vercel 배포본을 만든다.

**Architecture:** SheetJS를 정적 vendor 파일로 포함하고, 브라우저가 파일을 `ArrayBuffer`로 읽어 시트·행을 파싱한다. Python `core.py`의 선정 규칙을 순수 JavaScript 모듈로 이식해 결과를 메모리에서 만들고, SheetJS로 결과 XLSX Blob을 생성한다. Vercel은 `/api`와 세션 토큰 없이 `web/` 정적 파일만 제공한다.

**Tech Stack:** Vanilla JavaScript, SheetJS `xlsx`, existing HTML/CSS, Node test runner, Vercel static routes.

**Spec:** `docs/superpowers/specs/2026-09-29-browser-only-customer-list-design.md`

## Global Constraints

- 고객정보를 서버 API, 로그, analytics로 전송하지 않는다.
- 정식 배포물은 정적 HTML/CSS/JavaScript와 가상 예제 파일만 포함한다.
- 기존 주소 1순위, 대표·사장·실장·팀장 2순위, 최신 날짜, 전화·휴대폰, 성·이름, 고객번호 제외 규칙을 유지한다.
- 파일당 30MB, 시트당 100,000행, 300열 제한을 브라우저에서 검증한다.
- 새로고침·탭 종료 시 작업 상태가 사라진다는 안내를 유지한다.

## Review Focus

- 날짜 없는 행과 미래 날짜가 최신 선택을 잘못 바꾸지 않는지: 날짜 경계 테스트로 고정한다.
- 주소 1순위 후보의 연락처 누락을 2순위로 잘못 대체하지 않는지: 우선순위 테스트로 고정한다.
- 제외 파일의 고객명·고객번호·제외사유 열 순서가 바뀌어도 읽는지: 헤더 탐색 테스트로 고정한다.
- 4MB 파일은 처리하고 30MB 초과 파일은 차단하는지: 파일 크기 테스트로 고정한다.
- 저장 결과의 `설문 제외` 시트에 고객명·고객번호·제외사유가 들어가는지: XLSX export 테스트로 고정한다.

---

### Task 1: 브라우저 XLSX 어댑터와 정적 vendor 구성

**Files:**
- Create: `web/vendor/xlsx.full.min.js`
- Create: `web/xlsx-adapter.js`
- Create: `tests/test_xlsx_adapter.mjs`
- Modify: `web/index.html`

**Interfaces:**
- Produces `XlsxAdapter.inspect(file) -> {sheets:[{name,rows,preview}]}`.
- Produces `XlsxAdapter.readRows(file, {sheet, header}) -> {headers, rows}`.
- Produces `XlsxAdapter.exportWorkbook(sheets) -> Blob`.

- [ ] **Step 1: Write failing Node/browser-compatible adapter tests** for sheet preview, header row extraction, Korean date cells, and export Blob.
- [ ] **Step 2: Run `node tests/test_xlsx_adapter.mjs` and verify it fails because the adapter is absent.**
- [ ] **Step 3: Add a pinned SheetJS vendor file and implement the three adapter functions with ArrayBuffer input and Blob output.**
- [ ] **Step 4: Load `xlsx.full.min.js` before `xlsx-adapter.js` in `web/index.html`.**
- [ ] **Step 5: Run the adapter tests and verify PASS, then commit `feat: add browser xlsx adapter`.**

### Task 2: JavaScript customer selection core

**Files:**
- Create: `web/core.js`
- Create: `tests/test_core_browser.mjs`
- Modify: `web/app.js`

**Interfaces:**
- Produces `CustomerCore.buildResult(records, keywords, excludedTargets) -> result`.
- Produces `CustomerCore.approveCustomer(result, customerId, values) -> result`.
- Consumes normalized records with the existing field names and returns `customers`, `machines`, `records`, `rejected`, `keywords`, and `excluded_ids`.

- [ ] **Step 1: Port the existing priority, date, contact validation, name/phone split, machine grouping, exclusion status, and manual approval cases into failing `.mjs` tests.**
- [ ] **Step 2: Run `node tests/test_core_browser.mjs` and verify failures before implementation.**
- [ ] **Step 3: Implement pure browser functions with no DOM, network, storage, or server imports.**
- [ ] **Step 4: Run the browser core tests and compare representative results against the Python test fixtures.**
- [ ] **Step 5: Commit `feat: add browser customer selection core`.**

### Task 3: Replace API-driven UI with local browser state

**Files:**
- Modify: `web/app.js`
- Modify: `web/index.html`
- Modify: `web/style.css`
- Create: `tests/test_browser_flow.mjs`

**Interfaces:**
- File inputs call `XlsxAdapter.inspect` and retain parsed file objects only in `state.files`.
- Build calls `XlsxAdapter.readRows` and `CustomerCore.buildResult`.
- Review and exclude buttons mutate `state.result` through `CustomerCore.approveCustomer` and local exclusion logic.
- Export calls `XlsxAdapter.exportWorkbook` and downloads the returned Blob.

- [ ] **Step 1: Add failing flow tests for two source files, a three-column exclusion file, build counts, `설문 제외` filtering, and export sheet headers.**
- [ ] **Step 2: Run `node tests/test_browser_flow.mjs` and verify it fails while UI still calls `/api`.**
- [ ] **Step 3: Replace `api()` calls and base64 payloads with local adapter/core calls; preserve existing mapping controls, review dialog, filters, pagination, and messages.**
- [ ] **Step 4: Update metrics and labels so `설문 제외 대상` is the upload label and exported `설문 제외` sheet has 고객명·고객번호·제외사유.**
- [ ] **Step 5: Run the flow tests and commit `feat: process customer files in browser`.**

### Task 4: Static Vercel configuration and privacy guardrails

**Files:**
- Modify: `vercel.json`
- Modify: `web/index.html`
- Modify: `README.md`
- Create: `tests/test_static_deploy.mjs`
- Delete or leave unused: `api/index.py` only after static verification passes

**Interfaces:**
- `/` serves `web/index.html`; `/app.js`, `/core.js`, `/xlsx-adapter.js`, `/mapping.js`, `/style.css`, and vendor assets serve as static files.
- No `/api` route is referenced by the browser bundle.

- [ ] **Step 1: Add failing static checks that scan browser assets for `fetch('/api/`, session-token placeholders, and customer-data POST payloads.**
- [ ] **Step 2: Run the static checks and verify they fail against the current API-based UI.**
- [ ] **Step 3: Simplify `vercel.json` to static rewrites and remove session-token meta usage and API routes from the HTML bundle.**
- [ ] **Step 4: Add privacy text explaining browser-only processing and local-state lifetime.**
- [ ] **Step 5: Run static checks and commit `feat: make Vercel deployment static and private-by-design`.**

### Task 5: End-to-end verification and deployment

**Files:**
- Modify: `README.md` if run instructions need updating
- Test: `tests/test_*.py`, `tests/test_*.mjs`

- [ ] **Step 1: Run Python regression tests and all browser module tests.**
- [ ] **Step 2: Use the browser on a local static server to load virtual files, apply an exclusion workbook, build results, review a customer, and download XLSX.**
- [ ] **Step 3: Verify a 4MB file succeeds and a file over 30MB is rejected before parsing.**
- [ ] **Step 4: Inspect browser console and network activity; confirm no customer-data request leaves the browser.**
- [ ] **Step 5: Deploy the static artifact to Vercel Production, verify the production page and download flow, then commit any final documentation change.**

## Execution Order

Tasks 1–2 establish the parsing and business interfaces. Task 3 consumes both interfaces and replaces the UI request path. Task 4 removes the server boundary only after the browser path works. Task 5 is the final regression, privacy, and production verification gate.
