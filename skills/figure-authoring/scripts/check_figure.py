#!/usr/bin/env python3
"""Check a figure's source against its prompt.

    check_figure.py <figure> [--source PATH] [--prompt PATH] [--quiet]

Every check here is one your eyes cannot settle from the render. draw.io accepts
a dangling edge, an edge with no geometry, and a label whose angle brackets the
HTML pass will eat — then silently omits them from the picture, so the figure
looks finished and is not.

This checks correctness only. It has no opinion on colour, type, or shape: those
are the author's decisions, and nothing here second-guesses them.

Exit 0 clean, 1 on any FAIL, 2 when a file is missing or unreadable.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from figure_paths import PROMPT, SOURCE  # noqa: E402

# The prompt declares a component id as "id: <value>"; model_figure.py writes
# them in that form and SKILL.md section 2 requires it.
DECLARED = re.compile(r"\bid:\s*([a-z0-9_.:-]+)", re.IGNORECASE)
WRAPPERS = ("object", "UserObject")          # draw.io writes either
# draw.io writes real formatting tags into html=1 labels; those are intended.
# Anything else inside angle brackets is a placeholder the HTML pass will eat.
FORMATTING = {"b", "i", "u", "br", "sub", "sup", "span", "div", "font", "p",
              "/b", "/i", "/u", "/span", "/div", "/font", "/p"}
RAW_TAG = re.compile(r"<(/?[A-Za-z_][\w.:-]*)>")


def _stray_tags(text):
    return [m for m in RAW_TAG.findall(text) if m.lower() not in FORMATTING]


class Report:
    def __init__(self):
        self.fails, self.notes = [], []

    def fail(self, msg):
        self.fails.append(msg)

    def note(self, msg):
        self.notes.append(msg)


def _parents(root):
    m = {}
    for parent in root.iter():
        for child in parent:
            m[id(child)] = parent
    return m


def _ident(el, parents):
    """Name a cell the way a reader can find it. A wrapped mxCell carries no id
    of its own, so fall back to the wrapper's spec_id or id."""
    own = el.get("spec_id") or el.get("id")
    if own:
        return own
    up = parents.get(id(el))
    while up is not None:
        name = up.get("spec_id") or up.get("id")
        if name:
            return "in {}".format(name)
        up = parents.get(id(up))
    return "unnamed"


def _styles(root):
    """Yield (element, style-dict) for every cell carrying a style."""
    for el in root.iter():
        if el.tag not in ("mxCell",) + WRAPPERS:
            continue
        raw = el.get("style")
        if raw is None:
            child = el.find("mxCell")
            if child is None:
                continue
            el, raw = child, child.get("style")
        if not raw:
            continue
        d = {}
        for part in raw.split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                d[k] = v
        yield el, d


def check_structure(root, rep, parents):
    cells = [el for el in root.iter() if el.tag in ("mxCell",) + WRAPPERS]
    ids = {el.get("id") for el in cells if el.get("id")}

    if "0" not in ids or "1" not in ids:
        rep.fail("no root cells: a model needs mxCell id=0 and id=1")

    for el in cells:
        if el.tag != "mxCell":
            continue
        if el.get("edge") == "1":
            for end in ("source", "target"):
                ref = el.get(end)
                if ref is not None and ref not in ids:
                    rep.fail("edge {} has a dangling {} -> {!r}".format(
                        _ident(el, parents), end, ref))
            if el.find("mxGeometry") is None:
                rep.fail("edge {} has no mxGeometry child; it will not render"
                         .format(_ident(el, parents)))


# A correct multi-line label writes &#10;, which the XML parse turns into a real
# newline — so this one check reads the raw file. A newline that is literal in
# the source is the defect; one that arrived via &#10; is correct.
RAW_NEWLINE = re.compile(r'(?:value|label)="[^"]*\n[^"]*"')


