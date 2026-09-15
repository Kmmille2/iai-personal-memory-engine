"""Shell-safe hook command strings shared by the host installers."""

from __future__ import annotations

from pathlib import Path


def hook_command(path: Path) -> str:
    """Return the ``bash <script>`` command a host should register for ``path``.

    Quoted POSIX form. A home directory with a space (``C:/Users/First Last``,
    ``/Users/First Last``) otherwise splits into two arguments, and an unquoted
    backslash path is eaten by the shell (``bash: C:UsersKyle: No such file``),
    so the host records a non-blocking hook error on every turn and nothing is
    captured.
    """
    return f'bash "{path.as_posix()}"'


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
