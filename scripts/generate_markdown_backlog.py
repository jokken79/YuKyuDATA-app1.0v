#!/usr/bin/env python3
"""Genera un backlog consolidado desde checklists pendientes en archivos Markdown."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "BACKLOG_PENDIENTES.md"

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "basuraa",
    ".agent",
    ".claude",
    "venv",
    ".venv",
    "__pycache__",
}

CHECKBOX_PATTERNS = [
    re.compile(r"^\s*[-*]\s*\[\s\]\s+(.*)$"),
    re.compile(r"^\s*\d+\.\s*\[\s\]\s+(.*)$"),
    re.compile(r"^\s*\[\s\]\s+(.*)$"),
]


@dataclass
class PendingItem:
    file_path: str
    line_number: int
    text: str


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def collect_pending_items() -> list[PendingItem]:
    items: list[PendingItem] = []

    for md_file in ROOT.rglob("*.md"):
        rel = md_file.relative_to(ROOT)
        if should_skip(rel):
            continue

        lines = md_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, line in enumerate(lines, start=1):
            for pattern in CHECKBOX_PATTERNS:
                match = pattern.match(line)
                if match:
                    text = re.sub(r"\s+", " ", match.group(1).strip())
                    if text:
                        items.append(
                            PendingItem(
                                file_path=rel.as_posix(),
                                line_number=idx,
                                text=text,
                            )
                        )
                    break

    return items


def render(items: list[PendingItem]) -> str:
    grouped: dict[str, list[PendingItem]] = {}
    for item in items:
        grouped.setdefault(item.file_path, []).append(item)

    files_sorted = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)

    lines: list[str] = [
        "# Backlog consolidado de pendientes Markdown",
        "",
        f"Generado automáticamente: {date.today().isoformat()}",
        "",
        "## Resumen",
        f"- Archivos con pendientes: **{len(files_sorted)}**",
        f"- Ítems pendientes detectados: **{len(items)}**",
        "",
        "## Top archivos con más pendientes",
    ]

    for file_path, file_items in files_sorted[:15]:
        lines.append(f"- `{file_path}`: {len(file_items)}")

    lines.extend(["", "## Pendientes por archivo", ""])

    for file_path, file_items in files_sorted:
        lines.append(f"### `{file_path}` ({len(file_items)})")
        for item in file_items:
            lines.append(
                f"- [ ] L{item.line_number}: {item.text}"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    items = collect_pending_items()
    content = render(items)
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"Backlog generado en {OUTPUT.relative_to(ROOT)} con {len(items)} ítems.")


if __name__ == "__main__":
    main()
