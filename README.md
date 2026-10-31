# fscss

[![PyPI](https://img.shields.io/pypi/v/fscss.svg)](https://pypi.org/project/fscss/)
[![Python versions](https://img.shields.io/pypi/pyversions/fscss.svg)](https://pypi.org/project/fscss/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Python interface to [FSCSS](https://fscss.devtem.org/)** (Figured Shorthand CSS).

Compile `.fscss` → plain CSS from scripts, Flask/Django, or the CLI — without writing JavaScript. This package **vendors** the official Node compiler (`xfscss`) and runs it for you; it does not reimplement the language in Python.

Hub guide: [hub.devtem.org/python-compiler](https://hub.devtem.org/python-compiler)

---

## How it works

```
style.fscss
    │
    ▼
Python API / CLI  (this package)
    │
    │  node fscss/_vendor/xfscss/bin/fscss.js …
    ▼
xfscss (Node)  ──►  style.css
```

| | |
|---|---|
| **Language** | Same as upstream FSCSS (currently **1.2.6**). New engine releases are re-vendored here. |
| **Runtime** | **Node.js 20+** must be on `PATH` (`node` or `nodejs`). Not bundled. |
| **Cost** | One Node process per compile — ideal for build steps, not a hot-reload daemon. |
| **Network** | Only for remote `@import` (URLs / registry names). Local files compile offline. |

---

## Requirements

- **Python** 3.7+ (tested 3.8–3.12)
- **Node.js** 20+ (global `fetch`, `Array.prototype.toReversed()`)

```bash
node --version   # should be v20 or newer
```

---

## Install

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

**`style.fscss`**

```css
$accent: #8f6bff;

@define card(sel:.card){`
  @use(sel) {
    px: 16px;
    py: 14px;
    rounded: 12px;
    stack: 12px;
  }
`}

body {
  bg: #0b0a13;
  color: $accent!;
  ff: sans-serif;
}

@card(.panel)
```

**Python**

```python
import fscss

fscss.compile_file("style.fscss", "style.css")
```

**CLI**

```bash
fscss style.fscss style.css
```

---

## CLI

```bash
fscss input.fscss [output.css]   # default output: input.css
fscss input.fscss --watch        # recompile on change (~1s poll)
fscss --version
```

Stdout/stderr from the compiler is printed. Exit code is non-zero only if the Node process fails.

---

## Python API

```python
import fscss
```

| Function | Returns | Notes |
|----------|---------|--------|
| `compile_file(input_path, output_path, *, cwd=None, timeout=None)` | `str` | Runs the compiler; returns combined stdout/stderr (includes warnings). Raises `RuntimeError` on failure or timeout. |
| `compile_string(source, *, input_dir=".", output_path=None, timeout=None)` | `str` | From a string. Without `output_path`, returns **CSS only** (warnings not included). |
| `compile` | — | Alias of `compile_file`. |
| `compile_dir(directory, recursive=True)` | `list[tuple[Path, Path]]` | Every `.fscss` → sibling `.css`. |
| `iter_fscss(directory, recursive=True)` | `list[Path]` | Sorted discovery. |
| `watch_dir(directory, interval=1.0, callback=None)` | `threading.Thread` | Daemon thread; recompiles on change. |
| `init_flask(app=None, *, directory=None, watch=None)` | `None` | Compiles static folder; watches when `app.debug` is true. |
| `init_django(directory=None)` | `None` | Defaults to `<BASE_DIR>/static`. |

### Examples

```python
import fscss

# String → CSS
css = fscss.compile_string("$c: red;\nbody{ color: $c!; }")

# Directory
for src, out in fscss.compile_dir("static"):
    print(f"{src} -> {out}")
```

**Flask**

```python
from flask import Flask
import fscss

app = Flask(__name__)
fscss.init_flask(app)   # compile now; watch in debug
```

**Django** (e.g. in `AppConfig.ready()`)

```python
import fscss

fscss.init_django()
# or: fscss.init_django("path/to/static")
```

---

## FSCSS syntax (short)

Full language docs: [fscss.devtem.org](https://fscss.devtem.org/).

```css
/* Prefer variables before rules */
$c: red;

.card {
  px: 16px;
  py: 14px;
  rounded: 12px;
  shadow: 0 8px 24px rgba(0,0,0,.35);
}

.box { color: $c!; }

@define center(elem){`
  @use(elem) {
    display: flex;
    align-items: center;
  }
`}
@center(.hero)

@import((card, button) from "./ui.fscss")
```

Browser IDE (no Python): [fscss.devtem.org/ide](https://fscss.devtem.org/ide)

---

## Semantics & limitations

Worth knowing before filing a bug:

- **Not a full CSS AST.** Unrecognized syntax is often passed through; typos can yield invalid CSS instead of a hard error. FSCSS-oriented issues may warn; arbitrary CSS is not fully validated.
- **Shorthands need a terminator.** Prefer `bg: red;` (semicolon). Compact forms without `;` may not expand. Short aliases (`px`, `rounded`, …) also accept a closing `}`.
- **No `c:` color alias** — use `color:`.
- **`$var` is order-sensitive.** Declare variables before rules; keep braces readable. Declarations after a one-line rule can be dropped; odd line breaks can change `var(--x)` vs inlined values.
- **Warnings are easy to miss.** The compiler often exits `0` with warnings. `compile_file` returns that text; `compile_string` returns CSS only.
- **Imports** resolve relative to the input file (or `input_dir` / cwd for strings).
- **Process model:** one Node process per call — no shared engine state across threads. `watch_dir` serializes compiles on its thread.
- **`@define` bodies with braces** should use backticks / the documented quoting form.
- **Upstream engine issues** (report to [Figsh/xfscss](https://github.com/Figsh/xfscss)): e.g. some array mutation forms, `$/var || fallback` in 1.2.6. Wrapper-only bugs: [Omonire/fscss-py/issues](https://github.com/Omonire/fscss-py/issues).

---

## Development

```bash
pip install -e ".[dev]"

pytest -q
ruff check .
mypy fscss
```

CI: lint + tests on Ubuntu/Windows, Python 3.8–3.12, wheel/sdist + `twine check`.

```
fscss/
├── core.py           # subprocess bridge
├── cli.py            # argparse CLI
├── integrations.py   # dir / watch / Flask / Django
└── _vendor/xfscss/   # pinned upstream (1.2.6)
```

To bump the engine: replace `_vendor/xfscss`, update version notes, run the suite.

---

## Feedback

Early release (`0.1.x`). Real projects help most:

1. `pip install fscss`
2. Compile an existing `.fscss` file (CLI and API).
3. Open an issue with:
   - `fscss --version`, Python, OS, `node --version`
   - minimal input + actual output
   - whether the same file works in [upstream CLI](https://www.npmjs.com/package/fscss) / [IDE](https://fscss.devtem.org/ide)

**Upstream:** [Figsh/xfscss](https://github.com/Figsh/xfscss) · **Docs:** [fscss.devtem.org](https://fscss.devtem.org/) · **Modules:** [fscss-ttr/FSCSS](https://github.com/fscss-ttr/FSCSS) · **Hub (Python):** [python-compiler](https://hub.devtem.org/python-compiler)

---

## License

MIT — see [LICENSE](LICENSE).  
Vendored compiler: MIT © Figsh — see `fscss/_vendor/xfscss/LICENSE`.
