"""Shell-safe hook command strings shared by the host installers."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def hook_command(path: Path) -> str:
    """Return the ``bash <script>`` command a host should register for ``path``.

    Quoted POSIX form. A home directory with a space (``C:/Users/First Last``,
    ``/Users/First Last``) otherwise splits into two arguments, and an unquoted
    backslash path is eaten by the shell (``bash: C:UsersKyle: No such file``),
    so the host records a non-blocking hook error on every turn and nothing is
    captured.
    """
    return f'{_bash_for_hooks()} "{path.as_posix()}"'


def _bash_for_hooks() -> str:
    """Interpreter token for the registered command.

    POSIX hosts resolve ``bash`` from PATH. On Windows a bare ``bash`` is a
    trap: Git for Windows puts only ``Git/cmd`` (git.exe) on the machine PATH,
    while ``C:/Windows/System32/bash.exe`` (the WSL shim) and the Store alias
    are always there — so a host that is not itself running inside Git Bash
    (Codex, a GUI app) launches WSL, which cannot see a ``C:/...`` script, and
    the hook dies silently. Pin the Git Bash executable instead.
    """
    if os.name != "nt":
        return "bash"
    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Git" / "bin" / "bash.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Git" / "bin" / "bash.exe",
    ]
    for c in candidates:
        if c.is_file():
            return f'"{c.as_posix()}"'
    found = shutil.which("bash")
    if found and "system32" not in found.lower() and "windowsapps" not in found.lower():
        return f'"{Path(found).as_posix()}"'
    return "bash"


def find_hook(entries: list, marker: str) -> dict | None:
    """Return the handler dict in Claude/Codex-shaped ``entries`` whose command
    names ``marker`` (the hook script filename), or None."""
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for handler in entry.get("hooks") or []:
            if isinstance(handler, dict) and marker in (handler.get("command") or ""):
                return handler
    return None
