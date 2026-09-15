"""Shell-safe hook command strings shared by the host installers."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def hook_command(path: Path) -> str:
    """Return the ``bash <script>`` command a host should register for ``path``.

    POSIX: ``bash "<path>"``. Windows: the Git Bash executable and the script
    as 8.3 short paths with no quotes at all. Two Windows traps make anything
    else fail silently in at least one host:

    * a bare ``bash`` resolves, for a host not itself running inside Git Bash
      (Codex CLI/Desktop, GUI apps), to ``C:/Windows/System32/bash.exe`` — the
      WSL shim — because Git only puts ``Git/cmd`` (git.exe) on the machine
      PATH; WSL cannot open a ``C:/...`` script (exit 127);
    * a command line that *starts* with a quote and contains more quotes has
      its first and last quote stripped by ``cmd.exe`` (the /C rule), so
      ``"C:/Program Files/Git/bin/bash.exe" "C:/Users/First Last/...sh"``
      runs as ``C:/Program`` and every hook reports Failed. Short names carry
      no spaces, so the registration needs no quotes and survives cmd,
      PowerShell and a direct CreateProcess alike.
    """
    if os.name != "nt":
        return f'bash "{path.as_posix()}"'
    bash = _git_bash_path()
    interp = _short_path(bash) if bash else "bash"
    return f"{_quote_if_needed(interp)} {_quote_if_needed(_short_path(path))}"


def _quote_if_needed(token: str) -> str:
    return f'"{token}"' if " " in token else token


def _short_path(path: Path) -> str:
    """8.3 form of an existing path (POSIX separators); the long form when the
    volume has 8.3 names disabled or the path does not exist yet."""
    try:
        import ctypes

        buf = ctypes.create_unicode_buffer(32768)
        n = ctypes.windll.kernel32.GetShortPathNameW(str(path), buf, 32768)  # type: ignore[attr-defined]
        if n and buf.value:
            return Path(buf.value).as_posix()
    except Exception:  # noqa: BLE001 -- fall back to the long form
        pass
    return path.as_posix()


def _git_bash_path() -> Path | None:
    candidates = [
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git" / "bin" / "bash.exe",
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Git" / "bin" / "bash.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Git" / "bin" / "bash.exe",
    ]
    for c in candidates:
        if c.is_file():
            return c
    found = shutil.which("bash")
    if found and "system32" not in found.lower() and "windowsapps" not in found.lower():
        return Path(found)
    return None


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
