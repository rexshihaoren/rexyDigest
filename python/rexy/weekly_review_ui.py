"""Dependency-free localhost UI for weekly Gist and Brief review."""

from __future__ import annotations

import html
import json
import secrets
import threading
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from .weekly_review import WeeklyReviewSession
from .generate.config import GeneratorConfig
from .generate.llm.deep_note import DeepNoteWriter


def start_weekly_review_server(
    session: WeeklyReviewSession,
    port: int = 0,
    *,
    config: GeneratorConfig | None = None,
    writer_factory: Callable[[], DeepNoteWriter] | None = None,
) -> tuple[ThreadingHTTPServer, str]:
    token = secrets.token_urlsafe(24)
    candidates = session.deep_note_candidates(config) if config is not None else []
    child_servers: list[ThreadingHTTPServer] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if not _authorized(parsed.query, token):
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            if parsed.path != "/":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            body = _page(session, candidates).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if not _authorized(parsed.query, token):
                self._json({"error": "forbidden"}, HTTPStatus.FORBIDDEN)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(length) or b"{}")
                if parsed.path == "/api/save":
                    session.save_brief(str(data.get("markdown", "")))
                    self._json({"saved": True})
                    return
                if parsed.path == "/api/discard":
                    session.discard_brief()
                    self._json({"discarded": True})
                    return
                if parsed.path == "/api/finish":
                    final = session.finish()
                    self._json({"finished": True, "final_path": str(final.resolve())})
                    return
                if parsed.path == "/api/generate-deep-notes":
                    if config is None or writer_factory is None:
                        raise ValueError("DeepNote generation is unavailable")
                    raw_ids = data.get("item_ids", [])
                    if not isinstance(raw_ids, list) or not all(isinstance(value, str) for value in raw_ids):
                        raise ValueError("item_ids must be a list of strings")
                    item_ids = list(raw_ids)
                    drafts = session.generate_deep_notes(item_ids, config, writer_factory())
                    review_urls: list[str] = []
                    from .generate.review_ui import find_review_session, start_review_server

                    for item_id in item_ids:
                        review = find_review_session(
                            session.review_corpus_root,
                            session.inbox_root,
                            session.window.end.isoformat(),
                            item_id,
                        )
                        child, child_url = start_review_server(review)
                        child_servers.append(child)
                        threading.Thread(target=child.serve_forever, daemon=True).start()
                        review_urls.append(child_url)
                    self._json({
                        "drafts": [str(path.resolve()) for path in drafts],
                        "review_urls": review_urls,
                    })
                    return
                self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
                self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

        def _json(self, value: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(value).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    return server, f"http://127.0.0.1:{server.server_port}/?token={token}"


def serve_weekly_review(
    session: WeeklyReviewSession,
    *,
    port: int = 0,
    open_browser: bool = True,
    config: GeneratorConfig | None = None,
    writer_factory: Callable[[], DeepNoteWriter] | None = None,
) -> None:
    server, url = start_weekly_review_server(
        session, port, config=config, writer_factory=writer_factory,
    )
    print(f"[rexy] weekly review: {url}")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _authorized(query: str, token: str) -> bool:
    return urllib.parse.parse_qs(query).get("token") == [token]


def _page(session: WeeklyReviewSession, candidates: list[Any]) -> str:
    gist = html.escape(session.gist_markdown)
    brief = html.escape(session.brief_markdown)
    brief_disabled = " disabled" if session.brief_discarded else ""
    discarded_message = "Brief publication discarded for this review." if session.brief_discarded else ""
    candidate_html = "".join(
        f'<label class="candidate"><input type="checkbox" value="{html.escape(candidate.entry.item_id)}">'
        f'<strong>{html.escape(candidate.item.title)}</strong><small>{html.escape(candidate.entry.tldr_en)}</small></label>'
        for candidate in candidates
    ) or "<p>No eligible DeepNote candidates.</p>"
    generate_control = '<button id="generate">Generate selected DeepNotes</button>' if candidates else ""
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Weekly Review</title>
<style>
body{{margin:0;padding-bottom:70px;font:15px system-ui;background:#f5f3ed;color:#24231f}}
header{{padding:14px 20px;background:#fff;border-bottom:1px solid #d8d4ca}}
main{{display:grid;grid-template-columns:1fr 1fr 320px;gap:16px;padding:16px;min-height:calc(100vh - 132px);box-sizing:border-box}}
section{{display:flex;flex-direction:column;min-width:0}} pre,textarea{{flex:1;margin:0;padding:16px;border:1px solid #ccc;border-radius:8px;background:#fff;overflow:auto;white-space:pre-wrap}}
textarea{{resize:none;font:14px ui-monospace,monospace}} button{{padding:9px 14px;margin-left:8px}} footer{{position:fixed;z-index:1;bottom:0;left:0;right:0;padding:14px 20px;background:#fff;border-top:1px solid #d8d4ca}} #status{{color:#666}} .candidate{{display:flex;flex-direction:column;gap:4px;padding:10px;background:#fff;border:1px solid #ccc;border-radius:8px;margin-bottom:8px}} .candidate input{{align-self:flex-start}} small{{color:#666}}
</style></head><body>
<header><strong>Weekly Review</strong> · {session.window.end.isoformat()}</header>
<main><section><h2>Gist · reference</h2><pre>{gist}</pre></section>
<section><h2>Brief · edit</h2><textarea id="brief"{brief_disabled}>{brief}</textarea></section>
<section><h2>DeepNotes · select 0–2</h2><div id="candidates">{candidate_html}</div>{generate_control}<div id="deep-status"></div></section></main>
<footer><span id="status" role="status">{discarded_message}</span><button id="save"{brief_disabled}>Save Brief</button><button id="discard"{brief_disabled}>Discard Brief</button><button id="finish"{brief_disabled}>Finish Review</button></footer>
<script>
const token=new URLSearchParams(location.search).get('token');
const briefEl=document.querySelector('#brief'),statusEl=document.querySelector('#status');
async function post(path,body){{const r=await fetch(path+'?token='+encodeURIComponent(token),{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(body)}});const d=await r.json();if(!r.ok)throw new Error(d.error);return d}}
async function runAction(button,action){{button.disabled=true;try{{await action()}}catch(error){{statusEl.textContent='Error: '+error.message}}finally{{button.disabled=false}}}}
document.querySelector('#save').onclick=()=>runAction(document.querySelector('#save'),async()=>{{await post('/api/save',{{markdown:briefEl.value}});statusEl.textContent='Saved'}});
document.querySelector('#discard').onclick=()=>runAction(document.querySelector('#discard'),async()=>{{if(!confirm('Discard this Brief publication? This cannot be finished from this review session.'))return;await post('/api/discard',{{}});briefEl.disabled=true;document.querySelector('#save').disabled=true;document.querySelector('#discard').disabled=true;document.querySelector('#finish').disabled=true;statusEl.textContent='Brief publication discarded for this review'}});
document.querySelector('#finish').onclick=()=>runAction(document.querySelector('#finish'),async()=>{{await post('/api/save',{{markdown:briefEl.value}});const d=await post('/api/finish',{{}});statusEl.textContent='Finished: '+d.final_path}});
const generateButton=document.querySelector('#generate');if(generateButton)generateButton.onclick=async()=>{{const ids=[...document.querySelectorAll('#candidates input:checked')].map(x=>x.value);if(ids.length>2){{alert('Select at most two DeepNotes');return}};const deepStatus=document.querySelector('#deep-status');deepStatus.textContent='Generating…';try{{const d=await post('/api/generate-deep-notes',{{item_ids:ids}});deepStatus.innerHTML=d.review_urls.map((url,i)=>`<p><a href="${{url}}" target="_blank">Review DeepNote ${{i+1}}</a></p>`).join('')||'<p>No DeepNotes selected.</p>'}}catch(e){{deepStatus.textContent=e.message}}}};
</script></body></html>"""
