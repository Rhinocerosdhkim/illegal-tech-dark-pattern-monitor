# IBM Plex — self-hosted

Latin subsets pulled from Google Fonts, licence SIL OFL 1.1.

The document must render identically without a network connection: the
Beweisakte is printed to PDF locally and may be opened years later from an
archive. A webfont link would make the layout depend on a third party — and
on a screenshot-based evidence file, a font that silently falls back changes
what the printed page looks like.

| File | Family |
|---|---|
| `sans-var.woff2` | IBM Plex Sans, variable 400–600 — UI, tables, chrome |
| `mono-400.woff2`, `mono-500.woff2` | IBM Plex Mono — every number, ID, signal name, hash, statute |
| `serif-400.woff2`, `serif-600.woff2` | IBM Plex Serif — document prose meant to be read |

Embedded base64 into every generated HTML by `dpm/report/design.py`, so a
single .html file is self-contained and can be mailed as is.
