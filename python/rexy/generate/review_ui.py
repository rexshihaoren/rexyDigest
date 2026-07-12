"""Local, dependency-free DeepNote visual review UI."""

from __future__ import annotations

import hashlib
import html
import json
import mimetypes
import re
import secrets
import threading
import urllib.parse
import webbrowser
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from .deep_note_format import validate_deep_note_markdown
from .deep_note_visuals import VisualReview, render_approved_visuals


class ReviewSession:
    def __init__(
        self,
        draft_path: Path,
        sidecar_path: Path,
        final_path: Path,
        reevaluate: Callable[[Path, Path, list[str]], None] | None = None,
    ) -> None:
        self.draft_path = draft_path
        self.sidecar_path = sidecar_path
        self.final_path = final_path
        self.reevaluate = reevaluate
        self._lock = threading.Lock()

    def state(self) -> dict[str, Any]:
        with self._lock:
            markdown = self.draft_path.read_text(encoding="utf-8")
            data = self._read_sidecar()
            candidates = data.get("candidates", [])
            section_reviews = _effective_section_reviews(data)
            return {
                "markdown": markdown,
                "preview_markdown": _render_current_selection(markdown, data),
                "validation_errors": validate_deep_note_markdown(markdown),
                "candidates": candidates,
                "section_reviews": section_reviews,
                "complete": bool(data.get("complete", True)),
                "error": str(data.get("error", "")),
                "publish_ready": self._publish_ready(markdown, data),
                "final_path": str(self.final_path),
            }

    def save_markdown(self, markdown: str) -> dict[str, Any]:
        errors = validate_deep_note_markdown(markdown)
        if errors:
            raise ValueError("invalid deep note Markdown: " + "; ".join(errors))
        with self._lock:
            old = self.draft_path.read_text(encoding="utf-8")
            old_sections = _sections(old)
            new_sections = _sections(markdown)
            changed = [
                heading for heading in new_sections
                if _content_hash(old_sections.get(heading, "")) != _content_hash(new_sections[heading])
            ]
            data = self._read_sidecar()
            section_reviews = data.setdefault("section_reviews", {})
            for heading in changed:
                section_reviews.pop(heading, None)
                for candidate in data.get("candidates", []):
                    if candidate.get("section_heading") != heading:
                        continue
                    approval = candidate.setdefault("approval", {})
                    if approval.get("status") in {"approved", "rejected", "no_visual"}:
                        approval["status"] = "stale"
                        approval["reviewed_at"] = None
            self.draft_path.write_text(markdown.rstrip() + "\n", encoding="utf-8")
            self._write_sidecar(data)
        if changed and self.reevaluate is not None:
            try:
                self.reevaluate(self.draft_path, self.sidecar_path, changed)
            except RuntimeError as exc:
                with self._lock:
                    data = self._read_sidecar()
                    data["complete"] = False
                    data["error"] = str(exc)
                    self._write_sidecar(data)
        return {"changed_sections": changed}

    def approve(self, candidate_id: str) -> None:
        with self._lock:
            data = self._read_sidecar()
            selected = next(
                (candidate for candidate in data.get("candidates", []) if candidate.get("candidate_id") == candidate_id),
                None,
            )
            if selected is None:
                raise ValueError(f"candidate not found: {candidate_id}")
            heading = str(selected["section_heading"])
            reviewed_at = _now()
            for candidate in data.get("candidates", []):
                if candidate.get("section_heading") != heading:
                    continue
                approval = candidate.setdefault("approval", {})
                approval["status"] = "approved" if candidate is selected else "rejected"
                approval["reviewed_at"] = reviewed_at
            data.setdefault("section_reviews", {})[heading] = {
                "status": "approved",
                "candidate_id": candidate_id,
                "reviewed_at": reviewed_at,
            }
            self._write_sidecar(data)

    def choose_no_visual(self, section_heading: str) -> None:
        with self._lock:
            data = self._read_sidecar()
            reviewed_at = _now()
            for candidate in data.get("candidates", []):
                if candidate.get("section_heading") == section_heading:
                    approval = candidate.setdefault("approval", {})
                    approval["status"] = "rejected"
                    approval["reviewed_at"] = reviewed_at
            data.setdefault("section_reviews", {})[section_heading] = {
                "status": "no_visual",
                "reviewed_at": reviewed_at,
            }
            self._write_sidecar(data)

    def waive_incomplete(self) -> None:
        with self._lock:
            data = self._read_sidecar()
            if data.get("complete", True):
                return
            reviewed_at = _now()
            reviews = data.setdefault("section_reviews", {})
            for candidate in data.get("candidates", []):
                approval = candidate.setdefault("approval", {})
                approval["status"] = "rejected"
                approval["reviewed_at"] = reviewed_at
                heading = str(candidate.get("section_heading", ""))
                reviews[heading] = {"status": "no_visual", "reviewed_at": reviewed_at}
            data["waived_incomplete"] = True
            data["waived_at"] = reviewed_at
            self._write_sidecar(data)

    def publish(self) -> Path:
        with self._lock:
            markdown = self.draft_path.read_text(encoding="utf-8")
            data = self._read_sidecar()
            if not self._publish_ready(markdown, data):
                raise ValueError("visual review incomplete")
            rendered = _render_current_selection(markdown, data)
            errors = validate_deep_note_markdown(rendered)
            if errors:
                raise ValueError("invalid final Markdown: " + "; ".join(errors))
            self.final_path.parent.mkdir(parents=True, exist_ok=True)
            self.final_path.write_text(rendered.rstrip() + "\n", encoding="utf-8")
            data["published_at"] = _now()
            data["final_path"] = str(self.final_path)
            self._write_sidecar(data)
            return self.final_path

    def asset_for(self, candidate_id: str) -> Path:
        data = self._read_sidecar()
        candidate = next(
            (item for item in data.get("candidates", []) if item.get("candidate_id") == candidate_id),
            None,
        )
        if candidate is None:
            raise ValueError("candidate not found")
        path = Path(str(candidate.get("asset_path", "")))
        return path if path.is_absolute() else Path.cwd() / path

    def _publish_ready(self, markdown: str, data: dict[str, Any]) -> bool:
        if validate_deep_note_markdown(markdown):
            return False
        if not data.get("complete", True) and not data.get("waived_incomplete", False):
            return False
        candidates = data.get("candidates", [])
        headings = {str(candidate.get("section_heading", "")) for candidate in candidates}
        reviews = _effective_section_reviews(data)
        return all(reviews.get(heading, {}).get("status") in {"approved", "no_visual"} for heading in headings)

    def _read_sidecar(self) -> dict[str, Any]:
        return json.loads(self.sidecar_path.read_text(encoding="utf-8"))

    def _write_sidecar(self, data: dict[str, Any]) -> None:
        self.sidecar_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def _sections(markdown: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^### .+$", markdown))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        result[match.group(0).strip()] = markdown[match.start():end]
    return result


def _content_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _effective_section_reviews(data: dict[str, Any]) -> dict[str, Any]:
    reviews = dict(data.get("section_reviews", {}))
    for candidate in data.get("candidates", []):
        heading = str(candidate.get("section_heading", ""))
        if heading in reviews:
            continue
        if candidate.get("approval", {}).get("status") == "approved":
            reviews[heading] = {
                "status": "approved",
                "candidate_id": candidate.get("candidate_id"),
                "reviewed_at": candidate.get("approval", {}).get("reviewed_at"),
            }
    return reviews


def _render_current_selection(markdown: str, data: dict[str, Any]) -> str:
    """Render only the current reviewed choices, including legacy reviewed drafts."""
    base = _strip_managed_visuals(markdown, data)
    reviews = [
        VisualReview(
            section_heading=str(candidate["section_heading"]),
            asset_path=str(candidate["asset_path"]),
            alt=str(candidate.get("alt") or "来源视觉证据"),
            status="approved",
        )
        for candidate in data.get("candidates", [])
        if candidate.get("approval", {}).get("status") == "approved"
    ]
    return render_approved_visuals(base, reviews)


def _strip_managed_visuals(markdown: str, data: dict[str, Any]) -> str:
    base = markdown
    for candidate in data.get("candidates", []):
        asset_path = str(candidate.get("asset_path", ""))
        if not asset_path:
            continue
        managed_image = rf"(?m)^[ \t]*!\[[^\n\]]*\]\({re.escape(asset_path)}\)[ \t]*\n?"
        base = re.sub(managed_image, "", base)
    return base


class _ReviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], session: ReviewSession, token: str) -> None:
        self.session = session
        self.token = token
        super().__init__(address, _ReviewHandler)


