#!/usr/bin/env python3
"""Check that every component id declared in a figure's prompt reaches its source.

    check_ids.py <figure>

Reads the declared ids from the prompt and the spec_id attributes from the .drawio,
then reports three things:

  missing    declared in the prompt, absent from the source  -> exit 1
  duplicate  the same spec_id used twice in the source       -> exit 1
  undeclared present in the source, not in the prompt        -> reported, not fatal

Undeclared ids are informational because titles, captions, and legend keys are minted
during generation rather than being instance data. A missing id is always a defect: a
component the prompt promised never reached the picture.
"""
import re, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from figure_paths import PROMPT, SOURCE

DECLARED = re.compile(r"\bid:\s*([A-Za-z0-9_.:-]+)")
IN_SOURCE = re.compile(r'spec_id="([^"]+)"')


def main(figure: str) -> int:
    prompt, source = pathlib.Path(PROMPT.format(figure=figure)), pathlib.Path(SOURCE.format(figure=figure))
    for f in (prompt, source):
        if not f.exists():
            print(f"missing file: {f}", file=sys.stderr)
            return 2

    declared = set(DECLARED.findall(prompt.read_text()))
    found = IN_SOURCE.findall(source.read_text())
    missing = sorted(declared - set(found))
    duplicate = sorted({i for i in found if found.count(i) > 1})
    undeclared = sorted(set(found) - declared)

    print(f"declared {len(declared)}  in source {len(set(found))}")
    if undeclared:
        print(f"  undeclared (ok): {len(undeclared)} -> {', '.join(undeclared[:6])}"
              f"{' …' if len(undeclared) > 6 else ''}")
    if missing:
        print(f"  MISSING: {', '.join(missing)}")
    if duplicate:
        print(f"  DUPLICATE: {', '.join(duplicate)}")
    return 1 if (missing or duplicate) else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
