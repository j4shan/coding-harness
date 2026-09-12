#!/usr/bin/env python3
"""Author, import, and validate a data-model spec — the literal instance data
behind a data-model figure.

    model_spec.py validate  <spec>
    model_spec.py from-sql  <file.sql>      [-o <spec>]
    model_spec.py from-json <doc>...        [-o <spec>] [--max-depth N] [--max-fields N]

The spec is JSON. A .yaml/.yml path also reads and writes YAML, but only when
PyYAML is installed; JSON needs nothing beyond the standard library, so it is
the format to reach for unless a human is editing the file by hand.

Shape:

    {"figure": "orders", "kind": "relational",
     "entities": [{"id": "customer", "label": "CUSTOMER", "category": "subject",
                   "fields": [{"name": "id", "type": "int", "key": "PK",
                               "required": true, "note": ""}]}],
     "relations": [{"from": "customer", "to": "order",
                    "cardinality": "one-to-many", "label": "places"}]}

`kind` is "relational" (tables and foreign keys -> erDiagram) or "document"
(nested records -> classDiagram). Importers never invent a category: everything
lands in "unassigned" until the author groups the entities.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
KINDS = ("relational", "document")

# Controlled vocabulary. Relational cardinalities map to crow's-foot pairs;
# document cardinalities map to composition multiplicities.
CARDINALITY = {
    "one-to-one":          ("||--||", "1"),
    "one-to-many":         ("||--o{", "0..*"),
    "one-to-at-least-one": ("||--|{", "1..*"),
    "zero-or-one-to-many": ("|o--o{", "0..*"),
    "many-to-many":        ("}o--o{", "*"),
    "contains-one":        ("||--||", "1"),
    "contains-many":       ("||--o{", "0..*"),
    "contains-optional":   ("|o--o|", "0..1"),
}

ID_RE = re.compile(r"^[a-z0-9_.:-]+$")
KEYS = ("PK", "FK", "UK", "")


class SpecError(Exception):
    pass


# --------------------------------------------------------------------------- io

def _is_yaml(path: str) -> bool:
    return str(path).lower().endswith((".yaml", ".yml"))


def load(path: str) -> dict:
    text = pathlib.Path(path).read_text()
    if _is_yaml(path):
        try:
            import yaml
        except ImportError:
            raise SpecError(
                f"{path} is YAML but PyYAML is not installed. Convert the spec to "
                f"JSON, or install PyYAML.")
        return yaml.safe_load(text)
    return json.loads(text)


def dump(spec: dict, path: str) -> None:
    p = pathlib.Path(path)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    if _is_yaml(path):
        try:
            import yaml
        except ImportError:
            raise SpecError("PyYAML is not installed; write the spec as .json instead.")
        p.write_text(yaml.safe_dump(spec, sort_keys=False))
    else:
        p.write_text(json.dumps(spec, indent=2) + "\n")


# --------------------------------------------------------------------- validate

def validate(spec: dict) -> list:
    """Return a list of problems. Empty means the spec is usable."""
    bad = []
    if not isinstance(spec, dict):
        return ["spec is not a mapping"]

    if spec.get("kind") not in KINDS:
        bad.append(f"kind must be one of {', '.join(KINDS)}; got {spec.get('kind')!r}")

    entities = spec.get("entities") or []
    if not entities:
        bad.append("no entities")

    seen = set()
    for e in entities:
        eid = e.get("id", "")
        if not ID_RE.match(str(eid)):
            bad.append(f"entity id {eid!r} is not lowercase [a-z0-9_.:-]")
        if eid in seen:
            bad.append(f"duplicate entity id {eid!r}")
        seen.add(eid)

        names = set()
        for f in e.get("fields") or []:
            fname = f.get("name", "")
            if not fname:
                bad.append(f"{eid}: field with no name")
            if fname in names:
                bad.append(f"{eid}: duplicate field {fname!r}")
            names.add(fname)
            if f.get("key", "") not in KEYS:
                bad.append(f"{eid}.{fname}: key must be one of PK, FK, UK or empty; "
                           f"got {f.get('key')!r}")

    for r in spec.get("relations") or []:
        for end in ("from", "to"):
            if r.get(end) not in seen:
                bad.append(f"relation {r.get('from')}->{r.get('to')}: "
                           f"{end} names no entity ({r.get(end)!r})")
        if r.get("cardinality") not in CARDINALITY:
            bad.append(f"relation {r.get('from')}->{r.get('to')}: unknown cardinality "
                       f"{r.get('cardinality')!r}; known: {', '.join(CARDINALITY)}")

    return bad


def component_ids(spec: dict) -> list:
    """Every component id the figure will carry, derived from the spec alone.

    A field holding a nested object and the entity drawn for that object are one
    component, so they share one id rather than colliding on two."""
    entity_ids = {e["id"] for e in spec.get("entities") or []}
    ids = []
    for e in spec.get("entities") or []:
        ids.append(e["id"])
        for f in e.get("fields") or []:
            fid = "{}.{}".format(e["id"], f["name"])
            if fid not in entity_ids:
                ids.append(fid)
    for r in spec.get("relations") or []:
        ids.append("rel.{}-{}".format(r["from"], r["to"]))
    return ids


# -------------------------------------------------------------------- from-sql

CREATE_RE = re.compile(
    r"CREATE\s+(?:TEMP\w*\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
    r"[`\"\[]?(?:(?P<schema>\w+)[`\"\]]?\.)?[`\"\[]?(?P<name>\w+)[`\"\]]?\s*\((?P<body>.*?)\)\s*"
    r"(?:[A-Za-z_ =]*?)?;",
    re.IGNORECASE | re.DOTALL)

TABLE_PK_RE = re.compile(r"^\s*(?:CONSTRAINT\s+\w+\s+)?PRIMARY\s+KEY\s*\((?P<cols>[^)]*)\)",
                         re.IGNORECASE)
TABLE_UQ_RE = re.compile(r"^\s*(?:CONSTRAINT\s+\w+\s+)?UNIQUE\s*(?:KEY\s+\w+\s*)?\((?P<cols>[^)]*)\)",
                         re.IGNORECASE)
TABLE_FK_RE = re.compile(
    r"^\s*(?:CONSTRAINT\s+\w+\s+)?FOREIGN\s+KEY\s*\((?P<cols>[^)]*)\)\s*"
    r"REFERENCES\s+[`\"\[]?(?P<ref>\w+)[`\"\]]?\s*(?:\((?P<refcols>[^)]*)\))?",
    re.IGNORECASE)
INLINE_REF_RE = re.compile(r"REFERENCES\s+[`\"\[]?(?P<ref>\w+)[`\"\]]?", re.IGNORECASE)
# Stop the type at the first constraint word, or it swallows NOT NULL /
# REFERENCES and the inline foreign key is lost with it. Multi-word types
# (DOUBLE PRECISION, CHARACTER VARYING, INT UNSIGNED) are listed explicitly.
TYPE_TAIL = r"(?:\s+(?:PRECISION|VARYING|UNSIGNED|ZEROFILL))*"
COL_RE = re.compile(
    r"^\s*[`\"\[]?(?P<name>\w+)[`\"\]]?\s+"
    r"(?P<type>[A-Za-z]\w*" + TYPE_TAIL + r"(?:\s*\([^)]*\))?)",
    re.IGNORECASE)

SKIP_LINE = re.compile(r"^\s*(?:CONSTRAINT\s+\w+\s+)?(?:PRIMARY\s+KEY|FOREIGN\s+KEY|UNIQUE|KEY|INDEX|CHECK)\b",
                       re.IGNORECASE)


def _split_top_level(body: str) -> list:
    """Split a CREATE TABLE body on commas that are not inside parentheses."""
    out, depth, cur = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        out.append("".join(cur))
    return out


def from_sql(text: str, figure: str) -> dict:
    # Strip comments so they cannot be mistaken for column definitions.
    text = re.sub(r"--[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

    entities, relations = [], []
    for m in CREATE_RE.finditer(text):
        table = m.group("name")
        eid = table.lower()
        fields, pk_cols, uq_cols, fks = [], set(), set(), {}

        for part in _split_top_level(m.group("body")):
            tpk = TABLE_PK_RE.match(part)
            if tpk:
                pk_cols |= {c.strip(" `\"[]") for c in tpk.group("cols").split(",")}
                continue
            tuq = TABLE_UQ_RE.match(part)
            if tuq:
                cols = [c.strip(" `\"[]") for c in tuq.group("cols").split(",")]
                if len(cols) == 1:      # a composite UNIQUE makes no single column unique
                    uq_cols |= set(cols)
                continue
            tfk = TABLE_FK_RE.match(part)
            if tfk:
                for c in tfk.group("cols").split(","):
                    fks[c.strip(" `\"[]")] = tfk.group("ref").lower()
                continue
            if SKIP_LINE.match(part):
                continue
            col = COL_RE.match(part)
            if not col:
                continue
            name = col.group("name")
            rest = part[col.end():]
            key = ""
            if re.search(r"\bPRIMARY\s+KEY\b", part, re.IGNORECASE):
                key = "PK"
            elif re.search(r"\bUNIQUE\b", rest, re.IGNORECASE):
                key = "UK"
            iref = INLINE_REF_RE.search(rest)
            if iref:
                fks[name] = iref.group("ref").lower()
            fields.append({
                "name": name,
                "type": re.sub(r"\s+", " ", col.group("type")).strip().lower(),
                "key": key,
                "required": bool(re.search(r"\bNOT\s+NULL\b", part, re.IGNORECASE)) or key == "PK",
                "note": "",
            })

        for f in fields:
            if f["name"] in pk_cols:
                f["key"] = "PK"
                f["required"] = True
            elif f["name"] in uq_cols and not f["key"]:
                f["key"] = "UK"
            if f["name"] in fks and f["key"] != "PK":
                f["key"] = "FK"

        entities.append({"id": eid, "label": table.upper(),
                         "category": "unassigned", "fields": fields})
        for col, ref in fks.items():
            relations.append({"from": ref, "to": eid, "cardinality": "one-to-many",
                              "label": col})

    known = {e["id"] for e in entities}
    relations = [r for r in relations if r["from"] in known and r["to"] in known]
    return {"figure": figure, "kind": "relational", "source": "sql",
            "entities": entities, "relations": relations}


# ------------------------------------------------------------------- from-json

def _typename(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    return type(v).__name__


def _iter_docs(paths):
    """Yield every top-level document. .ndjson/.jsonl yield one per line."""
    for p in paths:
        path = pathlib.Path(p)
        text = path.read_text()
        if path.suffix.lower() in (".ndjson", ".jsonl"):
            for line in text.splitlines():
                if line.strip():
                    yield json.loads(line)
        elif path.suffix.lower() in (".yaml", ".yml"):
            try:
                import yaml
            except ImportError:
                raise SpecError(f"{p} is YAML but PyYAML is not installed.")
            doc = yaml.safe_load(text)
            yield from doc if isinstance(doc, list) else [doc]
        else:
            doc = json.loads(text)
            yield from doc if isinstance(doc, list) else [doc]


def from_json(paths, figure: str, max_depth: int = 4, max_fields: int = 25) -> dict:
    # entity id -> field name -> {"types": Counter, "seen": int}
    shape = collections.OrderedDict()
    # entity id -> observed document count
    totals = collections.Counter()
    # (parent, child) -> cardinality
    links = collections.OrderedDict()
    truncated = set()

    def walk(obj, eid, depth):
        totals[eid] += 1
        fields = shape.setdefault(eid, collections.OrderedDict())
        for k, v in obj.items():
            entry = fields.setdefault(k, {"types": collections.Counter(),
                                          "elems": collections.Counter(),
                                          "child": None, "seen": 0})
            entry["seen"] += 1
            entry["types"][_typename(v)] += 1

            if isinstance(v, dict):
                child = "{}.{}".format(eid, k)
                if depth + 1 > max_depth:
                    truncated.add(child)
                    continue
                entry["child"] = child
                links[(eid, child)] = "contains-one"
                walk(v, child, depth + 1)
            elif isinstance(v, list):
                # Union element types across every document, once per field —
                # typing each occurrence separately produces a combinatorial mess.
                for e in v:
                    entry["elems"][_typename(e)] += 1
                elems = [e for e in v if isinstance(e, dict)]
                if elems:
                    child = "{}.{}".format(eid, k)
                    if depth + 1 > max_depth:
                        truncated.add(child)
                        continue
                    entry["child"] = child
                    links[(eid, child)] = "contains-many"
                    for e in elems:
                        walk(e, child, depth + 1)

    docs = 0
    for doc in _iter_docs(paths):
        if not isinstance(doc, dict):
            continue
        docs += 1
        walk(doc, figure, 1)

    if not docs:
        raise SpecError("no object documents found in the given paths")

    entities = []
    for eid, fields in shape.items():
        total = totals[eid]
        out = []
        for name, entry in list(fields.items())[:max_fields]:
            types = collections.Counter({t: n for t, n in entry["types"].items() if n > 0})
            nullable = "null" in types
            named = sorted(t for t in types if t != "null")
            child = entry.get("child")
            rendered = []
            for t in named:
                if t == "array":
                    inner = sorted(x for x in entry["elems"] if x != "null")
                    if child:
                        rendered.append("array<{}>".format(child.split(".")[-1]))
                    else:
                        rendered.append("array<{}>".format("|".join(inner) or "empty"))
                elif t == "object" and child:
                    rendered.append(child.split(".")[-1])
                else:
                    rendered.append(t)
            required = entry["seen"] == total and not nullable
            note = "" if required else "seen {}/{}".format(entry["seen"], total)
            if nullable and entry["seen"] == total:
                note = "nullable"
            if entry["elems"] and len({x for x in entry["elems"] if x != "null"}) > 1:
                note = (note + "; " if note else "") + "heterogeneous array"
            out.append({"name": name, "type": "|".join(rendered) or "null",
                        "key": "", "required": required, "note": note})
        dropped = len(fields) - len(out)
        if dropped > 0:
            out.append({"name": "…", "type": "{} more fields".format(dropped),
                        "key": "", "required": False, "note": "truncated"})
        label = eid.split(".")[-1] if "." in eid else eid
        entities.append({"id": eid, "label": label, "category": "unassigned",
                         "fields": out, "observed": total})

    relations = [{"from": a, "to": b, "cardinality": c,
                  "label": b.split(".")[-1]} for (a, b), c in links.items()]

    spec = {"figure": figure, "kind": "document", "source": "json",
            "documents_sampled": docs, "entities": entities, "relations": relations}
    if truncated:
        spec["truncated_at_depth"] = sorted(truncated)
    return spec


# ------------------------------------------------------------------------ main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="check a spec and list its component ids")
    v.add_argument("spec")

    s = sub.add_parser("from-sql", help="build a spec from CREATE TABLE statements")
    s.add_argument("sql")
    s.add_argument("-o", "--out")
    s.add_argument("--figure")

    j = sub.add_parser("from-json", help="infer a spec from sample documents")
    j.add_argument("docs", nargs="+")
    j.add_argument("-o", "--out")
    j.add_argument("--figure")
    j.add_argument("--max-depth", type=int, default=4)
    j.add_argument("--max-fields", type=int, default=25)

    a = ap.parse_args(argv)

    if a.cmd == "validate":
        spec = load(a.spec)
        problems = validate(spec)
        ids = component_ids(spec)
        print("entities {}  relations {}  component ids {}".format(
            len(spec.get("entities") or []), len(spec.get("relations") or []), len(ids)))
        for p in problems:
            print("  PROBLEM: " + p)
        return 1 if problems else 0

    figure = a.figure or os.path.splitext(os.path.basename(
        a.sql if a.cmd == "from-sql" else a.docs[0]))[0]
    figure = re.sub(r"[^a-z0-9_-]", "_", figure.lower())

    if a.cmd == "from-sql":
        spec = from_sql(pathlib.Path(a.sql).read_text(), figure)
    else:
        spec = from_json(a.docs, figure, a.max_depth, a.max_fields)

    problems = validate(spec)
    out = a.out or "{}/{}_model.json".format("resources/data", figure)
    dump(spec, out)
    print("wrote {}  entities {}  relations {}".format(
        out, len(spec["entities"]), len(spec["relations"])))
    print("every entity landed in category 'unassigned' — group them before drawing")
    for p in problems:
        print("  PROBLEM: " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SpecError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        sys.exit(2)
