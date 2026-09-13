"""Fluxbox menu integration for Alinux."""

from __future__ import annotations

import os
import shlex
import sys
import tempfile
from pathlib import Path


def _menu_entry() -> str:
    """Build a launcher that works even when Fluxbox has a minimal PATH."""
    python = shlex.quote(sys.executable)
    log_path = shlex.quote(str(Path.home() / ".cache" / "alinux" / "gui.log"))
    command = f"mkdir -p ~/.cache/alinux; {python} -m alinux open >>{log_path} 2>&1"
    return f"[exec] (Open Alinux) {{sh -c {shlex.quote(command)}}}"


def install_fluxbox_menu(menu_path: str | os.PathLike[str] | None = None) -> str:
    """Add an Open Alinux entry to the user's Fluxbox menu idempotently."""
    path = Path(menu_path).expanduser() if menu_path else Path.home() / ".fluxbox" / "menu"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else "[begin] (Fluxbox)\n[end]\n"
    menu_entry = _menu_entry()
    if "(Open Alinux)" in existing:
        return f"Alinux is already in the Fluxbox menu at {path}."
    lines = existing.splitlines()
    end_index = next((index for index, line in enumerate(lines) if line.strip() == "[end]"), len(lines))
    lines.insert(end_index, menu_entry)
    content = "\n".join(lines).rstrip() + "\n"
    fd, temporary_path = tempfile.mkstemp(prefix=".alinux-menu-", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temporary_file:
            temporary_file.write(content)
        os.replace(temporary_path, path)
    except Exception:
        try:
            os.unlink(temporary_path)
        except OSError:
            pass
        raise
    return f"Added Open Alinux to the Fluxbox menu at {path}. Restart or reconfigure Fluxbox to see it."
