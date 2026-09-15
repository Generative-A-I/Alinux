from alinux import setup


def test_ollama_support_excludes_i686(monkeypatch):
    monkeypatch.setattr(setup.platform, "machine", lambda: "i686")

    assert setup._ollama_supported() is False


def test_ollama_support_accepts_64_bit_x86(monkeypatch):
    monkeypatch.setattr(setup.platform, "machine", lambda: "x86_64")

    assert setup._ollama_supported() is True