class _ReviewHandler(BaseHTTPRequestHandler):
    server: _ReviewServer

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if not self._authorized(parsed):
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if parsed.path == "/":
            self._send("text/html; charset=utf-8", _PAGE.replace("__TOKEN__", self.server.token).encode())
            return
        if parsed.path == "/api/state":
            self._json(self.server.session.state())
            return
        if parsed.path == "/final":
            try:
                self._send(
                    "text/markdown; charset=utf-8",
                    self.server.session.final_path.read_bytes(),
                )
            except OSError:
                self.send_error(HTTPStatus.NOT_FOUND)
            return
        if parsed.path.startswith("/asset/"):
            candidate_id = urllib.parse.unquote(parsed.path.removeprefix("/asset/"))
            try:
                asset = self.server.session.asset_for(candidate_id)
                mime = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
                self._send(mime, asset.read_bytes())
            except (ValueError, OSError):
                self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if not self._authorized(parsed):
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        try:
            payload = self._body()
            if parsed.path == "/api/save":
                result = self.server.session.save_markdown(str(payload.get("markdown", "")))
                self._json({**self.server.session.state(), **result})
            elif parsed.path == "/api/approve":
                self.server.session.approve(str(payload.get("candidate_id", "")))
                self._json(self.server.session.state())
            elif parsed.path == "/api/no-visual":
                self.server.session.choose_no_visual(str(payload.get("section_heading", "")))
                self._json(self.server.session.state())
            elif parsed.path == "/api/waive-incomplete":
                self.server.session.waive_incomplete()
                self._json(self.server.session.state())
            elif parsed.path == "/api/publish":
                final = self.server.session.publish()
                self._json({
                    "published": True,
                    "final_path": str(final),
                    "final_url": f"/final?token={self.server.token}",
                })
            elif parsed.path == "/api/close":
                self._json({"closed": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _authorized(self, parsed: urllib.parse.ParseResult) -> bool:
        query = urllib.parse.parse_qs(parsed.query)
        return secrets.compare_digest(query.get("token", [""])[0], self.server.token)

    def _body(self) -> dict[str, Any]:
        size = min(int(self.headers.get("Content-Length", "0")), 2_000_000)
        raw = self.rfile.read(size)
        return json.loads(raw or b"{}")

    def _json(self, value: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        self._send("application/json; charset=utf-8", json.dumps(value, ensure_ascii=False).encode(), status)

    def _send(self, mime: str, body: bytes, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)


def start_review_server(session: ReviewSession, port: int = 0) -> tuple[_ReviewServer, str]:
    token = secrets.token_urlsafe(24)
    server = _ReviewServer(("127.0.0.1", port), session, token)
    return server, f"http://127.0.0.1:{server.server_port}/?token={token}"


def serve_review(
    session: ReviewSession,
    *,
    port: int = 0,
    open_browser: bool = True,
) -> None:
    server, url = start_review_server(session, port)
    print(f"DeepNote review: {url}")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def find_review_session(
    corpus_root: Path,
    inbox_dir: Path,
    end_date: str,
    item_id: str | None = None,
) -> ReviewSession:
    item_part = _safe_item_part(item_id) if item_id else None
    matches = sorted((corpus_root / "visuals").glob(f"*/{end_date}/candidates.json"))
    if item_part:
        matches = [path for path in matches if path.parent.parent.name == item_part]
    if not matches:
        raise FileNotFoundError(f"no visual review found for {end_date}")
    if len(matches) > 1:
        names = ", ".join(path.parent.parent.name for path in matches)
        raise ValueError(f"multiple visual reviews found ({names}); pass --item-id")
    sidecar = matches[0]
    resolved_part = sidecar.parent.parent.name
    staged = corpus_root / "deep_notes" / resolved_part / end_date / "draft.md"
    sidecar_data = json.loads(sidecar.read_text(encoding="utf-8"))
    final = Path(sidecar_data.get("final_path") or inbox_dir / f"deep_{resolved_part}_{end_date}.md")
    if staged.exists():
        draft = staged
    elif final.exists():
        editable = _strip_managed_visuals(final.read_text(encoding="utf-8"), sidecar_data)
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_text(editable.rstrip() + "\n", encoding="utf-8")
        draft = staged
    else:
        draft = final
    if not draft.exists():
        raise FileNotFoundError(f"DeepNote draft missing: {draft}")
    def reevaluate(draft_path: Path, sidecar_path: Path, headings: list[str]) -> None:
        from .visual_review import GeminiVisualJudge, judge_candidates

        judge_candidates(draft_path, sidecar_path, GeminiVisualJudge(), headings)

    return ReviewSession(draft, sidecar, final, reevaluate=reevaluate)


def _safe_item_part(item_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", item_id).strip("_")[:80]


_PAGE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>DeepNote Review</title>
  <style>
    :root { color-scheme: light; --bg:#f6f6f3; --panel:#fff; --ink:#181816; --muted:#6d6d66; --line:#deded7; --accent:#235c45; --soft:#eef4f0; --danger:#9c352d; }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    header { height:58px; padding:0 22px; display:flex; align-items:center; gap:16px; border-bottom:1px solid var(--line); background:rgba(246,246,243,.96); position:sticky; top:0; z-index:2; }
    h1 { font-size:16px; margin:0; font-weight:650; }
    #progress { color:var(--muted); font-size:13px; }
    .spacer { flex:1; }
    button { border:1px solid var(--line); border-radius:7px; background:var(--panel); color:var(--ink); padding:8px 12px; cursor:pointer; font:inherit; }
    button:hover { border-color:#aaa; }
    button.primary { background:var(--accent); border-color:var(--accent); color:#fff; }
    button.ghost { border:0; background:transparent; color:var(--muted); }
    button:disabled { opacity:.42; cursor:not-allowed; }
    main { display:grid; grid-template-columns:minmax(360px,1fr) minmax(420px,1fr); min-height:calc(100vh - 58px); }
    .editor { padding:20px; border-right:1px solid var(--line); display:flex; flex-direction:column; gap:10px; position:sticky; top:58px; height:calc(100vh - 58px); }
    textarea { display:none; width:100%; flex:1; resize:none; border:1px solid var(--line); border-radius:8px; padding:16px; background:var(--panel); color:var(--ink); font:13px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace; outline:none; }
    textarea:focus { border-color:#8a9f94; box-shadow:0 0 0 3px var(--soft); }
    .editor-bar { display:flex; align-items:center; gap:10px; }
    #save { display:none; }
    #status { color:var(--muted); font-size:13px; }
    #notice { color:var(--accent); font-size:13px; font-weight:600; }
    #errors { color:var(--danger); font-size:13px; white-space:pre-wrap; }
    .mode-switch { display:flex; gap:4px; align-self:flex-start; padding:3px; border:1px solid var(--line); border-radius:8px; background:#ecece7; }
    .mode-switch button { padding:5px 9px; border:0; background:transparent; }
    .mode-switch button.active { background:var(--panel); box-shadow:0 1px 2px rgba(0,0,0,.08); }
    #preview { display:block; flex:1; overflow:auto; border:1px solid var(--line); border-radius:8px; padding:18px 22px; background:var(--panel); }
    #preview h1 { font-size:24px; margin:0 0 16px; }
    #preview h3 { font-size:17px; margin:26px 0 10px; }
    #preview p, #preview li { line-height:1.65; }
    #preview blockquote { margin:12px 0; padding-left:14px; border-left:3px solid var(--line); color:var(--muted); }
    #preview figure { margin:20px 0; }
    #preview figure img { width:100%; max-height:430px; object-fit:contain; border-radius:8px; background:#ecece8; }
    #preview figcaption { color:var(--muted); font-size:12px; margin-top:5px; }
    .reviews { padding:20px 22px 100px; }
    .section { margin:0 0 28px; }
    .section-head { display:flex; gap:12px; align-items:baseline; margin-bottom:10px; }
    .section h2 { margin:0; font-size:16px; }
    .badge { font-size:12px; color:var(--muted); }
    .candidate { background:var(--panel); border:1px solid var(--line); border-radius:10px; overflow:hidden; margin:10px 0; }
    .candidate.approved { border-color:var(--accent); box-shadow:0 0 0 2px var(--soft); }
    .candidate img { width:100%; max-height:430px; display:block; object-fit:contain; background:#ecece8; }
    .candidate-body { padding:13px 14px; }
    .meta { color:var(--muted); font-size:12px; margin-bottom:6px; }
    .reason { margin:0 0 12px; }
    .actions { display:flex; gap:8px; align-items:center; }
    .choice-help { color:var(--muted); font-size:12px; margin:7px 0 0; }
    button.selected-choice { color:#fff; background:var(--accent); border-color:var(--accent); opacity:1; }
    .no-visual { margin-top:8px; }
    .no-visual.selected-choice { background:#62625d; border-color:#62625d; }
    footer { position:fixed; right:0; bottom:0; width:50%; padding:14px 22px; border-top:1px solid var(--line); background:rgba(246,246,243,.96); display:flex; justify-content:flex-end; }
    @media (max-width:900px) { main { grid-template-columns:1fr; } .editor { position:relative; top:0; height:65vh; border-right:0; border-bottom:1px solid var(--line); } footer { width:100%; } }
  </style>
</head>
<body>
  <header><h1>DeepNote Review</h1><span id="progress"></span><span id="notice" role="status" aria-live="polite"></span><span class="spacer"></span><button class="ghost" id="close">Close ×</button></header>
  <main>
    <section class="editor"><div class="mode-switch" role="tablist" aria-label="Note view"><button id="edit-tab" role="tab" aria-selected="false">Edit note</button><button class="active" id="preview-tab" role="tab" aria-selected="true">Preview note</button></div><textarea id="markdown" spellcheck="false" aria-label="DeepNote Markdown"></textarea><article id="preview" aria-label="DeepNote preview"></article><div id="errors"></div><div class="editor-bar"><button class="primary" id="save">Save changes</button><span id="status">Saved</span></div></section>
    <section class="reviews" id="reviews"></section>
  </main>
  <footer><button class="primary" id="publish" disabled>Finish review</button></footer>
  <script>
    const token="__TOKEN__"; const api=p=>`${p}?token=${encodeURIComponent(token)}`;
    let state=null, original="";
    const markdown=document.querySelector('#markdown'), preview=document.querySelector('#preview'), save=document.querySelector('#save'), status=document.querySelector('#status'), notice=document.querySelector('#notice');
    async function call(path, body={}) { const r=await fetch(api(path),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); const data=await r.json(); if(!r.ok) throw new Error(data.error||'Request failed'); return data; }
    function esc(v) { const d=document.createElement('div'); d.textContent=v??''; return d.innerHTML; }
    function group(items) { return items.reduce((m,c)=>((m[c.section_heading]??=[]).push(c),m),{}); }
    function safeUrl(v) { return /^https?:\/\//.test(v||'')?v:''; }
    function inline(v) { return esc(v).replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>'); }
    function renderPreview(s) {
      const assets=Object.fromEntries(s.candidates.map(c=>[c.asset_path,c]));
      preview.innerHTML=(s.preview_markdown||s.markdown).split('\n').map(line=>{
        const image=line.trim().match(/^!\[([^\]]*)\]\((.+)\)$/);
        if(image&&assets[image[2]]) { const c=assets[image[2]]; return `<figure><img src="${api('/asset/'+encodeURIComponent(c.candidate_id))}" alt="${esc(image[1])}"><figcaption>${esc(image[1])}</figcaption></figure>`; }
        if(line.startsWith('# ')) return `<h1>${inline(line.slice(2))}</h1>`;
        if(line.startsWith('### ')) return `<h3>${inline(line.slice(4))}</h3>`;
        if(/^---+$/.test(line.trim())||/^─+$/.test(line.trim())) return '<hr>';
        if(line.startsWith('> ')) return `<blockquote>${inline(line.slice(2))}</blockquote>`;
        if(/^\s*- /.test(line)) return `<li>${inline(line.replace(/^\s*- /,''))}</li>`;
        return line.trim()?`<p>${inline(line)}</p>`:'';
      }).join('');
    }
    function render(s) {
      state=s; if(markdown.value!==s.markdown && !markdown.matches(':focus')) markdown.value=s.markdown; original=s.markdown;
      renderPreview(s);
      const grouped=group(s.candidates), reviews=s.section_reviews||{};
      const incomplete=!s.complete?`<article class="section"><div class="candidate-body" style="border:1px solid #d8b7b2;border-radius:8px;background:#fff8f7"><strong>Visual enrichment incomplete</strong><p class="reason">${esc(s.error||'A visual provider failed.')}</p><button id="waive">Continue text-only</button></div></article>`:'';
      document.querySelector('#reviews').innerHTML=incomplete+Object.entries(grouped).map(([heading,items])=>{
        const review=reviews[heading]||{};
        const noVisual=review.status==='no_visual';
        const decision=review.status==='approved'?'Visual selected':noVisual?'No visual selected':'Choose one outcome';
        return `<article class="section"><div class="section-head"><h2>${esc(heading)}</h2><span class="badge">${decision}</span></div>`+
          items.map(c=>{ const selected=review.status==='approved'&&review.candidate_id===c.candidate_id; const source=safeUrl(c.source?.timestamp_url||c.timestamp_url); return `<div class="candidate ${selected?'approved':''}"><img loading="lazy" src="${api('/asset/'+encodeURIComponent(c.candidate_id))}" alt="${esc(c.alt||'Visual candidate')}"><div class="candidate-body"><div class="meta">${source?`<a href="${esc(source)}" target="_blank" rel="noopener">View source</a>`:'Source image'} · Gemini ${esc(c.signals?.judge_decision||'not judged')} / ${esc(c.signals?.judge_confidence||'—')}</div><p class="reason">${esc(c.signals?.judge_reason||c.reason||'')}</p><div class="actions"><button class="${selected?'selected-choice':''}" data-approve="${esc(c.candidate_id)}" ${selected?'disabled aria-pressed="true"':''}>${selected?'Selected ✓':'Use this visual'}</button></div></div></div>`; }).join('')+
          `<button class="no-visual ${noVisual?'selected-choice':''}" data-none="${esc(heading)}" ${noVisual?'disabled aria-pressed="true"':''}>${noVisual?'No visual selected ✓':'Publish this section without a visual'}</button><p class="choice-help">Choose this when the image does not materially improve learning.</p></article>`;
      }).join('') || '<p>No visual candidates. Text-only publication is valid.</p>';
      const done=Object.keys(grouped).filter(h=>['approved','no_visual'].includes(reviews[h]?.status)).length;
      document.querySelector('#progress').textContent=`${done} of ${Object.keys(grouped).length} visual sections complete`;
      document.querySelector('#publish').disabled=!s.publish_ready;
      document.querySelector('#errors').textContent=(s.validation_errors||[]).join('\n');
    }
    function showMode(mode) { const editing=mode==='edit', editTab=document.querySelector('#edit-tab'), previewTab=document.querySelector('#preview-tab'); markdown.style.display=editing?'block':'none'; preview.style.display=editing?'none':'block'; editTab.classList.toggle('active',editing); previewTab.classList.toggle('active',!editing); editTab.setAttribute('aria-selected',String(editing)); previewTab.setAttribute('aria-selected',String(!editing)); }
    document.querySelector('#edit-tab').onclick=()=>showMode('edit');
    document.querySelector('#preview-tab').onclick=()=>showMode('preview');
    markdown.addEventListener('input',()=>{ const dirty=markdown.value!==original; save.style.display=dirty?'inline-block':'none'; status.textContent=dirty?'Unsaved changes':'Saved'; });
    save.onclick=async()=>{ save.disabled=true; status.textContent='Saving…'; try { render(await call('/api/save',{markdown:markdown.value})); status.textContent='Saved'; save.style.display='none'; } catch(e) { document.querySelector('#errors').textContent=e.message; status.textContent='Not saved'; } finally { save.disabled=false; } };
    document.querySelector('#reviews').onclick=async e=>{ const a=e.target.dataset.approve,n=e.target.dataset.none,w=e.target.id==='waive'; if(!a&&!n&&!w)return; try { render(await call(w?'/api/waive-incomplete':a?'/api/approve':'/api/no-visual',a?{candidate_id:a}:n?{section_heading:n}:{})); notice.textContent=w?'Visual failure waived; text-only publishing enabled.':a?'Visual selected and saved.':'This section will publish without a visual.'; } catch(err) { alert(err.message); } };
    document.querySelector('#publish').onclick=async()=>{ try { const r=await call('/api/publish'); document.body.innerHTML=`<main style="display:block;max-width:640px;margin:12vh auto;padding:30px"><h1>Review complete</h1><p>Published to <a href="${esc(r.final_url)}" target="_blank" rel="noopener">${esc(r.final_path)}</a></p><p style="color:#6d6d66">The review stays available until you close it.</p><button id="done-close">Close review</button></main>`; document.querySelector('#done-close').onclick=async()=>{ await call('/api/close'); document.body.innerHTML='<main style="display:block;padding:40px"><p>Review closed.</p></main>'; }; } catch(e) { alert(e.message); } };
    document.querySelector('#close').onclick=async()=>{ if(markdown.value!==original&&!confirm('Discard unsaved text changes and close?'))return; await call('/api/close'); window.close(); document.body.innerHTML='<main style="display:block;padding:40px"><p>Review closed. Progress is saved.</p></main>'; };
    fetch(api('/api/state')).then(r=>r.json()).then(s=>{ markdown.value=s.markdown; render(s); });
  </script>
</body>
</html>"""
