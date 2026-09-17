"""Run locally: python app.py. Only listens on 127.0.0.1."""
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from pathlib import Path
import secrets
import threading
import webbrowser
import argparse
from core import build_result, approve_customer
from excel_io import inspect_book, read_records, export_result, sample_book

ROOT = Path(__file__).resolve().parent


class SurveyServer(HTTPServer):
    def __init__(self, address):
        super().__init__(address, Handler)
        self.token = secrets.token_urlsafe(32)
        self.files = {}
        self.result = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # No customer details written to logs.

    def send(self, data, kind='application/json; charset=utf-8', status=200, filename=None):
        if not isinstance(data, bytes):
            data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        if filename:
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data)

    def valid_host(self):
        return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

    def do_GET(self):
        if not self.valid_host():
            return self.send({'error': '접속 주소를 확인해 주세요.'}, status=403)
        path = self.path.split('?')[0]
        if path == '/':
            page = (ROOT / 'web' / 'index.html').read_text(encoding='utf-8')
            return self.send(page.replace('__TOKEN__', self.server.token).encode(), 'text/html; charset=utf-8')
        if path in ('/app.js', '/mapping.js', '/style.css'):
            return self.send((ROOT / 'web' / path[1:]).read_bytes(), 'text/javascript; charset=utf-8' if path.endswith('.js') else 'text/css; charset=utf-8')
        if path in ('/sample1.xlsx', '/sample2.xlsx'):
            return self.send(sample_book(int(path[7])), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=path[1:])
        return self.send({'error': '페이지가 없습니다.'}, status=404)

    def do_POST(self):
        if not self.valid_host() or self.headers.get('X-Session-Token') != self.server.token:
            return self.send({'error': '프로그램 화면을 새로 열어 주세요.'}, status=403)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 42 * 1024 * 1024:
                raise ValueError('요청 크기가 너무 큽니다. 파일당 30MB 이하로 선택해 주세요.')
            payload = json.loads(self.rfile.read(length))
            if self.path == '/api/inspect':
                slot = str(payload['slot'])
                if slot not in ('1', '2'):
                    raise ValueError('파일 위치 오류')
                self.server.result = None
                self.server.files.pop(slot, None)
                name = Path(payload['name']).name
                if not name.lower().endswith(('.xlsx', '.xlsm')):
                    raise ValueError('.xlsx 또는 .xlsm 파일만 지원합니다. .xls는 Excel에서 .xlsx로 저장해 주세요.')
                data = base64.b64decode(payload['data'], validate=True)
                info = inspect_book(data)
                self.server.files[slot] = (name, data)
                return self.send(info)
            if self.path == '/api/demo':
                self.server.result = None
                response = []
                for slot in ('1', '2'):
                    name, data = f'가상예제_{slot}.xlsx', sample_book(int(slot))
                    self.server.files[slot] = (name, data)
                    response.append(dict(slot=slot, name=name, **inspect_book(data)))
                return self.send(response)
            if self.path == '/api/build':
                self.server.result = None
                if set(self.server.files) != {'1', '2'}:
                    raise ValueError('엑셀 파일 2개를 모두 선택해 주세요.')
                if len(payload['inputs']) != 2 or {str(i['slot']) for i in payload['inputs']} != {'1', '2'}:
                    raise ValueError('서로 다른 파일 2개의 연결 설정이 필요합니다.')
                records = []
                for settings in payload['inputs']:
                    name, data = self.server.files[str(settings['slot'])]
                    records.extend(read_records(data, settings['sheet'], settings['header'], settings['mapping'], name))
                self.server.result = build_result(records, payload.get('keywords'))
                return self.send(self.server.result)
            if self.path in ('/api/approve', '/api/exclude', '/api/export'):
                if self.server.result is None:
                    raise ValueError('먼저 목록을 생성해 주세요.')
                if self.path == '/api/export':
                    return self.send(export_result(self.server.result), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename='survey_customers.xlsx')
                if self.path == '/api/approve':
                    if payload.get('confirmed') is not True:
                        raise ValueError('최신 정보와 담당자 직급을 확인한 뒤 체크해 주세요.')
                    customer = approve_customer(self.server.result, payload['customer_id'], payload['values'])
                    record_id = payload.get('record_id')
                    candidate = next((r for r in customer['candidates'] if r['record_id'] == record_id), None)
                    if candidate:
                        customer['source'] = candidate['source'] + ' / 사용자 확인·수정'
                        customer['updated'] = candidate['updated']
                else:
                    customer = next(c for c in self.server.result['customers'] if c['customer_id'] == payload['customer_id'])
                    customer.update(status='확인 필요', reasons=['사용자가 설문 대상에서 제외'], manual=False)
                return self.send(self.server.result)
            return self.send({'error': '지원하지 않는 요청입니다.'}, status=404)
        except Exception as error:
            message = str(error) if isinstance(error, (ValueError, KeyError)) else '파일 처리에 실패했습니다. 파일 형식과 시트·제목 행을 확인해 주세요.'
            return self.send({'error': message}, status=400)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    server = SurveyServer(('127.0.0.1', args.port))
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'Survey customer tool: {url}', flush=True)
    print('Keep this window open. Close it or press Ctrl+C to stop.', flush=True)
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
