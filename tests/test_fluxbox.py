from pathlib import Path

from alinux.fluxbox import install_fluxbox_menu, remove_fluxbox_menu
from alinux.main import main


def test_fluxbox_menu_entry_is_added_once(tmp_path: Path):
    menu_path = tmp_path / "menu"
    menu_path.write_text("[begin] (Fluxbox)\n[end]\n", encoding="utf-8")

    install_fluxbox_menu(menu_path)
    install_fluxbox_menu(menu_path)

    content = menu_path.read_text(encoding="utf-8")
    assert content.count("(Open Alinux)") == 1
    assert "-m alinux open" in content


def test_menu_command_does_not_require_llm_dependencies(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("sys.argv", ["alinux", "install-fluxbox-menu"])
    (tmp_path / ".fluxbox").mkdir()

    assert main.__module__ == "alinux.main"
    assert main() == 0
    assert "Open Alinux" in capsys.readouterr().out


def test_fluxbox_menu_entry_can_be_removed(tmp_path: Path):
    menu_path = tmp_path / "menu"
    menu_path.write_text("[begin] (Fluxbox)\n[exec] (Open Alinux) {alinux open}\n[end]\n", encoding="utf-8")

    result = remove_fluxbox_menu(menu_path)

    assert "Removed Alinux" in result
    assert "Open Alinux" not in menu_path.read_text(encoding="utf-8")
