# fscss (Python)

Python wrapper for [FSCSS](https://fscss.devtem.org/) (Figured Shorthand CSS). This package vendors the official FSCSS Node.js compiler (`xfscss`) and runs it via Node.js.

## Requirements

- Python >= 3.7
- Node.js >= 14 (installed and available in `PATH` as `node` or `nodejs`)

## Installation

```bash
pip install fscss
```

Or install from source:

```bash
pip install -e .
```

## Usage

### CLI

Same as the Node CLI:

```bash
fscss input.fscss output.css
```

Or just:

```bash
fscss input.fscss  # outputs input.css
```

### Python API

```python
import fscss

# Compile file
fscss.compile_file("style.fscss", "style.css")

# Compile string
css = fscss.compile_string("@c: red; body{ c: @c; }")
print(css)

# Also available as compile()
fscss.compile("style.fscss", "style.css")
```

### Flask integration (example)

```python
from flask import Flask, send_from_directory
import fscss
from pathlib import Path

app = Flask(__name__)

# Compile .fscss on startup
static = Path(app.static_folder)
fscss.compile_file(static / "style.fscss", static / "style.css")

if __name__ == "__main__":
    app.run(debug=True)
```

## Notes

- Node.js is not bundled. It must be installed on the system.
- Relative imports in `.fscss` files work the same as the original compiler.
- This keeps full compatibility with the upstream FSCSS compiler.