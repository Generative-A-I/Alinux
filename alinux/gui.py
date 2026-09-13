"""Tkinter desktop interface for Alinux."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .agent import Agent
from .main import _dispatch


class AlinuxWindow:
    """Desktop control center that routes operations through the Agent."""

    def __init__(self, root: tk.Tk, agent: Agent | None = None) -> None:
        self.root = root
        self.agent = agent or Agent()
        self.root.title("Alinux Control Center")
        self.root.geometry("760x520")
        self.root.minsize(620, 420)

        frame = ttk.Frame(root, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Alinux Control Center", font=("TkDefaultFont", 18, "bold")).pack(anchor=tk.W)
        ttk.Label(frame, text="System status, windows, audio, and applications").pack(anchor=tk.W, pady=(0, 12))

        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(0, 12))
        for label, request in (("System Status", "show system status"), ("Active Windows", "list windows"), ("Volume Up", "volume up"), ("Volume Down", "volume down"), ("Mute", "volume mute")):
            ttk.Button(actions, text=label, command=lambda text=request: self.run_request(text)).pack(side=tk.LEFT, padx=(0, 6))

        self.output = tk.Text(frame, height=16, state=tk.DISABLED, wrap=tk.WORD)
        self.output.pack(fill=tk.BOTH, expand=True)
        self.output.tag_configure("user", foreground="#245b9e")
        self.output.tag_configure("assistant", foreground="#1f6b45")

        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X, pady=(12, 0))
        self.input = ttk.Entry(controls)
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input.bind("<Return>", lambda _event: self.submit())
        ttk.Button(controls, text="Send", command=self.submit).pack(side=tk.LEFT, padx=(8, 0))
        self.input.focus_set()
        self._write("Alinux is ready.\n", "assistant")

    def _write(self, text: str, tag: str) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text, tag)
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)

    def run_request(self, request: str) -> None:
        self.input.delete(0, tk.END)
        self._write(f"Command: {request}\n", "user")
        try:
            response = _dispatch(self.agent.decide(request))
        except Exception as exc:  # noqa: BLE001 - GUI must remain open after a request failure
            response = f"Alinux recovered from an error: {exc}"
        self._write(f"Result: {response}\n\n", "assistant")

    def submit(self) -> None:
        request = self.input.get().strip()
        if not request:
            return
        self.run_request(request)


def open_gui(agent: Agent | None = None, use_default_groq_api: bool = False) -> int:
    """Open the Alinux desktop window and return a process exit status."""
    try:
        root = tk.Tk()
    except (ImportError, tk.TclError) as exc:
        print(f"Could not open the Alinux GUI: {exc}")
        print("Install python3-tk and ensure DISPLAY points to the Fluxbox session.")
        return 1
    AlinuxWindow(root, agent or Agent(use_default_groq_api=use_default_groq_api))
    root.mainloop()
    return 0
