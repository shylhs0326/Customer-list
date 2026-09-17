"""Vercel adapter for the existing local HTTP handler.

Vercel invokes the BaseHTTPRequestHandler class named ``handler``. The
application state is kept for the lifetime of a warm function so the UI can
complete its short upload/build/review flow; users should export results
before ending the session.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import Handler as LocalHandler
from excel_io import sample_book


class handler(LocalHandler):
    def valid_host(self):
        return True

    def _prepare_state(self):
        server = self.server
        if not hasattr(server, 'token'):
            server.token = self.headers.get('X-Session-Token') or '__TOKEN__'
        if not hasattr(server, 'files'):
            server.files = {}
        if not hasattr(server, 'result'):
            server.result = None

    def do_GET(self):
        self._prepare_state()
        if self.path.startswith('/api/index.py?sample='):
            slot = self.path.rsplit('=', 1)[-1]
            if slot in ('1', '2'):
                return self.send(sample_book(int(slot)), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=f'sample{slot}.xlsx')
        return super().do_GET()

    def do_POST(self):
        self._prepare_state()
        # The static Vercel page cannot receive the local per-process token;
        # accept the browser session token for this function instance.
        if self.headers.get('X-Session-Token'):
            self.server.token = self.headers['X-Session-Token']
        return super().do_POST()
