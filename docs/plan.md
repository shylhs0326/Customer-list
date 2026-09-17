# 구현 계획

목표: 두 엑셀을 연결하고 검토한 뒤 고객번호당 1명의 설문 목록을 저장한다.

- [x] 통합 규칙 테스트 작성: 중복 기계, 최신 담당자, 최신 행 누락, 날짜 충돌, 권한 없음, 고객번호 누락, 수동 확인 검증.
- [x] core.py 구현: build_result(records, keywords), approve_customer(result, customer_id, values).
- [x] Excel 경계 테스트 작성: 숫자 표시 형식, 제목 행, 열 연결, 수식 캐시 누락, 출력 문자열 안전성.
- [x] excel_io.py 구현: inspect_book(bytes), read_records(bytes, sheet, header_row, mapping, source), export_result(result).
- [x] app.py와 web 화면 구현: 두 파일 업로드, 연결 설정, 결과 필터, 고객 검토, 다운로드. 변경된 입력은 기존 결과를 무효화한다.
- [x] 실행 스크립트, 가상 예제, 한국어 사용 설명서 제공.
- [x] 전체 단위·통합 테스트와 실제 브라우저 흐름 확인.

검증: 자동 테스트 22개. 브라우저에서 가상 파일 두 개의 열 자동 연결 → 고객 4명(대상 2, 검토 2) → 수동 확인 후 대상 3명 반영 확인. 저장 파일은 HTTP 통합 테스트로 다시 열어 시트, 고객 수, 앞자리 0 및 기계 쌍을 검증했다. 실제 고객 데이터와 100,000행 규모 성능 검증은 수행하지 않았다.
