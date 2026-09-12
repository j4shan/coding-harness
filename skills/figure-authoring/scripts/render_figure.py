#!/usr/bin/env python3
"""Validate, lay out, export, and open a figure.

    render_figure.py <figure> [--layout verticalFlow] [--scale 2] [--no-layout]
    render_figure.py <figure> --from-mermaid path/to/diagram.mmd

Runs the whole render path in one call so the three things that are easy to get
wrong cannot be: validation omits --layout (the layout pass loads leniently and
accepts malformed XML a plain export rejects), validation writes to a throwaway
path (validating in place repairs the file and destroys the evidence), and
validation runs before the layout pass.

Layout is skipped automatically for Mermaid-converted input, whose parser has
already placed everything.
"""
from __future__ import annotations

import argparse
import pathlib
import platform
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from figure_paths import SOURCE, RENDER  # noqa: E402

DRAWIO = str(pathlib.Path(__file__).parent / "drawio")
PRESETS = ("verticalFlow", "horizontalFlow", "verticalTree", "horizontalTree",
           "radialTree", "organic", "libavoid")


def run(args, what):
    proc = subprocess.run([DRAWIO] + args, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write((proc.stderr or proc.stdout or "").rstrip() + "\n")
        raise SystemExit("{} failed (exit {})".format(what, proc.returncode))
    return proc


def validate(src):
    """Export to XML with a throwaway output. Catches a truncated, malformed,
    empty, or non-diagram file. Does not catch a dangling edge reference, a
    missing root cell, or an edge with no geometry — check_figure.py does."""
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as fh:
        out = fh.name
    try:
        run(["-x", "-f", "xml", "-o", out, src], "validation")
    finally:
        pathlib.Path(out).unlink(missing_ok=True)


def open_file(path):
    system = platform.system()
    if system == "Darwin":
        cmd = ["open", path]
    elif system == "Windows":
        cmd = ["cmd.exe", "/c", "start", "", path]
    elif "microsoft" in platform.release().lower():
        win = subprocess.run(["wslpath", "-w", path], capture_output=True, text=True)
        cmd = ["cmd.exe", "/c", "start", "", win.stdout.strip()]
    else:
        cmd = ["xdg-open", path]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except Exception:
        print("could not open it; the file is at {}".format(pathlib.Path(path).resolve()))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("figure")
    ap.add_argument("--layout", default="verticalFlow", choices=PRESETS)
    ap.add_argument("--no-layout", action="store_true",
                    help="keep the positions already in the source")
    ap.add_argument("--scale", type=int, default=1,
                    help="raster scale; use 2 for small type at full page width")
    ap.add_argument("--border", type=int, default=12)
    ap.add_argument("--from-mermaid", metavar="MMD",
                    help="convert this .mmd to the figure source first")
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args(argv)

    src = SOURCE.format(figure=a.figure)
    png = RENDER.format(figure=a.figure)
    pathlib.Path(src).parent.mkdir(parents=True, exist_ok=True)

    skip_layout = a.no_layout
    if a.from_mermaid:
        run(["-x", "-f", "xml", "-o", src, a.from_mermaid], "mermaid conversion")
        print("converted {} -> {}".format(a.from_mermaid, src))
        skip_layout = True     # the Mermaid parser has already placed everything

    if not pathlib.Path(src).exists():
        print("no source at {}".format(src), file=sys.stderr)
        return 2

    validate(src)
    print("validated {}".format(src))

    if not skip_layout and "figurePlacedBy=\"mermaid\"" in pathlib.Path(src).read_text():
        skip_layout = True
        print("source was placed by the Mermaid parser; skipping the layout pass")

    if not skip_layout:
        run(["-x", "-f", "xml", "--layout", a.layout, "-o", src, src], "layout")
        print("laid out with {}".format(a.layout))

    export = ["-x", "-f", "png", "-e", "-b", str(a.border)]
    if a.scale > 1:
        export += ["-s", str(a.scale)]
    run(export + ["-o", png, src], "export")
    size = pathlib.Path(png).stat().st_size
    print("exported {} ({:,} bytes)".format(png, size))

    if not a.no_open:
        open_file(png)
    return 0


if __name__ == "__main__":
    sys.exit(main())
