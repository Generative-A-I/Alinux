from alinux import system_controls
from alinux.agent import AgentAction
from alinux.main import _dispatch


def test_arbitrary_system_commands_are_rejected():
    result = system_controls.execute_system_command("rm -rf /")

    assert result.startswith("Unknown system command")


def test_dispatch_responds_without_desktop_access():
    result = _dispatch(AgentAction(action="respond_to_user", parameter="Hello"))

    assert result == "Hello"


def test_browser_uses_builtin_standard_library_browser():
    command = system_controls._browser_command()

    assert command[-2:] == ["-m", "alinux.browser"]