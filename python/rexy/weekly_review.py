"""One offline human-review session backed by an immutable Actions package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
import tomllib
import shutil

from .domain import Window
from .review_package import verify_review_package

if TYPE_CHECKING:
    from .generate.config import GeneratorConfig
    from .generate.deep_note_picker import DeepNoteCandidate
    from .generate.llm.deep_note import DeepNoteWriter


@dataclass(slots=True)
class WeeklyReviewSession:
    package_root: Path
    workspace_root: Path
    inbox_root: Path
    window: Window
    gist_path: Path
    generated_brief_path: Path
    working_brief_path: Path
    review_corpus_root: Path

    @classmethod
    def open(
        cls,
        package_root: Path,
        inbox_root: Path,
        workspace_root: Path | None = None,
    ) -> WeeklyReviewSession:
        manifest = verify_review_package(package_root)
        try:
            artifacts = manifest["artifacts"]
            gist_relative = artifacts["gist"]  # type: ignore[index]
            brief_relative = artifacts["brief"]  # type: ignore[index]
            window = Window.parse(str(manifest["window"]))
            run_id = str(manifest["run_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("review package artifact metadata invalid") from exc
        gist_path = _package_path(package_root, str(gist_relative))
        brief_path = _package_path(package_root, str(brief_relative))
        workspace = workspace_root or Path(".rexy/reviews") / run_id
        review_corpus = workspace / "corpus"
        package_corpus = package_root / "corpus"
        if package_corpus.exists() and package_corpus.resolve() != review_corpus.resolve() and not review_corpus.exists():
            shutil.copytree(package_corpus, review_corpus)
        elif not review_corpus.exists():
            review_corpus.mkdir(parents=True)
        return cls(
            package_root=package_root,
            workspace_root=workspace,
            inbox_root=inbox_root,
            window=window,
            gist_path=gist_path,
            generated_brief_path=brief_path,
            working_brief_path=workspace / "work" / "edited_weekly_brief.md",
            review_corpus_root=review_corpus,
        )

    @property
    def gist_markdown(self) -> str:
        return self.gist_path.read_text(encoding="utf-8")

    @property
    def brief_markdown(self) -> str:
        source = self.working_brief_path if self.working_brief_path.exists() else self.generated_brief_path
        return source.read_text(encoding="utf-8")

    def save_brief(self, markdown: str) -> Path:
        self.working_brief_path.parent.mkdir(parents=True, exist_ok=True)
        self.working_brief_path.write_text(markdown.rstrip() + "\n", encoding="utf-8")
        return self.working_brief_path

    def deep_note_candidates(self, config: GeneratorConfig) -> list[DeepNoteCandidate]:
        from .generate.deep_note_picker import collect_deep_note_candidates

        candidates, _skipped = collect_deep_note_candidates(
            self.window, self.review_corpus_root, config,
        )
        return candidates

    def generator_config(self) -> GeneratorConfig:
        from .generate.config import GeneratorConfig

        manifest = verify_review_package(self.package_root)
        relative = manifest.get("generator_config")
        if not relative:
            return GeneratorConfig()
        return GeneratorConfig.load(_package_path(self.package_root, str(relative)))

    def generate_deep_notes(
        self,
        item_ids: list[str],
        config: GeneratorConfig,
        writer: DeepNoteWriter,
    ) -> list[Path]:
        from .generate.deep_note_picker import (
            MAX_DEEP_NOTE_PICKS,
            _generate_selected_notes,
            _write_picks_file,
        )

        if len(item_ids) > MAX_DEEP_NOTE_PICKS:
            raise ValueError(f"select at most {MAX_DEEP_NOTE_PICKS} DeepNotes")
        candidates = {candidate.entry.item_id: candidate for candidate in self.deep_note_candidates(config)}
        unknown = [item_id for item_id in item_ids if item_id not in candidates]
        if unknown:
            raise ValueError(f"ineligible DeepNote selection: {', '.join(unknown)}")
        selected = [candidates[item_id] for item_id in item_ids]
        picks_file = self.workspace_root / "work" / "deep_picks" / f"{self.window.end.isoformat()}.toml"
        _write_picks_file(picks_file, self.window, item_ids)
        written, _skipped = _generate_selected_notes(
            selected,
            self.window,
            self.review_corpus_root,
            self.inbox_root,
            writer,
            input_fn=lambda _prompt: "s",
            output_fn=lambda _message: None,
        )
        return written

    def finish(self) -> Path:
        picks_file = self.workspace_root / "work" / "deep_picks" / f"{self.window.end.isoformat()}.toml"
        if picks_file.exists():
            from .generate.llm.deep_note import safe_filename_part

            data = tomllib.loads(picks_file.read_text(encoding="utf-8"))
            item_ids = [value for value in data.get("item_ids", []) if isinstance(value, str)]
            missing = [
                item_id for item_id in item_ids
                if not (
                    self.inbox_root
                    / f"deep_{safe_filename_part(item_id)}_{self.window.end.isoformat()}.md"
                ).is_file()
            ]
            if missing:
                raise ValueError(
                    "DeepNote review incomplete: " + ", ".join(missing)
                )
        self.inbox_root.mkdir(parents=True, exist_ok=True)
        final = self.inbox_root / f"weekly_brief_{self.window.end.isoformat()}.md"
        if final.exists():
            raise FileExistsError(f"reviewed weekly Brief already exists: {final}")
        final.write_text(self.brief_markdown.rstrip() + "\n", encoding="utf-8")
        return final


def _package_path(package_root: Path, relative: str) -> Path:
    path = (package_root / relative).resolve()
    try:
        path.relative_to(package_root.resolve())
    except ValueError as exc:
        raise ValueError(f"review artifact escapes package: {relative}") from exc
    if not path.is_file():
        raise ValueError(f"review artifact missing: {relative}")
    return path
