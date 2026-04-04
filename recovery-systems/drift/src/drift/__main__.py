"""Launch the DRIFT desktop shell."""

from __future__ import annotations

from drift.ui.main_window import main as _main


def main() -> int:
    """Run the DRIFT desktop application."""

    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
