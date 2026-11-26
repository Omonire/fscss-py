from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import tempfile
import time
from pathlib import Path

from . import __version__
from .core import compile_file
from .environment import check_all, engine_path, find_node, format_version, node_version
from .node_install import detect_package_managers, install_command, run_install

__all__ = ["main"]

COMMANDS = {
    "compile",
    "watch",
    "init",
    "doctor",
    "build",
    "clean",
    "env",
    "completion",
    "report",
    "version",
}

GLOBAL_FLAGS = {"-h", "--help", "--version", "-v", "--verbose", "-q", "--quiet", "--no-color"}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fscss",
        description="FSCSS (Figured Shorthand CSS) to plain CSS from the command line.",
    )
    parser.add_argument("--version", action="store_true", help="Print version info")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Only print errors")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    sub = parser.add_subparsers(dest="command")

    compile_p = sub.add_parser("compile", help="Compile a .fscss file")
    compile_p.add_argument("input", help="Input .fscss file")
    compile_p.add_argument("output", nargs="?", help="Output .css file (default: input with .css)")
    compile_p.add_argument("-o", "--output", dest="output_opt", help="Output .css file")
    compile_p.add_argument("-w", "--watch", action="store_true", help="Recompile on change")
    compile_p.add_argument("--cwd", help="Resolve relative imports from this directory")
    compile_p.add_argument("--timeout", type=float, help="Abort after N seconds")
    compile_p.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    compile_p.add_argument(
        "--check", action="store_true", help="Compare with existing output; exit 1 on drift"
    )

    watch_p = sub.add_parser("watch", help="Recompile on change")
    watch_p.add_argument("input", help="Input .fscss file")
    watch_p.add_argument("output", nargs="?", help="Output .css file (default: input with .css)")
    watch_p.add_argument(
        "--interval", type=float, default=1.0, help="Poll interval in seconds (default 1.0)"
    )

    init_p = sub.add_parser("init", help="Set up this machine/project")
    init_p.add_argument("--yes", action="store_true", help="Don't prompt; assume yes")
    init_p.add_argument(
        "--pm",
        choices=["winget", "choco", "scoop", "brew", "apt", "dnf", "pacman", "zypper", "apk"],
        help="Force a package manager",
    )
    init_p.add_argument(
        "--no-config", action="store_true", help="Skip creating fscss.toml / sample file"
    )
    init_p.add_argument("--force", action="store_true", help="Overwrite existing config files")
    init_p.add_argument("--json", action="store_true", help="Machine-readable output")

    doctor_p = sub.add_parser("doctor", help="Check the environment")
    doctor_p.add_argument(
        "--check", action="store_true", help="Exit 1 if any check fails; never prompt or install"
    )
    doctor_p.add_argument("--json", action="store_true", help="Machine-readable output")

    build_p = sub.add_parser("build", help="Compile a directory")
    build_p.add_argument(
        "directory", nargs="?", default=".", help="Directory to compile (default: .)"
    )
    build_p.add_argument("--no-recursive", action="store_true", help="Only scan the top level")
    build_p.add_argument(
        "--check", action="store_true", help="Compare with existing output; exit 1 on drift"
    )
    build_p.add_argument("--strict", action="store_true", help="Treat warnings as errors")

    clean_p = sub.add_parser("clean", help="Delete generated .css files")
    clean_p.add_argument(
        "directory", nargs="?", default=".", help="Directory to clean (default: .)"
    )
    clean_p.add_argument("--no-recursive", action="store_true", help="Only scan the top level")
    clean_p.add_argument("--dry-run", action="store_true", help="Show what would be deleted")

    env_p = sub.add_parser("env", help="Print resolved paths and versions")
    env_p.add_argument("--json", action="store_true", help="Machine-readable output")

    comp_p = sub.add_parser("completion", help="Print shell completion script")
    comp_p.add_argument("shell", choices=["bash", "zsh", "fish", "powershell"])

    report_p = sub.add_parser("report", help="Print a paste-ready bug report")
    report_p.add_argument("--json", action="store_true", help="Machine-readable output")

    ver_p = sub.add_parser("version", help="Print version info")
    ver_p.add_argument("--json", action="store_true", help="Machine-readable output")

    return parser


