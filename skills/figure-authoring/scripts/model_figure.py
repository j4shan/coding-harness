#!/usr/bin/env python3
"""Turn a data-model spec into a figure template.

    model_figure.py <figure> --emit prompt     # scaffold the prompt, ids declared
    model_figure.py <figure> --emit mermaid    # the erDiagram / classDiagram text
    model_figure.py <figure> --emit drawio     # convert, restyle, attach ids

`--emit drawio` runs draw.io's Mermaid converter, then attaches each component's
spec_id and spec_category by joining on the mermaidId the converter emits. It
leaves styling to the author: the converted diagram keeps draw.io's own look, and
restyling it is a decision for whoever is making the figure.

Reads  resources/data/<figure>_model.json   (or .yaml, with PyYAML installed)
Writes resources/img/<figure>.drawio, resources/img_prompt/<figure>_prompt.md
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import model_spec                             # noqa: E402
from figure_paths import PROMPT, SOURCE, MODEL  # noqa: E402

DRAWIO = str(pathlib.Path(__file__).parent / "drawio")


def _token(text: str) -> str:
    """Mermaid accepts word characters here. Anything else ends the token and
    silently truncates the diagram, so fold it rather than passing it through."""
    t = re.sub(r"[^A-Za-z0-9_]+", "_", str(text)).strip("_")
    return t or "unnamed"


def _quoted(text: str) -> str:
    return str(text).replace('"', "'")


def _member_type(text: str) -> str:
    """Class members tolerate [] and ?, so an array reads as X[] rather than
    being folded flat. Unions spell out, because | ends the token."""
    t = str(text or "any")
    m = re.match(r"^array<(.*)>$", t)
    if m:
        inner = m.group(1) or "any"
        return _token(inner.replace("|", "_or_")) + "[]"
    return _token(t.replace("|", "_or_"))


def _member_name(field: dict) -> str:
    """classDiagram has no comment column, so optionality rides on the name.
    The exact n/N stays in the spec, which is what a reviewer reads."""
    return _token(field["name"]) + ("" if field.get("required", True) else "?")


# ---------------------------------------------------------------- mermaid text

def emit_mermaid(spec: dict) -> str:
    return (_er if spec.get("kind") == "relational" else _class)(spec)


def _er(spec: dict) -> str:
    lines = ["erDiagram"]
    by_id = {e["id"]: e for e in spec["entities"]}
    for r in spec.get("relations") or []:
        pair = model_spec.CARDINALITY[r["cardinality"]][0]
        lines.append("    {} {} {} : {}".format(
            _token(by_id[r["from"]]["label"]), pair,
            _token(by_id[r["to"]]["label"]), _token(r.get("label") or "relates")))
    for e in spec["entities"]:
        lines.append("    {} {{".format(_token(e["label"])))
        for f in e.get("fields") or []:
            row = "        {} {}".format(_token(f.get("type") or "any"), _token(f["name"]))
            if f.get("key"):
                row += " " + f["key"]
            note = f.get("note") or ("" if f.get("required", True) else "optional")
            if note:
                row += ' "{}"'.format(_quoted(note))
            lines.append(row)
        lines.append("    }")
    return "\n".join(lines) + "\n"


def _class(spec: dict) -> str:
    lines = ["classDiagram"]
    by_id = {e["id"]: e for e in spec["entities"]}
    for e in spec["entities"]:
        lines.append("    class {} {{".format(_token(e["label"])))
        lines.append("        <<{}>>".format(_token(e.get("kind") or "object")))
        for f in e.get("fields") or []:
            lines.append("        +{} {}".format(
                _member_type(f.get("type")), _member_name(f)))
        lines.append("    }")
    for r in spec.get("relations") or []:
        mult = model_spec.CARDINALITY[r["cardinality"]][1]
        lines.append('    {} *-- "{}" {} : {}'.format(
            _token(by_id[r["from"]]["label"]), mult,
            _token(by_id[r["to"]]["label"]), _token(r.get("label") or "has")))
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------- convert/restyle

FIELD_MEMBER = re.compile(r"^\+\S+\s+(?P<name>\w+)\??$")


def _tag_fields(wrapper, entity, kids, entity_ids=frozenset()):
    """Attach a spec_id to each field row, so the join covers fields and not
    just entities. Matching is by the name drawn in the row, because the
    converter's row order is its own business.

    erDiagram puts the field name in the second cell of a tableRow;
    classDiagram puts '+type name' on a single child cell."""
    wanted = {}
    for f in entity.get("fields") or []:
        fid = "{}.{}".format(entity["id"], f["name"])
        if fid in entity_ids:
            continue        # the nested entity already carries this id
        wanted[_token(f["name"])] = fid

    tagged = 0
    for row in kids.get(wrapper.get("id"), []):
        name = None
        cells = kids.get(row.get("id"), [])
        if cells:                                    # erDiagram table row
            values = [(c.get("value") or "").strip() for c in cells]
            if len(values) > 1 and values[1]:
                name = values[1]
        else:                                        # classDiagram member
            m = FIELD_MEMBER.match((row.get("value") or "").strip())
            if m:
                name = m.group("name")
        if not name:
            continue
        spec_id = wanted.pop(_token(name), None)
        if spec_id:
            row.set("spec_id", spec_id)
            row.set("spec_category", entity.get("category", ""))
            tagged += 1
    return tagged, sorted(wanted.values())


def _children_of(root):
    kids = {}
    for el in root.iter():
        if el.tag in ("mxCell", "UserObject", "object"):
            kids.setdefault(el.get("parent"), []).append(el)
    return kids



def to_drawio(spec: dict, figure: str, keep_mermaid: bool = False) -> str:
    mmd = emit_mermaid(spec)
    src = SOURCE.format(figure=figure)
    pathlib.Path(src).parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False) as fh:
        fh.write(mmd)
        tmp = fh.name
    try:
        proc = subprocess.run([DRAWIO, "-x", "-f", "xml", "-o", src, tmp],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            raise SystemExit("draw.io conversion failed:\n" + (proc.stderr or proc.stdout))
    finally:
        if keep_mermaid:
            pathlib.Path(src).with_suffix(".mmd").write_text(mmd)
        pathlib.Path(tmp).unlink(missing_ok=True)

    tree = ET.parse(src)
    root = tree.getroot()

    # A converted diagram with no labels is the silent-failure mode: draw.io
    # exits 0 on an unsupported diagram type and writes an empty skeleton.
    if not any((el.get("label") or el.get("value") or "").strip()
               for el in root.iter() if el.tag in ("mxCell", "UserObject", "object")):
        raise SystemExit(
            "draw.io produced a diagram with no labels — the Mermaid type is "
            "probably unsupported by this build. Source kept at " + src)

    by_label = {_token(e["label"]): e for e in spec["entities"]}
    by_id = {e["id"]: e for e in spec["entities"]}
    kids = _children_of(root)
    attached = 0
    untagged = []

    for el in list(root.iter()):
        mid = el.get("mermaidId") or ""
        if mid.startswith("n:"):
            ent = by_label.get(_token(mid[2:]))
            if not ent:
                continue
            cat = ent.get("category", "")
            el.set("spec_id", ent["id"])
            el.set("spec_category", cat)
            attached += 1
            n, unmatched = _tag_fields(el, ent, kids, set(by_id))
            attached += n
            untagged.extend(unmatched)
        elif mid.startswith("e:"):
            m = re.match(r"e:(.+?)->(.+?)#", mid)
            if not m:
                continue
            src_l, dst_l = _token(m.group(1)), _token(m.group(2))
            rel = next((r for r in spec.get("relations") or []
                        if _token(by_id[r["from"]]["label"]) == src_l
                        and _token(by_id[r["to"]]["label"]) == dst_l), None)
            if not rel:
                continue
            cat = by_id[rel["from"]].get("category", "")
            el.set("spec_id", "rel.{}-{}".format(rel["from"], rel["to"]))
            el.set("spec_category", cat)
            attached += 1

    # The converter duplicates each cell's style into mermaidBaseStyle, which is
    # never drawn. Drop it so the style attribute is the single source of truth.
    for el in root.iter():
        el.attrib.pop("mermaidBaseStyle", None)

    # draw.io's Mermaid parser has already placed everything. Say so, so
    # render_figure.py does not lay the diagram out a second time.
    for model in root.iter("mxGraphModel"):
        model.set("figurePlacedBy", "mermaid")

    tree.write(src, encoding="unicode")
    print("wrote {}  components tagged {}".format(src, attached))
    expected = len(model_spec.component_ids(spec))
    if untagged:
        print("  note: {} field(s) drawn without an id: {}".format(
            len(untagged), ", ".join(untagged[:6])))
    if attached < expected:
        print("  note: tagged {} of {} components; the rest did not survive "
              "conversion".format(attached, expected))
    return src


# ------------------------------------------------------------------ prompt

def emit_prompt(spec: dict, figure: str) -> str:
    ids = model_spec.component_ids(spec)
    kind = spec.get("kind")
    n_fields = sum(len(e.get("fields") or []) for e in spec["entities"])
    out = [
        "# {} — figure prompt".format(figure),
        "",
        "## Claim",
        "",
        "<!-- One sentence a reader should be able to say after looking. Write this first. -->",
        "",
        "## Audience",
        "",
        "<!-- Who reads it, and what they already know. -->",
        "",
        "## Instance data",
        "",
        "Literal instance data lives in `{}`.".format(MODEL.format(figure=figure)),
        "",
        "- kind: {}".format(kind),
        "- entities: {}".format(len(spec["entities"])),
        "- fields: {}".format(n_fields),
        "- relations: {}".format(len(spec.get("relations") or [])),
    ]
    if spec.get("documents_sampled"):
        out.append("- documents sampled: {}".format(spec["documents_sampled"]))
    if spec.get("source"):
        out.append("- imported from: {}".format(spec["source"]))
    out += ["", "Component ids:", ""]
    for e in spec["entities"]:
        out.append("- id: {}  — {} ({})".format(
            e["id"], e["label"], e.get("category", "")))
        for f in e.get("fields") or []:
            out.append("  - id: {}.{}".format(e["id"], f["name"]))
    for r in spec.get("relations") or []:
        out.append("- id: rel.{}-{}  — {} {} {}".format(
            r["from"], r["to"], r["from"], r["cardinality"], r["to"]))
    out += [
        "",
        "## Emphasis",
        "",
        "<!-- What must be noticed first; what is context. -->",
        "",
        "## Exclusions",
        "",
        "<!-- What was kept out, and why. -->",
        "",
        "## Destination",
        "",
        "<!-- Page width, print or screen, light or dark. -->",
        "",
        "## Style",
        "",
        "<!-- Colour, type, shape, edge semantics, layout, grouping, legend.",
        "     Your decisions; record them so the next pass does not re-derive them. -->",
        "",
        "| Category | Entities |",
        "| --- | --- |",
    ]
    groups = {}
    for e in spec["entities"]:
        groups.setdefault(e.get("category", ""), []).append(e["label"])
    for cat, labels in groups.items():
        out.append("| {} | {} |".format(cat or "(none)", ", ".join(labels)))
    out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("figure")
    ap.add_argument("--emit", choices=("prompt", "mermaid", "drawio"), required=True)
    ap.add_argument("--spec", help="override the spec path")
    ap.add_argument("--keep-mermaid", action="store_true",
                    help="keep the .mmd beside the source, for debugging")
    a = ap.parse_args(argv)

    spec_path = a.spec or MODEL.format(figure=a.figure)
    if not pathlib.Path(spec_path).exists():
        print("no spec at {} — build one with model_spec.py".format(spec_path),
              file=sys.stderr)
        return 2
    spec = model_spec.load(spec_path)
    problems = model_spec.validate(spec)
    if problems:
        for p in problems:
            print("  PROBLEM: " + p, file=sys.stderr)
        return 1

    if a.emit == "mermaid":
        sys.stdout.write(emit_mermaid(spec))
    elif a.emit == "prompt":
        dest = pathlib.Path(PROMPT.format(figure=a.figure))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(emit_prompt(spec, a.figure))
        print("wrote {}  ids declared {}".format(
            dest, len(model_spec.component_ids(spec))))
    else:
        to_drawio(spec, a.figure, a.keep_mermaid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
