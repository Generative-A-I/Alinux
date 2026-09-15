"""Small, predictable Linux desktop control functions for Alinux.

All subprocess calls use argument lists and timeouts. Operations intentionally
cover a narrow set of desktop actions so an LLM cannot directly execute an
arbitrary shell command.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Sequence

_DEFAULT_TIMEOUT = 8
_ALLOWED_APPS = {
    "terminal": ("x-terminal-emulator",),
    "file manager": ("xdg-open", os.path.expanduser("~")),
}


def _run(command: Sequence[str], timeout: int = _DEFAULT_TIMEOUT) -> subprocess.CompletedProcess[str]:
    """Run a desktop command without invoking a shell."""
    return subprocess.run(
        list(command),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _tool_available(tool: str) -> bool:
    return shutil.which(tool) is not None


def _browser_command() -> list[str] | None:
    """Build the dependency-free Alinux browser command."""
    return [sys.executable, "-m", "alinux.browser"]


def launch_app(application: str) -> str:
    """Launch a known desktop application by friendly name."""
    name = application.strip().lower()
    if name == "browser":
        command = _browser_command()
    else:
        command = _ALLOWED_APPS.get(name)
    if command is None:
        return f"I cannot launch {application!r}; supported apps are terminal, browser, and file manager."
    if name != "browser" and not _tool_available(command[0]):
        return f"Cannot launch {name}: required command {command[0]!r} is not installed."
    try:
        subprocess.Popen(list(command), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        return f"Could not launch {name}: {exc}"
    return f"Launched {name}."


def adjust_volume(change: str) -> str:
    """Adjust ALSA master volume using amixer."""
    if not _tool_available("amixer"):
        return "Cannot adjust volume: amixer is not installed."
    normalized = change.strip().lower()
    if normalized in {"up", "increase", "louder", "+"}:
        value = "5%+"
        description = "increased"
    elif normalized in {"down", "decrease", "quieter", "-"}:
        value = "5%-"
        description = "decreased"
    elif normalized in {"mute", "muted"}:
        value = "toggle"
        description = "toggled"
    else:
        return "Volume parameter must be up, down, or mute."
    try:
        result = _run(("amixer", "-q", "sset", "Master", value))
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"Volume adjustment failed: {exc}"
    if result.returncode != 0:
        detail = result.stderr.strip() or "amixer returned an error"
        return f"Volume adjustment failed: {detail}"
    return f"Volume {description}."


def list_windows() -> str:
    """Return active window IDs and titles from xdotool."""
    if not _tool_available("xdotool"):
        return "Cannot list windows: xdotool is not installed."
    try:
        result = _run(("xdotool", "search", "--name", "."))
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"Window listing failed: {exc}"
    if result.returncode != 0 or not result.stdout.strip():
        return "No active windows found."
    windows: list[str] = []
    for window_id in result.stdout.splitlines():
        window_id = window_id.strip()
        if not window_id:
            continue
        title_result = _run(("xdotool", "getwindowname", window_id))
        title = title_result.stdout.strip() if title_result.returncode == 0 else "(untitled)"
        windows.append(f"{window_id}: {title}")
    return "Active windows:\n" + "\n".join(windows) if windows else "No active windows found."


def manage_window(action: str, window_id: str) -> str:
    """Close or minimize one window by its xdotool ID."""
    if not _tool_available("xdotool"):
        return "Cannot manage windows: xdotool is not installed."
    normalized = action.strip().lower()
    command = {"close": "windowclose", "minimize": "windowminimize"}.get(normalized)
    if command is None or not window_id.strip().isdigit():
        return "Window action must be close or minimize, with a numeric window ID."
    try:
        result = _run(("xdotool", command, window_id.strip()))
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"Window action failed: {exc}"
    if result.returncode != 0:
        return f"Window action failed: {result.stderr.strip() or 'xdotool returned an error'}"
    return f"Window {window_id.strip()} {normalized}d."


def system_status() -> str:
    """Return concise CPU, memory, and battery information."""
    status: list[str] = []
    if _tool_available("uptime"):
        result = _run(("uptime",))
        if result.returncode == 0:
            status.append(f"Load: {result.stdout.strip()}")
    try:
        memory = _run(("free", "-h"))
        memory_line = next((line for line in memory.stdout.splitlines() if line.startswith("Mem:")), None)
        if memory_line:
            fields = memory_line.split()
            status.append(f"Memory: {fields[2]} used of {fields[1]}" if len(fields) > 2 else f"Memory: {memory_line}")
    except (OSError, subprocess.TimeoutExpired):
        status.append("Memory: unavailable")
    battery_path = "/sys/class/power_supply"
    batteries = [entry for entry in os.listdir(battery_path)] if os.path.isdir(battery_path) else []
    battery = next((entry for entry in batteries if entry.startswith("BAT")), None)
    if battery:
        capacity_file = os.path.join(battery_path, battery, "capacity")
        try:
            with open(capacity_file, encoding="ascii") as file:
                status.append(f"Battery: {file.read().strip()}%")
        except OSError:
            status.append("Battery: unavailable")
    else:
        status.append("Battery: not detected")
    return "System status:\n" + "\n".join(status)


def execute_system_command(command: str) -> str:
    """Execute a named safe system operation, never an arbitrary shell string."""
    normalized = command.strip().lower()
    if normalized in {"status", "system status", "info"}:
        return system_status()
    if normalized in {"windows", "list windows", "active windows"}:
        return list_windows()
    if normalized in {"volume up", "volume down", "volume mute"}:
        return adjust_volume(normalized.removeprefix("volume "))
    return "Unknown system command. Supported commands: status, windows, volume up, volume down, volume mute."
