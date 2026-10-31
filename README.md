# fscss (Python)

[![PyPI](https://img.shields.io/pypi/v/fscss.svg)](https://pypi.org/project/fscss/)
[![Python versions](https://img.shields.io/pypi/pyversions/fscss.svg)](https://pypi.org/project/fscss/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A Python interface to **FSCSS** (Figured Shorthand CSS). It packages the
official Node compiler (`xfscss`) and drives it from Python, so you can compile
`.fscss` files from build scripts, web frameworks, or the command line without
writing JavaScript.

---

## FSCSS and this package

**FSCSS** is the upstream CSS preprocessor. It extends plain CSS with property
shorthands, `$variables`, `@define` mixins, `@import` modules, arrays, events,
and other transforms. The compiler is JavaScript (`xfscss`, npm package
`fscss`), maintained by [Figsh](https://github.com/Figsh) under
[fscss-ttr](https://github.com/fscss-ttr); the language was conceived by
Ekuyik Sam. Docs: <https://fscss.devtem.org/>.

**This package** is a Python distribution, maintained by
[Omonire](https://github.com/Omonire). It does **not** reimplement FSCSS in
Python. It ships a pinned copy of the upstream compiler and runs it with Node:

```
style.fscss ──► Python API / CLI (fscss)
                  │
                  │  fscss/core.py
                  │  node fscss/_vendor/xfscss/bin/fscss.js style.fscss style.css
                  ▼
             xfscss 1.2.6 (Node) ──► style.css
```

Consequences of this design:

| | |
|---|---|
| Language parity | Exactly the vendored upstream version (`1.2.6`). New upstream releases must be re-vendored. |
| Runtime | Node.js is required and is **not** bundled or installed for you. |
| Overhead | One `node` process per compile. Fine for build steps; not a hot-reload daemon. |
| Python surface | API, CLI, file discovery, watching, and Flask/Django helpers on top of the compiler. |
| Network | Only needed for FSCSS remote imports (`https://…` or registry names). Local files compile offline. |

---

## Requirements

- **Python 3.7+** (metadata; CI covers 3.8–3.12)
- **Node.js 20+** on `PATH` as `node` or `nodejs`

Node 20+ is required because the vendored engine uses global `fetch` (18+) and
`Array.prototype.toReversed()` (20+).

## Installation

```bash
pip install fscss
```

From source:

```bash
git clone https://github.com/Omonire/fscss-py
cd fscss-py
pip install -e ".[dev]"
```

---

## Quick start

`style.fscss`:

```fscss
$accent: #8f6bff;

@define card(sel:.card) {
  `@use(sel) {
    px: 16px;
    py: 14px;
    rounded: 12px;
    stack: 12px;
  }`
}

body {
  bg: #0b0a13;
  color: $accent!;
}

@card(.panel)
```

```python
import fscss

fscss.compile_file("style.fscss", "style.css")
```

```bash
fscss style.fscss style.css
```

## CLI

```bash
fscss input.fscss [output.css]   # output defaults to input.css
fscss input.fscss --watch        # recompile on change (1s polling)
fscss --version
```

The CLI prints the compiler's combined stdout/stderr and exits non-zero only
when the compiler process itself fails.

## Python API

```python
import fscss
```

| Function | Returns | Notes |
|---|---|---|
| `compile_file(input_path, output_path, *, cwd=None, timeout=None)` | `str` | Runs the compiler; returns combined stdout/stderr (warnings included). Raises `RuntimeError` on failure or timeout. |
| `compile_string(source, *, input_dir=".", output_path=None, timeout=None)` | `str` | Compiles from a string. Without `output_path`, returns the CSS. Warnings are **not** returned. |
| `compile` | alias of `compile_file` | Kept for convenience. |
| `compile_dir(directory, recursive=True)` | `list[tuple[Path, Path]]` | Compiles every `.fscss` to a sibling `.css`. |
| `iter_fscss(directory, recursive=True)` | `list[Path]` | Sorted discovery helper. |
| `watch_dir(directory, interval=1.0, callback=None)` | `threading.Thread` | Daemon thread; recompiles changed files. |
| `init_flask(app=None, *, directory=None, watch=None)` | `None` | Compiles the static folder; watches when `app.debug` is true. |
| `init_django(directory=None)` | `None` | Compiles `<BASE_DIR>/static` by default. |

### Examples

```python
import fscss

# String → CSS
css = fscss.compile_string("$c: red;\nbody{ color: $c!; }")
# :root{--c: red;}
# body{ color: var(--c); }

# Whole directory
for src, out in fscss.compile_dir("static"):
    print(f"{src} -> {out}")
```

Flask:

```python
from flask import Flask
import fscss

app = Flask(__name__)
fscss.init_flask(app)          # compile now, watch in debug
```

Django (`AppConfig.ready()`):

```python
import fscss

fscss.init_django()
```

---

## FSCSS syntax at a glance

Full language reference: <https://fscss.devtem.org/>.

```fscss
/* variables first — declarations after a one-line rule are dropped (see below) */
$c: red;

/* shorthands */
.card {
  px: 16px;
  py: 14px;
  rounded: 12px;
  shadow: 0 8px 24px rgba(0,0,0,.35);
}

.box { color: $c!; }          /* → var(--c) */

/* reusable mixins */
@define center(elem) {
  `@use(elem) { display: flex; align-items: center; }`
}
@center(.hero)

/* selective imports */
@import((card, button) from "./ui.fscss")
```

---

## Semantics and limitations

These are properties of the current wrapper and the vendored engine; they are
worth knowing before you file a bug.

- **The engine is a regex pipeline, not an AST parser.** Syntax it does not
  recognize is passed through unchanged. A typo may produce invalid CSS rather
  than a compile error.
- **Shorthand families need a trailing semicolon.** `bg: red;` expands, but
  `body{bg:red}` (no `;`) is left untouched. The short aliases (`m`, `px`,
  `rounded`, …) also accept a closing `}`.
- **There is no `c:` shorthand.** Use `color: …`.
- **`$var` handling is line-based and order-sensitive.** Declare variables
  before any rule, and put braces on their own lines. A declaration placed
  after a one-line rule (`.card { px: 16px; }`) is silently dropped, leaving
  `var(--c)` undefined. Putting a usage on its own line inside a block can also
  inline the raw value instead of emitting `var(--c)`.
- **Warnings are easy to lose.** The compiler usually exits `0` even when it
  warns. `compile_file` returns that output, but `compile_string` returns only
  the CSS.
- **Relative imports** resolve against the input file's directory (or `cwd` for
  `compile_string`).
- **Not thread-safe by design:** each call spawns a separate Node process, so
  calls do not share engine state. `watch_dir` runs compiles on one thread.
- **`@define` bodies containing braces must be quoted/backticked.**
- **Upstream bugs exist** (e.g. `@arr.x!+[…]` raises, `$/var || fallback` is
  broken in 1.2.6). Report engine semantics upstream; report wrapper behavior
  here.

---

## Development

```bash
pip install -e ".[dev]"

pytest -q            # test suite
ruff check .         # lint
mypy fscss           # types
```

CI runs lint plus the test suite on Ubuntu and Windows across Python
3.8–3.12, builds the wheel/sdist, and runs `twine check`.

Layout:

```
fscss/
├── core.py          # subprocess bridge to the Node compiler
├── cli.py           # argparse CLI
├── integrations.py  # directory/watcher/Flask/Django helpers
└── _vendor/xfscss/  # pinned upstream compiler (1.2.6)
```

To update the engine, replace `_vendor/xfscss` with a new upstream release,
update the version notes here, and re-run the suite.

---

## Try it and tell us what breaks

This is an early (`0.1.0`) wrapper and real-world reports are the fastest way
to harden it. Please:

1. `pip install fscss`
2. Compile one of your existing `.fscss` files (CLI and Python API).
3. Open an issue at <https://github.com/Omonire/fscss-py/issues> with:
   - `fscss --version`, Python version, OS, `node --version`
   - a minimal `.fscss` input and the actual output
   - whether the same input compiles with upstream `fscss`/the IDE

Upstream project: <https://github.com/Figsh/xfscss> ·
Docs: <https://fscss.devtem.org/> ·
Modules: <https://github.com/fscss-ttr/fscss-modules>

## License

MIT — see [LICENSE](LICENSE). The vendored compiler is MIT © Figsh; see
`fscss/_vendor/xfscss/LICENSE`.
