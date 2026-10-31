# Introduction

`fscss` (Python) is a Python wrapper for **FSCSS** (Figured Shorthand CSS), a lightweight CSS preprocessor that compiles shorthand syntax down to plain, dependency-free CSS. This package vendors the official FSCSS Node.js compiler (`xfscss`) and exposes it through a small Python API and CLI, so Python projects can compile `.fscss` files without pulling in the Node toolchain themselves.

This library exists because two developers built two halves of the same idea.

## Omonire - Python wrapper

Omonire authors and maintains this Python package. That covers the public API (`compile`, `compile_file`, `compile_string`), the CLI, the framework integrations for Flask and Django, packaging, and the release pipeline that publishes to PyPI.

The design goal is deliberately thin: keep full behavioral compatibility with upstream FSCSS, add Python-native ergonomics, and never fork the compiler.

- GitHub: [Omonire](https://github.com/Omonire)
- Package: [pypi.org/project/fscss](https://pypi.org/project/fscss/)

## Figsh - FSCSS and the upstream compiler

Figsh is the developer behind FSCSS and its official compiler, published under **Figsh Development**. The language, the `xfscss` engine vendored in `fscss/_vendor/xfscss`, the npm package, the browser runtime, and the VS Code extension all come from that work.

This wrapper only exists because the upstream compiler is stable and well documented. Any credit for the language itself belongs there.

- Site: [fscss.devtem.org](https://fscss.devtem.org/)
- GitHub: [Figsh](https://github.com/Figsh) / [Figsh/xfscss](https://github.com/Figsh/xfscss)
- npm: [npmjs.com/package/fscss](https://www.npmjs.com/package/fscss)
- Writing: [dev.to/figsh](https://dev.to/figsh)

## A short history of FSCSS

FSCSS (Figured Shorthand Cascading Style Sheet) was conceived in 2022 by **Ekuyik Sam**, with early development carried out by Figsh. The first work focused on the shared-value shorthand methods (`%2` through `%6`, `%i`) and basic variable handling with `$name: value`.

Since then the language has grown to include `copy()`, `@define` parameterized blocks, arrays and loops, `@event` conditionals, `pattern()` semantic matching, compile-time property shorthands such as `size`, `px`, `inset-x`, and `ratio-fit()`, and consolidated browser entry points (`runtime.js` and `esm.js`).

FSCSS is published under Figsh Development as the `fscss` package on npm and maintained through the `fscss-ttr` organization on GitHub.

## How the two halves fit together

| Layer | Maintainer | What it does |
| --- | --- | --- |
| FSCSS language and `xfscss` compiler | Figsh | Parses `.fscss` and emits standard CSS |
| `fscss` Python package | Omonire | Vendors the compiler and wraps it for Python and the CLI |

If a stylesheet compiles incorrectly, the bug is almost always upstream in `xfscss`. If the Python API, CLI, or packaging misbehaves, it is this repository.

## Credits

- FSCSS language and compiler: Figsh / Figsh Development
- Original concept: Ekuyik Sam
- Python wrapper, CLI, and integrations: Omonire

FSCSS is MIT licensed. This wrapper is MIT licensed as well.
