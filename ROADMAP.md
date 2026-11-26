# fscss (Python) — Roadmap

Positioning: **FSCSS is the CSS preprocessor for Python web apps.** Semantic
mixins, design tokens, and compile-time logic that compile to plain CSS — no
runtime, no class bloat, and eventually no Node.js requirement.

This is not a plan to clone Tailwind. It is a plan to win the niche Tailwind
cannot serve well: Python-first, zero-runtime, semantic CSS.

Current baseline: `0.1.0` on PyPI, vendored `xfscss 1.2.6`, Python API/CLI,
Flask/Django helpers, CI on Python 3.8–3.12 (Ubuntu + Windows), 36 tests.
The CLI now includes `init`, `doctor`, `build`, `clean`, `env`, `report`, and
`completion`; `init` can install Node through the platform package manager.

---

## Guiding principles

1. **Never silently succeed.** Every compiler warning is either surfaced or
   explicitly suppressed. Exit codes are meaningful.
2. **Plain CSS out.** No runtime, no injected style tags, no build lock-in.
3. **Python is the product.** Node is an implementation detail to be removed.
4. **Parity before invention.** Match the vendored engine on a fixture corpus
   before adding new language features.
5. **Small, boring releases.** Semver, changelog, deprecation policy.

---
## Pre Phase
Before going into any phase, please @Omonire take note that we need to make a version of `pip install fscss`  ask and check for the user after successful installation, use `fscss doctor` to check if the Machine of the user meets the requirements of `FSCSS` Devtemple[https://devtemple.com]
## Phase 0 — Foundation (v0.2)

Goal: make failures visible and the package trustworthy.

### 0.1 Structured diagnostics

The vendored engine writes warnings to stderr and usually exits `0`.
`compile_string` currently drops that output.

- Add `fscss.CompileResult` (or a `strict`/`on_warning` option) exposing
  `css`, `warnings`, `output`.
- `compile_file` keeps returning `str` for compatibility; add
  `compile_file_result` (or `capture=True`).
- CLI: `--strict` (warnings → exit 2), `--quiet`, `--json`.
- Detect engine failure comments (`/* Failed import: … */`,
  `/* Can't import … multiple times */`) and surface them as warnings.

**Acceptance:** a file with a failed import prints a clear message and exits
non-zero under `--strict`.

### 0.2 `--check` mode

- `fscss input.fscss --check` compiles to a temp file and compares with the
  existing `.css`; exits `1` on drift without writing.
- Same behavior for `compile_dir(..., check=True)`.

**Acceptance:** `--check` usable in CI and pre-commit.

### 0.3 Correct tests

Current tests accept invalid FSCSS (`h1{c:blue}`, `body{bg:red}`) and only
assert that output contains a substring.

- Replace with valid fixtures and assert exact output.
- Add a parity corpus under `tests/fixtures/` covering: shorthands, `$vars`,
  `@define` (quoted and unquoted bodies), `@import` (selective, wildcard,
  `as`), `@arr`, `@event`, `num()`, `count()`, `pattern()`.
- Add a regression test for the `$var`-after-one-line-rule bug documented in
  the README.

**Acceptance:** every test compiles real FSCSS and compares full CSS.

### 0.4 Packaging hygiene

- Add `fscss/py.typed` and include it in `pyproject.toml`/`MANIFEST.in`.
- Verify wheel contents include the full vendor tree on Windows and Linux.
- Decide on Python floor: 3.7/3.8 are EOL; recommend `>=3.9` for 0.2.

**Acceptance:** `pip install` from a clean wheel compiles a file on all CI
targets.

---

## Phase 1 — Remove the Node requirement (v0.3)

Goal: `pip install fscss` and compile with no Node.js installed.

### 1.1 Engine strategy spike

Evaluate, in order:

| Option | Pros | Cons |
|---|---|---|
| Pure-Python port of `xfscss` | No runtime, fast startup, debuggable | Large effort; must track upstream |
| Pyodide/WASM build of the JS engine | Close parity, no Node binary | Large wheel; slow cold start |
| Bundle a Node binary | Fast parity | Big wheels, platform matrix, licensing |
| Keep Node, auto-install | Minimal work | Poor UX, security concerns |

Deliverable: a short decision record (`docs/engine-decision.md`) with
benchmarks: cold start, warm compile of 100 files, wheel size, parity score.

### 1.2 Engine abstraction

- Introduce `fscss/_engine/` with a stable interface
  (`compile(source, input_dir) -> (css, warnings)`).
- `NodeEngine` wraps the current subprocess path.
- Add the chosen backend behind the same interface; auto-select at runtime
  with an env override (`FSCSS_ENGINE=node|native`).
- Keep the vendored tree as the reference implementation.

**Acceptance:** the parity corpus passes on both engines; the native engine is
the default when available.

### 1.3 Performance

- Avoid writing temp files for `compile_string` where the engine allows it.
- Reuse a persistent engine process/worker for `compile_dir` and watch mode
  (amortize startup).
- Add `--jobs` for parallel directory compilation.

**Targets:** 100 files < 2s warm; cold start < 500ms with the native engine.

---

## Phase 2 — Framework integrations (v0.3–0.4)

Goal: FSCSS feels native in Python web projects.

### 2.1 Django

- `FscssFinder` for `STATICFILES_FINDERS` (compile on collectstatic).
- `AppConfig.ready()` opt-in with a guard against running during migrations.
- Management commands: `manage.py fscss compile`, `manage.py fscss watch`,
  `manage.py fscss check`.
- Respect `STATIC_ROOT`/`STATIC_URL`, `--dry-run`, `--clear`.

### 2.2 Flask

- `flask fscss compile|watch|check` CLI group.
- Hook into the reloader so debug mode recompiles once per change (debounced).
- `init_flask(app, watch=None)` stays, but delegates to the new CLI helpers.

### 2.3 FastAPI / Starlette

- `fscss.init_fastapi(app, directory="static")` startup hook.
- Optional `FscssStaticFiles` wrapper that compiles on first request in dev.

### 2.4 Caching

- Manifest (`.fscss-cache.json`) keyed by source path + mtime + size + engine
  version; skip unchanged files.
- Atomic writes (temp file + `os.replace`) so servers never serve half a file.
- Content hash helper for cache-busting URLs.

**Acceptance:** runnable `examples/django`, `examples/flask`, `examples/fastapi`
apps, each exercised in CI.

---

## Phase 3 — Tooling (v0.4–0.5)

Goal: make FSCSS feel like a language, not a script.

- **LSP server** (`fscss lsp`): diagnostics from the engine, completion for
  shorthands/`@define` names, go-to-definition for `@import`, hover docs.
- **Formatter** (`fscss fmt`): normalize shorthand expansion and property
  order; `--check` mode.
- **Source maps**: line-level mapping from `.fscss` to `.css` (stretch; the
  regex engine has no AST, so start with line spans from `@define` expansion).
- **Editor support**: reuse the upstream VS Code grammar; publish a Python
  package that ships the grammar for other editors.

**Acceptance:** VS Code shows an inline error for a failed import and completes
`@define` names from imported modules.

---

## Phase 4 — Ecosystem (v1.0)

Goal: an offline-first module ecosystem distributed through PyPI.

- **PyPI module packs**: `fscss-st-core`, `fscss-overlapui`, etc., each
  exposing `.fscss` files via package data.
- **Resolver**: `@import((*) from st-core)` resolves installed packages before
  falling back to the jsDelivr registry; `FSCSS_OFFLINE=1` forbids network.
- **Lockfile**: record module versions and content hashes for reproducible
  builds.
- **Component gallery**: real examples (cards, nav, forms, charts) with
  compiled output and size.
- **Tailwind migration guide**: map common utility patterns to FSCSS
  `@define`/tokens, and show the output-size difference.
- **Benchmarks page**: build time, output size, runtime bytes (zero).

**Acceptance:** a project can `pip install fscss-st-core` and compile with no
network access.

---

## Phase 5 — Community and positioning (ongoing)

- Docs site with a "FSCSS for Python" landing page and framework quick starts.
- `CHANGELOG.md`, semver policy, deprecation windows.
- Issue templates that request engine version, Node/Python versions, and a
  minimal repro.
- Compatibility matrix: Python × OS × engine.
- Upstream relationship: track `xfscss` releases, re-vendor, and contribute
  fixes for engine bugs found here (e.g. `@arr.x!+[…]`, `$/var || fallback`).

---

## Success metrics

| Metric | Target |
|---|---|
| Install → first compiled CSS | < 60s, no Node |
| 100-file compile (warm) | < 2s |
| Silent failures | 0 (every warning surfaced or explicitly suppressed) |
| Parity on upstream fixtures | 100% |
| Output size vs Tailwind (3 sample pages) | ≤ Tailwind |
| Supported Python | 3.9–3.13 |
| CI platforms | Ubuntu, Windows, macOS |

---

## Non-goals

- Utility-class parity with Tailwind (`flex`, `items-center`, …).
- A runtime CSS-in-JS layer or browser auto-scan (that is upstream's job).
- A bundler or dev server of our own.
- Reimplementing the language differently from upstream. Parity first.

---

## How this maps to the current code

| Area | Today | Phase |
|---|---|---|
| Compiler bridge | `fscss/core.py` (`compile_file`, `compile_string`, `compile`) | 0, 1 |
| CLI | `fscss/cli.py` (`compile`, `watch`, `init`, `doctor`, `build`, `clean`, `env`, `report`, `completion`) | 0, 3 (`lsp`, `fmt`) |
| Environment | `fscss/environment.py`, `fscss/node_install.py` (Node detection + package-manager install) | 0 |
| Integrations | `fscss/integrations.py` (`compile_dir`, `watch_dir`, `init_flask`, `init_django`) | 2 |
| Engine | `fscss/_vendor/xfscss` (1.2.6) | 1 |
| Packaging | `pyproject.toml` (`packages = ["fscss"]`), `MANIFEST.in` | 0, 4 |
| CI | `.github/workflows/test.yml` (3.8–3.12, Node 20) | 0, 5 |
| Tests | `tests/test_core.py`, `tests/test_cli.py`, `tests/test_environment.py`, `tests/test_node_install.py`, `tests/test_cli_commands.py` | 0 |

---

## Risks

- **Upstream fragility.** The engine is a regex pipeline; behavior can change
  between versions. Mitigation: fixture corpus + pinned vendor + decision
  record.
- **Engine port scope.** A pure-Python port is the largest single bet. Timebox
  the spike and keep `NodeEngine` as the fallback.
- **Feature creep.** Every new language feature widens the parity gap.
  Mitigation: parity gate before invention.
- **Packaging weight.** WASM/Node bundling inflates wheels. Measure before
  committing.

---

Engineered and Written by Omonire
