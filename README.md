# Alinux

Alinux is an AI orchestration shell for a minimal Debian 12 desktop running
Fluxbox. It converts natural-language requests into a small, validated set of
desktop actions.

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade --no-cache-dir --index-url https://pypi.org/simple 'alinux[openai]'
python -c "import alinux; print(alinux.__version__)"
```

On a fresh Debian 12 Fluxbox installation, the complete setup is:

```bash
python -m pip install alinux
alinux setup
```

`alinux setup` installs Tkinter, desktop control tools, Ollama,
starts the Ollama service, and downloads the lightweight `smollm2:360m` model.
It may ask for your sudo password.

The base package has no compiled model dependency. Use `python -m pip install
alinux` when running without an LLM, or install the `openai` extra for OpenAI,
Groq, and other OpenAI-compatible providers.

When no API key is configured, Alinux uses Ollama's local JSON-schema API
instead of stopping. Install Ollama, start it, and download the lightweight
default model:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull smollm2:360m
alinux
```

Set `ALINUX_LOCAL_MODEL` to use another model already installed in Ollama.

Alinux includes a small browser built from Python's standard library. It uses
Tkinter, `urllib`, and `html.parser`, with no Chromium, Firefox, WebKit, Qt, or
other browser engine. It supports navigation, back/forward, reload, links,
HTML text, and basic HTTP(S) pages. JavaScript, plugins, and advanced CSS are
not supported by this intentionally lightweight engine.

```bash
sudo apt install python3-tk
```

For model access, export a key and optionally choose a provider/model. Any
OpenAI-compatible API can be configured with a custom endpoint:

```bash
export ALINUX_API_KEY='your-key'
export ALINUX_MODEL='gpt-4o-mini'
export ALINUX_API_BASE_URL='https://your-provider.example/v1'
```

To use the built-in Groq/Llama configuration from the command line, set your
Groq key and pass the flag:

```bash
export GROQ_API_KEY='your-groq-key'
alinux --use-default-groq-api
```

The flag selects `llama-3.3-70b-versatile` and Groq's API endpoint. It does
not embed or fetch a secret key.

Groq is supported directly, including Alinux's built-in open model preset:

```bash
export ALINUX_PROVIDER='groq'
export ALINUX_API_KEY='your-groq-key'
alinux
```

With `ALINUX_PROVIDER=groq` and no model override, Alinux uses
`llama-3.3-70b-versatile` at Groq's OpenAI-compatible endpoint. You can also
select it explicitly with `ALINUX_MODEL=llama-3.3-70b-versatile`.

The desktop hooks expect `xdotool`, `amixer`, `free`, and `uptime`. Missing
tools are reported as readable responses rather than terminating Alinux.

## Run

```bash
alinux
```

Open the graphical Alinux window from a terminal with:

```bash
alinux open
```

To add **Open Alinux** to the Fluxbox desktop context menu, run this once
inside the Fluxbox session:

```bash
alinux install-fluxbox-menu
```

Remove the menu entry with:

```bash
alinux remove-fluxbox-menu
```

Then restart or reconfigure Fluxbox. The installer uses the active Python
interpreter and writes GUI errors to `~/.cache/alinux/gui.log`, so menu
launches continue to work even when Fluxbox has a minimal `PATH`. It updates
`~/.fluxbox/menu` without replacing your existing entries. The GUI requires
Debian's `python3-tk` package and a valid `DISPLAY`.

Type requests such as `show system status`, `turn the volume down`, or
`open the terminal`. Enter `quit` or press `Ctrl-D` to exit.

Alinux never executes arbitrary shell text from the model. Only the operations
listed in its system prompt and `system_controls.py` are routable.