"""Small Alinux web browser built with Python's standard library.

This intentionally renders readable HTML and links without embedding a large
browser engine. It supports navigation, history, reload, and ordinary HTTP(S)
requests; JavaScript, plugins, and advanced CSS are outside its small runtime.
"""

from __future__ import annotations

import html
import threading
import tkinter as tk
from html.parser import HTMLParser
from tkinter import ttk
from urllib.parse import urljoin
from urllib.request import Request, urlopen


class _PageParser(HTMLParser):
    """Convert basic HTML into text runs and clickable links."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.runs: list[tuple[str, str | None]] = []
        self.skip_depth = 0
        self.link: str | None = None
        self.pending_space = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        attributes = dict(attrs)
        if tag == "a" and attributes.get("href"):
            self.link = attributes["href"]
        if tag in {"br", "hr", "p", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self._newline()

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag == "a":
            self.link = None
        if tag in {"p", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self._newline()

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = " ".join(data.split())
        if not text:
            return
        if self.pending_space and self.runs and not self.runs[-1][0].endswith("\n"):
            text = " " + text
        self.pending_space = True
        self.runs.append((text, self.link))

    def _newline(self) -> None:
        if self.runs and not self.runs[-1][0].endswith("\n"):
            self.runs.append(("\n", None))
        self.pending_space = False


class AlinuxBrowser:
    """A lightweight, dependency-free HTML browser window."""

    def __init__(self, root: tk.Tk, start_url: str = "https://example.com") -> None:
        self.root = root
        self.root.title("Alinux Browser")
        self.root.geometry("1000x700")
        self.history: list[str] = []
        self.history_index = -1

        toolbar = ttk.Frame(root, padding=8)
        toolbar.pack(fill=tk.X)
        self.back_button = ttk.Button(toolbar, text="Back", command=self.back, width=7)
        self.back_button.pack(side=tk.LEFT)
        self.forward_button = ttk.Button(toolbar, text="Forward", command=self.forward, width=8)
        self.forward_button.pack(side=tk.LEFT, padx=(4, 8))
        ttk.Button(toolbar, text="Reload", command=self.reload, width=7).pack(side=tk.LEFT)
        self.address = ttk.Entry(toolbar)
        self.address.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self.address.bind("<Return>", lambda _event: self.navigate(self.address.get()))
        ttk.Button(toolbar, text="Go", command=lambda: self.navigate(self.address.get()), width=7).pack(side=tk.LEFT)

        body = ttk.Frame(root)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.page = tk.Text(body, wrap=tk.WORD, padx=18, pady=14, cursor="arrow")
        scrollbar = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.page.yview)
        self.page.configure(yscrollcommand=scrollbar.set)
        self.page.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.page.tag_configure("link", foreground="#1769aa", underline=True)
        self.page.tag_configure("heading", font=("TkDefaultFont", 16, "bold"))
        self.navigate(start_url, add_history=True)

    def navigate(self, url: str, add_history: bool = True) -> None:
        url = url.strip()
        if not url:
            return
        if "://" not in url:
            url = "https://" + url
        self.address.delete(0, tk.END)
        self.address.insert(0, url)
        self._set_page("Loading...")
        if add_history:
            self.history = self.history[: self.history_index + 1]
            self.history.append(url)
            self.history_index += 1
        self._update_navigation()
        threading.Thread(target=self._fetch, args=(url,), daemon=True).start()

    def _fetch(self, url: str) -> None:
        try:
            request = Request(url, headers={"User-Agent": "AlinuxBrowser/0.1"})
            with urlopen(request, timeout=15) as response:
                content_type = response.headers.get_content_type()
                data = response.read(2_000_000)
                charset = response.headers.get_content_charset() or "utf-8"
                text = data.decode(charset, errors="replace")
            if content_type == "text/html":
                parser = _PageParser()
                parser.feed(text)
                runs = parser.runs
            else:
                runs = [(text, None)]
            self.root.after(0, lambda: self._render(url, runs))
        except Exception as exc:  # noqa: BLE001 - display network errors in the page
            error = str(exc)
            self.root.after(0, lambda: self._set_page(f"Could not load {html.escape(url)}\n\n{error}"))

    def _render(self, url: str, runs: list[tuple[str, str | None]]) -> None:
        self.page.configure(state=tk.NORMAL)
        self.page.delete("1.0", tk.END)
        for index, (text, target) in enumerate(runs):
            tag = f"link_{index}" if target else None
            if tag:
                self.page.tag_configure(tag, foreground="#1769aa", underline=True)
                self.page.tag_bind(tag, "<Button-1>", lambda _event, href=target: self.navigate(urljoin(url, href)))
            self.page.insert(tk.END, text, tag)
        self.page.configure(state=tk.DISABLED)
        self.root.title(f"Alinux Browser - {url}")

    def _set_page(self, text: str) -> None:
        self.page.configure(state=tk.NORMAL)
        self.page.delete("1.0", tk.END)
        self.page.insert("1.0", text)
        self.page.configure(state=tk.DISABLED)

    def back(self) -> None:
        if self.history_index > 0:
            self.history_index -= 1
            self.navigate(self.history[self.history_index], add_history=False)

    def forward(self) -> None:
        if self.history_index + 1 < len(self.history):
            self.history_index += 1
            self.navigate(self.history[self.history_index], add_history=False)

    def reload(self) -> None:
        if self.history_index >= 0:
            self.navigate(self.history[self.history_index], add_history=False)


def main() -> int:
    root = tk.Tk()
    AlinuxBrowser(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
