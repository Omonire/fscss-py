## Build
```bash
Remove-Item -Recurse -Force dist,build,*.egg-info -ErrorAction SilentlyContinue
python -m build
```

## Check
```bash
twine check dist/*
```

## TestPyPI (recommended)
```bash
twine upload --repository testpypi dist/*
```
Test install:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple fscss
```

## PyPI
```bash
twine upload dist/*
```

## Auth
Use API token: username `__token__`, password `<your-api-token>`

## Notes
- Package name: `fscss`
- Version in `pyproject.toml` must be bumped if republishing
- Node.js required at runtime
- Only upload after `twine check` passes