def check_raw(text, rep):
    for m in RAW_NEWLINE.finditer(text):
        rep.fail("literal newline inside {}; write &#10; or the label collapses "
                 "to one line".format(m.group(0)[:40].replace("\n", "\\n")))


def check_labels(root, rep, parents):
    for el in root.iter():
        if el.tag not in ("mxCell",) + WRAPPERS:
            continue
        for attr in ("value", "label"):
            text = el.get(attr)
            if not text:
                continue
            style = el.get("style") or ""
            child = el.find("mxCell")
            if not style and child is not None:
                style = child.get("style") or ""
            stray = _stray_tags(text)
            if stray and "html=1" in style:
                rep.fail("{}: {!r} carries html=1 and unescaped <{}>; the HTML "
                         "pass will drop it. Double-escape it (&amp;lt;)".format(
                             _ident(el, parents), text[:40], stray[0]))
            elif stray:
                rep.note("{}: {!r} holds <{}>; it renders literally today, but "
                         "turning on html=1 would drop it".format(
                             _ident(el, parents), text[:40], stray[0]))


def check_type(root, rep):
    """A cell that states no font renders with the viewer's default, so it can
    look different on another machine. That is a portability fact, not a style
    rule — it is reported as a note, and the figure still passes."""
    missing = sum(1 for _, st in _styles(root)
                  if "fontSize" not in st or "fontFamily" not in st)
    if missing:
        rep.note("{} styled cells state no fontFamily or fontSize; they fall back "
                 "to the viewer's default and may render differently elsewhere"
                 .format(missing))


def check_ids(root, prompt_text, rep):
    found = [el.get("spec_id") for el in root.iter() if el.get("spec_id")]
    declared = set(DECLARED.findall(prompt_text or ""))
    missing = sorted(declared - set(found))
    dupes = sorted({i for i in found if found.count(i) > 1})
    undeclared = sorted(set(found) - declared)

    if prompt_text is None:
        rep.fail("no prompt file; the prompt is the figure's retained specification")
    elif not declared:
        rep.fail("the prompt declares no component ids in the form 'id: <value>'")

    for i in missing:
        rep.fail("id {!r} is declared in the prompt but absent from the source".format(i))
    for i in dupes:
        rep.fail("spec_id {!r} is used twice; a copy-paste duplicated a component".format(i))
    if undeclared:
        rep.note("{} ids in the source are not declared in the prompt (titles, "
                 "captions and legend keys are minted during generation): {}".format(
                     len(undeclared), ", ".join(undeclared[:6])
                     + (" …" if len(undeclared) > 6 else "")))
    return len(declared), len(set(found))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("figure")
    ap.add_argument("--source")
    ap.add_argument("--prompt")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    src = pathlib.Path(a.source or SOURCE.format(figure=a.figure))
    pr = pathlib.Path(a.prompt or PROMPT.format(figure=a.figure))
    if not src.exists():
        print("missing source: {}".format(src), file=sys.stderr)
        return 2

    text = src.read_text()
    if "<mxGraphModel" not in text:
        print("{} holds no mxGraphModel; it may be a compressed .drawio. Open and "
              "re-save it uncompressed.".format(src), file=sys.stderr)
        return 2
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        print("{} is not well-formed XML: {}".format(src, exc), file=sys.stderr)
        return 2

    rep = Report()
    parents = _parents(root)
    if "<!--" in text:
        rep.fail("the source carries an XML comment; draw.io breaks on them")
    check_raw(text, rep)
    check_structure(root, rep, parents)
    check_labels(root, rep, parents)
    check_type(root, rep)
    declared, found = check_ids(root, pr.read_text() if pr.exists() else None, rep)

    print("{}: {} ids declared, {} in source".format(a.figure, declared, found))
    for n in rep.notes:
        if not a.quiet:
            print("  note: " + n)
    for f in rep.fails:
        print("  FAIL: " + f)
    if not rep.fails:
        print("  clean")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main())