def _normalize_argv(argv: list[str]) -> list[str]:
    """Allow ``fscss input.fscss [output.css]`` as shorthand for ``compile``."""
    if not argv:
        return argv
    first = argv[0]
    if first in COMMANDS or first in GLOBAL_FLAGS:
        return argv
    return ["compile", *argv]


def _resolve_outputs(input_path: str, output_path: str | None) -> tuple[str, str]:
    if output_path:
        return input_path, output_path
    return input_path, str(Path(input_path).with_suffix(".css"))


def _node_hint() -> str | None:
    if find_node():
        return None
    return "Hint: Node.js is required. Run `fscss init` to check and install it."


def _has_warnings(output: str) -> bool:
    lowered = (output or "").lower()
    return any(
        marker in lowered for marker in ("failed import", "can't import", "warning", "error")
    )


def _read_css(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _check_output(
    input_path: str, output_path: str, cwd: str | None = None, timeout: float | None = None
) -> int:
    out = Path(output_path)
    if not out.exists():
        print(f"Error: missing output file: {out}", file=sys.stderr)
        return 1
    fd, tmp = tempfile.mkstemp(suffix=".css")
    os.close(fd)
    try:
        compile_file(input_path, tmp, cwd=cwd, timeout=timeout)
        if _read_css(Path(tmp)) != _read_css(out):
            print(f"Error: {output_path} is out of date", file=sys.stderr)
            return 1
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _run_compile(args, input_path: str, output_path: str) -> int:
    if args.check:
        return _check_output(input_path, output_path, cwd=args.cwd, timeout=args.timeout)
    try:
        output = compile_file(input_path, output_path, cwd=args.cwd, timeout=args.timeout)
        if output and not args.quiet:
            print(output, end="")
        if args.strict and _has_warnings(output):
            print("Error: compiler reported warnings (--strict)", file=sys.stderr)
            return 2
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        hint = _node_hint()
        if hint:
            print(hint, file=sys.stderr)
        return 2 if "Node" in str(e) else 1


def _watch(input_path: str, output_path: str, interval: float = 1.0) -> int:
    from .integrations import watch_dir

    src = Path(input_path).resolve()
    try:
        output = compile_file(input_path, output_path)
        if output:
            print(output, end="")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        hint = _node_hint()
        if hint:
            print(hint, file=sys.stderr)

    print(f"Watching {src} for changes... (Ctrl+C to stop)")
    watch_dir(
        src.parent, interval=interval, callback=lambda s, o: print(f"[fscss] recompiled {s} -> {o}")
    )

    try:
        while True:
            time.sleep(interval)
    except KeyboardInterrupt:
        return 0


def _checks_payload() -> list:
    return [
        {"name": c.name, "status": c.status, "detail": c.detail, "hint": c.hint}
        for c in check_all()
    ]


def _print_checks(checks) -> None:
    for c in checks:
        mark = "ok" if c.status == "ok" else ("!!" if c.status == "fail" else "ww")
        print(f"  [{mark}] {c.name}: {c.detail}")
        if c.hint and c.status != "ok":
            print(f"       {c.hint}")


def _cmd_env(args) -> int:
    node = find_node()
    payload = {
        "fscss": __version__,
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.machine()}",
        "node": node,
        "node_version": format_version(node_version(node)),
        "engine": str(engine_path()),
        "cwd": os.getcwd(),
    }
    if args.json:
        print(json.dumps(payload))
    else:
        print(f"fscss {payload['fscss']}")
        print(f"Python {payload['python']}")
        print(f"Platform {payload['platform']}")
        print(f"Node {payload['node_version']} ({payload['node'] or 'not found'})")
        print(f"Engine {payload['engine']}")
        print(f"CWD {payload['cwd']}")
    return 0


