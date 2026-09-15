"""One-command Debian setup for Alinux."""

from __future__ import annotations

import shutil
import subprocess
import urllib.request

MODEL = "smollm2:360m"
APT_PACKAGES = ("python3-tk", "xdotool", "alsa-utils", "procps", "curl")


def _run(command: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, input=input_text, text=True, check=False)


def _privileged_prefix() -> list[str]:
    if shutil.which("sudo"):
        return ["sudo"]
    return []


def _ollama_running() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2):
            return True
    except OSError:
        return False


def setup() -> int:
    """Install Debian dependencies, Ollama, and the local SmolLM2 model."""
    if shutil.which("apt-get") is None:
        print("Alinux setup currently requires Debian or Ubuntu with apt-get.")
        return 1
    prefix = _privileged_prefix()
    print("Installing Alinux desktop dependencies...")
    result = _run(prefix + ["apt-get", "update"])
    if result.returncode != 0:
        return result.returncode
    result = _run(prefix + ["apt-get", "install", "-y", *APT_PACKAGES])
    if result.returncode != 0:
        return result.returncode
    if shutil.which("ollama") is None:
        print("Installing Ollama...")
        script = urllib.request.urlopen("https://ollama.com/install.sh", timeout=30).read().decode()
        result = _run([*prefix, "sh", "-s"], input_text=script)
        if result.returncode != 0:
            return result.returncode
    if not _ollama_running():
        print("Starting Ollama...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Downloading local model {MODEL}...")
    result = _run(["ollama", "pull", MODEL])
    if result.returncode != 0:
        return result.returncode
    print("Alinux setup complete. Run: alinux")
    return 0