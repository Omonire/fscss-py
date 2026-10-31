# fscss Roadmap

This document covers two tracks:

1. **v1 maintenance** - keep the published `0.1.x` line healthy while v2 is designed.
2. **v2 ideas** - the direction for the next major version.

Current state: `0.1.0` is published on PyPI and the CI matrix is green across Python 3.8-3.12 on Ubuntu and Windows.

---

## v1 maintenance

The v1 line is a thin wrapper around the vendored Node compiler in `fscss/_vendor/xfscss`. The goal is stability, not new features.

### Release hygiene

- **Patch releases only.** Bump to `0.1.x` for fixes; no new APIs in v1.
- **PyPI is immutable.** A version can never be reused. Always bump `pyproject.toml` before re-tagging.
- **Tag = version.** The Git tag must match `pyproject.toml` and the GitHub release title.
- **Releases are cut from `main` only.** Do not tag a branch.
- Publishing runs through `.github/workflows/publish.yml` using PyPI trusted publishing (OIDC), triggered by a published GitHub release. No API token is stored in the repo.

### CI guarantees

- `.github/workflows/test.yml` must stay green on the full matrix (Ubuntu + Windows, Python 3.8-3.12).
- The `lint` job runs `ruff` and `mypy`. Do not merge with lint failures.
- Every release build must pass `python -m build` and `twine check dist/*`.
- Keep the workflow checkout clean: never commit a nested git checkout as a gitlink. Root `xfscss/` is ignored and must stay untracked. The only compiler copy that ships is `fscss/_vendor/xfscss`.

### Known v1 constraints (accepted, not fixed in v1)

- Node.js is required at runtime. `_find_node()` looks for `node`/`nodejs` in `PATH`.
- Errors are surfaced as a single `RuntimeError` string containing combined stdout/stderr; there is no line/column metadata.
- `compile_dir` recompiles every file on every call; no cache.
- `watch_dir` polls file mtimes instead of using OS file events.
- The CLI handles one input file at a time.

### v1 checklist for each fix

1. Reproduce with a test in `tests/`.
2. Keep Python 3.8 compatibility (this line still supports 3.8; 3.7 support is declared but untested).
3. Run `pytest`, `ruff check fscss tests`, `mypy fscss`.
4. Update `README.md` if behavior is user-visible.
5. Commit with a scoped message, push to `main`, confirm CI is green.
6. For a release: bump version, tag, publish the GitHub release, confirm the PyPI upload.

### v1 support window

- v1 receives security and correctness fixes until v2.0.0 ships.
- After v2.0.0, v1 gets critical fixes only for one minor cycle, then is archived.

---

## v2 ideas

v2 targets the two things most likely to make a new user bounce: the Node.js runtime requirement and the lack of actionable error output. Everything else is secondary.

### 1. Remove the Node.js dependency

This is the highest-impact change. Options, cheapest to hardest:

- **Bundle Node in platform wheels.** `pip install` just works; cost is roughly 40 MB per platform wheel.
- **Embed a JS engine.** Run the vendored JS through QuickJS (`quickjs` / `py_mini_racer`). Smaller than Node, but needs compatibility testing against the full compiler.
- **Port the compiler to Python.** Largest effort, but removes the JS dependency entirely. `fscss/_vendor/xfscss/lib/functions/shorthands.js` is the behavioral spec.

Decision point: start with bundled Node to ship fast, keep the JS engine and pure-Python ports as follow-ups.

### 2. Structured errors

Replace `RuntimeError(stdout)` with a typed exception:

- `FscssError` carrying `file`, `line`, `column`, `code`, `message`
- separate `stdout` and `stderr` instead of a merged blob
- preserve the process exit code
- make it machine-readable for editors and CI

### 3. CLI overhaul

- Directory mode: `fscss src/ -o dist/`
- stdin/stdout: `fscss -` and `--stdin`
- `--check`: exit non-zero when output differs from disk (CI and pre-commit friendly)
- `--minify`, `--sourcemap`, `--quiet`, `--json` diagnostics
- subcommands: `fscss build`, `fscss watch`, `fscss check`
- `fscss.toml` project config
- real watch mode with debounce and OS file events instead of mtime polling

### 4. Build-system integration

- A build hook for setuptools/hatch that compiles `*.fscss` into the wheel so packages never ship stale CSS.
- A pre-commit hook entry point.

### 5. Packaging and typing

- Drop Python 3.8 (EOL); add 3.13 to the matrix.
- Ship `py.typed` and inline types; stop relying on `ignore_missing_imports`.
- Switch `pyproject.toml` from a hardcoded `packages = ["fscss"]` to package discovery so subpackages are included automatically.
- Stop committing build output and scratch files (`dist/`, `*.egg-info/`, `out_*.css`, `test*.fscss`).

### 6. Caching and incremental builds

- Content-hash cache keyed by source + compiler version so `compile_dir` only rebuilds changed files.
- Track `@import` dependencies so a changed partial recompiles its dependents.

### 7. Framework integrations

- Keep `init_flask` and `init_django`, but add an ASGI variant and a dev-server hook.
- Compile once at startup in production; watch only in debug.

### Suggested v2 scope for the first release

Bundled Node runtime, structured errors, and the `--check` plus directory-mode CLI. That is shippable in one release and removes the two biggest friction points.

### v2 exit criteria

- `pip install fscss` works on a machine with no Node.js.
- Every compiler failure reports a file and line.
- CI can run `fscss --check` against a directory and fail on drift.
- Full test matrix green on the supported Python versions.