def _cmd_version(args) -> int:
    node = find_node()
    payload = {
        "fscss": __version__,
        "xfscss": "1.2.6",
        "node": format_version(node_version(node)),
        "python": platform.python_version(),
    }
    if args.json:
        print(json.dumps(payload))
    else:
        print(f"fscss {payload['fscss']} (xfscss {payload['xfscss']})")
        print(f"Node {payload['node']} | Python {payload['python']}")
    return 0


def _cmd_doctor(args) -> int:
    checks = check_all()
    if args.json:
        print(json.dumps(_checks_payload()))
    else:
        _print_checks(checks)
    failed = any(c.status == "fail" for c in checks)
    return 1 if (args.check and failed) else 0


def _cmd_init(args) -> int:
    checks = check_all()
    if not args.json:
        print("fscss init")
        _print_checks(checks)

    node_ok = any(c.name == "Node.js" and c.status == "ok" for c in checks)

    if not node_ok:
        if os.environ.get("FSCSS_NO_DOWNLOAD") == "1":
            print("Error: Node.js is missing and FSCSS_NO_DOWNLOAD=1", file=sys.stderr)
            return 2

        managers = detect_package_managers()
        if args.pm:
            managers = [args.pm]
        if not managers:
            print(
                "Error: no supported package manager found. Install Node.js 20+ from https://nodejs.org/.",
                file=sys.stderr,
            )
            return 2

        pm = args.pm or managers[0]
        command = install_command(pm)
        print(f"\nNode.js 20+ not found. Install it with {pm}?")
        print(f"  Command: {' '.join(command)}")

        proceed = args.yes
        if not proceed and sys.stdin.isatty():
            answer = input("Continue? [Y/n] ").strip().lower()
            proceed = answer in ("", "y", "yes")
        elif not proceed:
            print("Non-interactive shell detected. Use `--yes` to auto-confirm.", file=sys.stderr)
            return 2

        if not proceed:
            return 2

        try:
            code = run_install(pm)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
        if code != 0:
            print(f"Error: {pm} exited with {code}", file=sys.stderr)
            return 2

        checks = check_all()
        node_ok = any(c.name == "Node.js" and c.status == "ok" for c in checks)
        if not node_ok:
            print(
                "Error: Node.js is still unavailable. Open a new terminal or check your PATH.",
                file=sys.stderr,
            )
            return 2
        if not args.json:
            print("Node.js installed and verified.")

    if not args.json and not args.no_config:
        config = Path("fscss.toml")
        if not config.exists() or args.force:
            config.write_text("# fscss project configuration\n", encoding="utf-8")
            print("Wrote fscss.toml")
        sample = Path("style.fscss")
        if not sample.exists() or args.force:
            sample.write_text(
                "$accent: #8f6bff;\n\nbody {\n  bg: #0b0a13;\n  color: $accent!;\n}\n",
                encoding="utf-8",
            )
            print("Wrote style.fscss")

    if args.json:
        print(json.dumps({"ready": node_ok, "checks": _checks_payload()}))
    else:
        print("\nAll checks passed." if node_ok else "\nSetup incomplete.")
    return 0 if node_ok else 2


def _cmd_build(args) -> int:
    from .integrations import iter_fscss

    recursive = not args.no_recursive
    files = list(iter_fscss(args.directory, recursive=recursive))
    if not files:
        print(f"No .fscss files found in {args.directory}")
        return 0

    failures = 0
    warnings = 0
    for src in files:
        out = src.with_suffix(".css")
        if args.check:
            if _check_output(str(src), str(out)) != 0:
                failures += 1
            continue
        try:
            output = compile_file(src, out)
            if args.strict and _has_warnings(output):
                print(f"Error: warnings in {src} (--strict)", file=sys.stderr)
                warnings += 1
        except Exception as e:
            print(f"Error compiling {src}: {e}", file=sys.stderr)
            failures += 1

    if args.check:
        print(f"{len(files)} file(s) checked, {failures} out of date.")
        return 1 if failures else 0

    print(f"{len(files) - failures} file(s) compiled, {failures} failed.")
    if warnings:
        return 2
    return 1 if failures else 0


