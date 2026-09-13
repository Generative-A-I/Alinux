"""Allow Alinux to run with ``python -m alinux``."""

from .main import main

if __name__ == "__main__":
    raise SystemExit(main())