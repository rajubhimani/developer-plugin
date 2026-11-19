"""Allow `python -m {{package}}`; runs the same function as the installed command."""

from {{package}}.cli import main

raise SystemExit(main())
