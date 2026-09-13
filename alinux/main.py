"""Command-line entry point for Alinux."""

from __future__ import annotations

import argparse


def _dispatch(agent_action) -> str:
    from . import system_controls

    if agent_action.action == "launch_app":
        return system_controls.launch_app(agent_action.parameter)
    if agent_action.action == "system_command":
        return system_controls.execute_system_command(agent_action.parameter)
    return agent_action.parameter


def _interactive(use_default_groq_api: bool = False) -> None:
    """Run the resilient interactive terminal loop."""
    from .agent import Agent

    print("Alinux ready. Type a request, or 'quit' to exit.")
    agent = Agent(use_default_groq_api=use_default_groq_api)
    while True:
        try:
            user_text = input("alinux> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAlinux stopped.")
            return
        if user_text.lower() in {"quit", "exit"}:
            print("Alinux stopped.")
            return
        try:
            print(_dispatch(agent.decide(user_text)))
        except Exception as exc:  # noqa: BLE001 - the interactive loop must recover
            print(f"Alinux recovered from an error: {exc}")


def main() -> int:
    """Run the GUI, Fluxbox installer, or terminal interface."""
    parser = argparse.ArgumentParser(prog="alinux", description="Alinux Linux desktop assistant")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("open", "install-fluxbox-menu"),
        help="open the GUI or install its Fluxbox context-menu entry",
    )
    parser.add_argument(
        "--use-default-groq-api",
        action="store_true",
        help="use Groq's built-in Llama model with GROQ_API_KEY",
    )
    args = parser.parse_args()
    if args.command == "open":
        try:
            from .gui import open_gui
        except ImportError:
            print("Could not open the Alinux GUI: install Debian's python3-tk package.")
            return 1

        return open_gui(use_default_groq_api=args.use_default_groq_api)
    if args.command == "install-fluxbox-menu":
        from .fluxbox import install_fluxbox_menu

        try:
            print(install_fluxbox_menu())
        except OSError as exc:
            print(f"Could not update the Fluxbox menu: {exc}")
            return 1
        return 0
    _interactive(use_default_groq_api=args.use_default_groq_api)
    return 0


if __name__ == "__main__":
    main()