def _cmd_clean(args) -> int:
    from .integrations import iter_fscss

    recursive = not args.no_recursive
    removed = 0
    for src in iter_fscss(args.directory, recursive=recursive):
        css = src.with_suffix(".css")
        if not css.exists():
            continue
        if args.dry_run:
            print(f"Would delete {css}")
        else:
            try:
                css.unlink()
                print(f"Deleted {css}")
            except OSError as e:
                print(f"Error deleting {css}: {e}", file=sys.stderr)
                continue
        removed += 1
    print(f"{'Would delete' if args.dry_run else 'Deleted'} {removed} file(s).")
    return 0


def _cmd_completion(args) -> int:
    commands = " ".join(sorted(COMMANDS))
    shell = args.shell
    if shell == "bash":
        print(
            '_fscss() { COMPREPLY=($(compgen -W "'
            + commands
            + ' --help --version --verbose --quiet" -- "${COMP_WORDS[COMP_CWORD]}")); }; '
            "complete -F _fscss fscss"
        )
    elif shell == "zsh":
        print("#compdef fscss\n_fscss() { _arguments '1:command:(" + commands + ")' }")
    elif shell == "fish":
        print('complete -c fscss -f -a "' + commands + '"')
    elif shell == "powershell":
        items = ", ".join(f"'{cmd}'" for cmd in sorted(COMMANDS))
        print(
            "Register-ArgumentCompleter -Native -CommandName fscss -ScriptBlock { "
            "param($wordToComplete, $commandAst, $cursorPosition); "
            f'@({items}) | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{ '
            "[System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_) } }"
        )
    return 0


def _cmd_report(args) -> int:
    node = find_node()
    checks = _checks_payload()
    payload = {
        "fscss": __version__,
        "xfscss": "1.2.6",
        "python": platform.python_version(),
        "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "node": node,
        "node_version": format_version(node_version(node)),
        "engine": str(engine_path()),
        "checks": checks,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0
    print("FSCSS Bug Report")
    print("=================")
    print(f"fscss: {payload['fscss']} (xfscss {payload['xfscss']})")
    print(f"python: {payload['python']}")
    print(f"os: {payload['os']}")
    print(f"node: {payload['node'] or 'not found'} ({payload['node_version']})")
    print(f"engine: {payload['engine']}")
    print("\nChecks:")
    for c in checks:
        print(f"  [{c['status']}] {c['name']}: {c['detail']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = _normalize_argv(list(sys.argv[1:] if argv is None else argv))
    parser = _build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "version", False) and not args.command:
        node = find_node()
        print(f"fscss {__version__} (xfscss 1.2.6)")
        print(f"Node {format_version(node_version(node))} | Python {platform.python_version()}")
        return 0

    command = args.command
    if command == "version":
        return _cmd_version(args)
    if command == "env":
        return _cmd_env(args)
    if command == "doctor":
        return _cmd_doctor(args)
    if command == "init":
        return _cmd_init(args)
    if command == "build":
        return _cmd_build(args)
    if command == "clean":
        return _cmd_clean(args)
    if command == "completion":
        return _cmd_completion(args)
    if command == "report":
        return _cmd_report(args)
    if command == "watch":
        input_path, output_path = _resolve_outputs(args.input, args.output)
        return _watch(input_path, output_path, interval=args.interval)
    if command == "compile":
        input_path, output_path = _resolve_outputs(args.input, args.output_opt or args.output)
        if args.watch:
            return _watch(input_path, output_path)
        return _run_compile(args, input_path, output_path)

    parser.print_help(sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
