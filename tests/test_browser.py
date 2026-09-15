from alinux.browser import _PageParser


def test_browser_parser_extracts_text_and_links():
    parser = _PageParser()
    parser.feed('<h1>Alinux</h1><p><a href="/status">System status</a></p>')

    assert any(text == "Alinux" for text, _target in parser.runs)
    assert ("System status", "/status") in parser.runs