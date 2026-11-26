# FSCSS for VS Code

Yes — FSCSS has an official Visual Studio Code extension. It gives you syntax
highlighting, snippets, and compilation for `.fscss` / `.xfscss` files, so you
can write FSCSS with editor support instead of plain text.

- **Marketplace:** [FSCSS on the VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=Figsh.fscss)
- **Extension ID:** `Figsh.fscss`
- **Source:** [Figsh/fscss-vscode-extension](https://github.com/Figsh/fscss-vscode-extension)

---

## Install the extension

Pick whichever method you prefer.

### Option 1 — VS Code UI

1. Open VS Code.
2. Open the Extensions view with `Ctrl+Shift+X` (`Cmd+Shift+X` on macOS).
3. Search for **FSCSS**.
4. Select the extension published by **Figsh** and click **Install**.

### Option 2 — Quick Open

1. Press `Ctrl+P` (`Cmd+P` on macOS).
2. Paste the following and press Enter:

   ```
   ext install Figsh.fscss
   ```

### Option 3 — Command line

If the `code` command is on your `PATH`:

```bash
code --install-extension Figsh.fscss
```

### Option 4 — From a VSIX file

Download the `.vsix` from the Marketplace or the GitHub releases, then run:

```bash
code --install-extension fscss-<version>.vsix
```

---

## Requirements

The extension provides editing support on its own, but its **compile** features
need an FSCSS compiler available on your machine.

1. **Node.js 20+** — required by the compiler.
2. **An FSCSS compiler**, one of:
   - the Node package: `npm install -g fscss`
   - this Python package: `pip install fscss` (vendors the compiler and exposes `fscss` on your PATH)

Verify your setup:

```bash
node --version   # v20 or newer
fscss --version
fscss doctor     # environment check (Python package)
```

> If you already installed `fscss` with pip, you do **not** need a separate
> global npm install just to edit files. The extension's built-in compile
> command looks for the FSCSS compiler; if it cannot find one, compile from the
> terminal with `fscss style.fscss style.css` instead.

---

## What the extension gives you

### Syntax highlighting

Full FSCSS-aware highlighting for:

- `@define`, `@fun`, `@obj`, `pattern()`
- `@import`, `@use`, `@match`, `@ext`
- `@arr`, `@event`, `@random`
- functions such as `exec()`, `num()`, `rpt()`, `copy()`, `count()`, `inline()`
- shorthand helpers such as `%2(...)`
- variables such as `$color`
- array methods such as `.randint`, `.list`, `.join`, `.length`, `.reverse`

It works alongside regular CSS, so `.fscss` files containing plain CSS still
look normal.

### Snippets

Type a trigger and press Tab. A few of the most useful ones:

| Trigger | Inserts |
|---|---|
| `def` | `@define` block |
| `defc` | call a defined block |
| `fun` | `@fun` style store |
| `obj` | `@obj` style object |
| `use` | `@use(...)` inside a define |
| `imp` / `impm` / `impa` / `impw` / `impr` | import forms (single, multi, alias, wildcard, URL) |
| `var` / `varu` | declare / use a variable |
| `str` / `stru` | create / use a string store |
| `arr` / `arrl` / `arrr` / `arrri` | arrays and loops |
| `ajon` / `arls` / `rand` / `randa` | join and random helpers |
| `num` / `cou` / `rpt` / `cpy` / `ext` | math, ranges, repeat, copy, extract |
| `even` | `@event` conditional logic |
| `key` / `keym` / `attr` | keyframes and attribute selectors |
| `exe` / `exew` | `exec()` debug log / warn |

### Compile from the editor

1. Open a `.fscss` file.
2. Open the Command Palette with `Ctrl+Shift+P` (`Cmd+Shift+P` on macOS).
3. Run **FSCSS: Compile**.

The extension reads the current file, runs the compiler, and writes the CSS
output (for example `style.fscss` → `style.css`).

### Compile on save

With auto-compile enabled, saving a `.fscss` file rebuilds its `.css` sibling
automatically:

```
style.fscss  ──save──►  style.css
```

That makes the extension a lightweight watch mode while you work.

---

## Typical workflow

1. Install the extension (`Figsh.fscss`).
2. Install Node.js 20+ and an FSCSS compiler (`pip install fscss` or `npm install -g fscss`).
3. Open or create a file ending in `.fscss`.
4. Write FSCSS — the status bar/language mode should show **FSCSS**, and
   highlighting should be active.
5. Compile with **FSCSS: Compile** or let save-on-compile run.
6. Link the generated `.css` from your HTML or framework template.

```html
<!-- Ship the compiled CSS, not the .fscss file -->
<link rel="stylesheet" href="style.css">
```

---

## Troubleshooting

**No syntax highlighting / language is "Plain Text"**

- Confirm the file extension is `.fscss` or `.xfscss`.
- Click the language name in the status bar and choose **FSCSS**.
- Reload the window: Command Palette → **Developer: Reload Window**.

**"FSCSS: Compile" does nothing or reports a missing compiler**

- Make sure `node --version` reports v20 or newer.
- Make sure `fscss --version` works in a terminal.
- Restart VS Code so it picks up a newly installed compiler / updated `PATH`.
- As a fallback, compile from the terminal:

  ```bash
  fscss style.fscss style.css
  ```

**Compiles in the terminal but not in VS Code**

VS Code may have started before `PATH` was updated. Fully quit and reopen it,
or set `FSCSS_NODE` to the Node executable if Node lives in a non-standard
location.

**Editor shows normal CSS colors only**

The file is probably being treated as CSS. Set the language mode to **FSCSS**,
then check that the extension is installed and enabled for this workspace.

**Python users:** run `fscss doctor` first. It checks Python, Node.js, the
vendored engine, write access, and available package managers, and tells you
what is missing.

---

## Links

- Marketplace: <https://marketplace.visualstudio.com/items?itemName=Figsh.fscss>
- Extension source: <https://github.com/Figsh/fscss-vscode-extension>
- FSCSS docs: <https://fscss.devtem.org/>
- Language repo: <https://github.com/fscss-ttr/FSCSS>
- npm package: <https://www.npmjs.com/package/fscss>
- Python package: <https://pypi.org/project/fscss/>
- Python docs / hub: <https://hub.devtem.org/python-compiler>
- Python FSCSS -> Python Extension: <https://github.com/omonire/fscss-py>
---

Engineered and Written by Omonire
