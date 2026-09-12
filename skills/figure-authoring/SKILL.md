---
name: figure-authoring
description: Author a figure through a written visualization prompt, then render it locally with the draw.io desktop tool. Invoke whenever a diagram, schematic, architecture sketch, flow, block diagram, chart, or explanatory illustration is being produced or revised for a document, paper, README, slide, or design note — including when the request is phrased as "draw", "sketch", "make a figure", "add a diagram", or "update the diagram" after the system it depicts changed. Collects content and style requirements into a prompt, completes the missing colour, type, and layout specifications automatically, and renders a raster image on the local machine.
disable-model-invocation: true
---

# Figure authoring

**Objective.** Turn a figure request into a written visualization prompt, complete that
prompt into a full specification without interrogating the requester, and render it to a
raster image with the local draw.io tool.

**Your tasks.** Confirm draw.io is available, collect the requirements into a prompt,
complete the specification, generate the diagram source, validate and render it locally,
and verify by looking.

Perform all six in order. Each states the conditions under which it applies.

## 0. Keep every artifact local

Render on this machine only. Never upload a diagram to `app.diagrams.net` or any other
hosted editor, and never build a `#create=` payload URL that carries diagram content to a
web service. A figure routinely encodes unreleased architecture, customer names, and
internal topology; a URL that carries it off the machine publishes all of that, and the
link cannot be recalled once shared.

Deliver files. When someone needs to edit the figure elsewhere, hand them the `.drawio`
file and let them open it in their own installation.

## 1. Confirm draw.io is available before you start

Check first, before writing a prompt or a line of XML. Discovering a missing renderer
after the specification is written wastes the whole pass.

```bash
.agents/skills/figure-authoring/scripts/drawio --check
```

The resolver finds the draw.io desktop binary on macOS, Linux, WSL2, and Windows, honours
a `DRAWIO_CMD` override, and reports the resolved path and version. It exits `127` with
installation instructions when the app is absent.

When it exits `127`, say so at once and choose: either the requester installs draw.io, or
you author the `.drawio` file and deliver it unrendered. Never silently skip the render
and present the source as though it were the finished figure.

## 2. Collect the requirements into a visualization prompt

Every figure owns three files, named for the figure, relative to the project root:

| Path | Role |
| --- | --- |
| `resources/img_prompt/<figure>_prompt.md` | the **prompt** — the retained specification |
| `resources/img/<figure>.drawio` | the **source** — the editable diagram |
| `resources/img/<figure>.png` | the **render** — the accepted output, carrying the source inside it |

Create both directories and all three files as you reach them — that is your job, not a
precondition to wait on. Retain all three when the figure is finished.

Name the figure in lowercase from `[a-z0-9_-]`, and use that one name in all three paths.

Generators may import these prefixes instead of retyping them:
`.agents/skills/figure-authoring/scripts/figure_paths.py`.

Write the prompt first. It is the retained specification: it outlives the source and the
render, and it is what a later pass reads to reproduce or revise the figure.

Record these, gathering from the request, the surrounding documents, and the code:

| Section | What it holds |
| --- | --- |
| **Claim** | the one sentence a reader should be able to say after looking at the figure |
| **Audience** | who reads it and what they already know |
| **Instance data** | the concrete nodes, groups, counts, and connections this figure depicts, written as literal data rather than prose, each carrying a component id |
| **Emphasis** | what must be noticed first, and what is context |
| **Exclusions** | what to keep out, and why it was cut |
| **Destination** | where the figure will appear — page width, print or screen, light or dark background |

Write the **Claim** before anything else. When you cannot write it, you do not yet know
what the figure is for, and drawing will not tell you.

Keep **Instance data** literal — lists, pairs, counts — because section 4 derives the
figure from it and a later reader checks the figure against it.

### Finalize a component id for every component

Give every node, edge, group, and legend key its own **component id**, and settle it here.
Downstream steps carry that id; they never invent one. The prompt is the only place an id
is minted, which is what lets a later pass join the rendered figure back to this file and
prove the two still agree.

Write each id in lowercase from `[a-z0-9_.:-]`, with no spaces, so it needs no XML
escaping and cannot trip the entity traps in section 4.

An id names the component, not its label. When the label changes, the id does not follow —
that is the point of having one, because it survives the rename that would break a join
keyed on displayed text.

Never regenerate ids on a later pass. A component keeps the id it was given for the life
of the figure, and a regenerated id is indistinguishable from a deleted component plus a
new one. For the same reason, never use a randomly generated value: it changes on every
run, so the source and the exported image differ byte for byte even when the picture is
identical, and a reviewer can no longer tell a real change from a re-run.

Keep ids unique within the figure. Uniqueness is worth asserting rather than assuming —
duplicating a component in the draw.io editor duplicates its id along with it.

## 3. Complete the specification

Read the prompt back and fill every gap yourself. Generate the colour theme, the font
configuration, and the chart and graph specification, then write them into the same
prompt file so the choices are recorded rather than re-improvised next time.

Ask the requester only where a choice changes the figure's meaning and the documents give
no answer. Style is not such a choice. A figure blocked on "what colour would you like?"
is a figure that did not get drawn.

### 3.1 Generate the colour theme

Assign a fill and a matching stroke to every category in the instance data, drawn from
draw.io's built-in palette so the figure looks native in the editor and prints cleanly:

| Role | Fill | Stroke |
| --- | --- | --- |
| primary subject | `#dae8fc` | `#6c8ebf` |
| healthy, accepted, internal | `#d5e8d4` | `#82b366` |
| attention, third-party, boundary | `#ffe6cc` | `#d79b00` |
| failure, rejected, risk | `#f8cecc` | `#b85450` |
| alternate grouping | `#e1d5e7` | `#9673a6` |
| deferred, out of scope, context | `#f5f5f5` | `#666666` |

Record in the prompt which category takes which role. Never assign a colour without a
recorded meaning — an unexplained hue reads as significant and sends the reader hunting.

Cap the palette at five meaningful fills plus the neutral. Past that a reader stops
decoding colour and starts ignoring it.

### 3.2 Generate the font configuration

Choose one family for the whole figure and state it in every style string, because a cell
without `fontFamily` silently falls back to the viewer's default and the figure renders
differently on another machine. Prefer the families draw.io ships with — `Helvetica`,
`Verdana`, `Times New Roman`, `Courier New` — and reserve the monospace family for
literal identifiers, paths, and code.

Set a type scale with visible steps, then record it in the prompt:

| Element | Size | Weight |
| --- | --- | --- |
| figure title | 18 | bold |
| group or lane heading | 14 | bold |
| node label | 12 | regular |
| edge label | 10 | regular |
| caption, footnote, legend | 11 | italic for the caption |

Never place two sizes within one point of each other. A step a reader cannot see is not a
hierarchy, only noise.

### 3.3 Generate the chart and graph specification

Resolve the figure's structure into concrete drawing decisions and record each one:

- **Shape per category.** Give every category one shape, and reserve that shape for that
  meaning alone. Never let one shape carry two distinctions at once.
- **Edge semantics.** State what a connector means — data flow, dependency, call,
  containment — and give each meaning one line style. Label the edges only where the
  meaning is not obvious from the nodes.
- **Layout.** Pick the direction the structure implies: a flow reads top-to-bottom or
  left-to-right, a hierarchy reads as a tree, a peer network reads as an organic graph.
  Name the preset from section 5.
- **Grouping.** State which nodes sit inside a container and what the container means.
- **Legend.** List every distinction the figure uses. Never list one it does not use.
- **Encoding redundancy.** Carry every distinction on at least two channels — fill *and*
  shape, or fill *and* an explicit word. Readers print in greyscale, project through poor
  projectors, and read with colour-vision deficiency; hue alone survives none of those.

Treat everything recorded in this section as binding. Before rendering, read the generated
source back against it and confirm each choice survived: every fill and stroke comes from
the theme table, every cell states the family and size the type scale assigned it, every
category keeps its one shape, and the legend lists exactly the distinctions the figure
uses. A specification the source quietly diverged from is worse than none, because the
next pass trusts it.

## 4. Generate the diagram source

Write the source to `resources/img/<figure>.drawio`, generating it from the instance data
recorded in section 2.

**Derive every number.** Never type a count, total, or percentage into a figure. Compute
it from the instance data and assert the result in the generator. A typed number is
correct only on the day it was typed; when the instance changes, a derived number changes
with it and a typed one silently becomes a lie. These assertions are the only ones worth
writing, because they check the one thing your eyes cannot confirm from the render.

Author the structure and let the layout engine place it — supply `0,0` for every
coordinate. Getting the structure right means naming the nodes and their connections;
hand-computed coordinates are the most expensive and most fragile way to draw.

### Carry the component id into the source

Wrap every component in an `<object>` so it carries its component id and its category as
attributes. draw.io shows these under *Edit Data* and never draws them, so the join stays
invisible in the render:

```xml
<object id="n1" label="Ingest" spec_id="ingest" spec_category="step">
  <mxCell style="rounded=1;fillColor=#d5e8d4;strokeColor=#82b366;fontFamily=Helvetica;fontSize=12;"
          vertex="1" parent="1">
    <mxGeometry x="0" y="0" width="160" height="50" as="geometry"/>
  </mxCell>
</object>
```

Inside an `<object>`, `label` holds the displayed text in place of `value`, and the
`<mxCell>` becomes a child that carries no `id` of its own. Custom attributes survive the
layout pass and the export, and they reach the embedded copy inside the PNG, so a rendered
figure can always be joined back to its prompt.

Carry `spec_category` alongside the id, naming the category from the theme table in
section 3.1. That turns style checking into a lookup rather than a guess: read the
category, then confirm the fill, stroke, and shape are the ones that category declared.
With a hundred components no other method scales.

Check the join before rendering:

```bash
python3 .agents/skills/figure-authoring/scripts/check_ids.py <figure>
```

It fails when an id declared in the prompt never reached the source — a component the
prompt promised and the picture omits — and when one `spec_id` is used twice, which is how
a copy-paste in the draw.io editor shows up. Ids present in the source but absent from the
prompt are reported without failing, because titles, captions, and legend keys are minted
during generation rather than being instance data.

Never rely on `id` alone for this: draw.io rewrites `id` values when it repairs a
collision, and reorders attributes as it saves, but it has no reason to touch `spec_id`.

A `.drawio` file is mxGraphModel XML. Cell `0` is the root and cell `1` the default layer;
every element sets `parent="1"`:

```xml
<mxGraphModel adaptiveColors="auto">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="n1" value="Ingest"
            style="rounded=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontFamily=Helvetica;fontSize=12;"
            vertex="1" parent="1">
      <mxGeometry x="0" y="0" width="160" height="50" as="geometry"/>
    </mxCell>
    <mxCell id="e1" edge="1" parent="1" source="n1" target="n2">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>
```

Give every cell a unique `id`, and give every edge its `<mxGeometry>` child — a
self-closing edge silently fails to render. Escape `&amp;`, `&lt;`, `&gt;`, and `&quot;`
in attributes. Never emit XML comments; they buy nothing and break parsing.

Break a label across lines with `&#10;`. A literal newline in the `value` attribute
collapses to a space, and the label then overruns the shape that was sized to hold it.

Double-escape a literal angle bracket in any label carrying `html=1`: write
`&amp;lt;name&amp;gt;` to display `<name>`. A single `&lt;name&gt;` survives the XML parse,
then the HTML pass reads it as a tag and drops it — the label renders with the placeholder
silently missing, which is easy to miss in a path like `img/<figure>.png`.

Prefer Mermaid as the source language for a standard flow, sequence, class, state, or ER
diagram, converting it with `-f xml`, because its parser lays the diagram out for you.

## 5. Validate, lay out, export, and display locally

Validate the source before anything else touches it. Export it to XML with a throwaway
output path and stop on a non-zero exit:

```bash
.agents/skills/figure-authoring/scripts/drawio \
  -x -f xml -o /tmp/validate-<figure>.xml resources/img/<figure>.drawio || exit 1
```

Three details make this the check and not a formality:

- **Omit `--layout`.** The layout pass loads the model leniently and salvages what it can,
  so it accepts malformed XML that a plain export rejects.
- **Write to a throwaway path.** Never validate in place. A pass that writes over the
  source turns a broken file into a well-formed one and destroys the evidence with it.
- **Run it before the layout pass**, on the file section 4 just generated.

This catches a truncated or malformed file, an empty one, and a file that is not a diagram
at all. It does not catch a dangling edge reference, a missing root cell, or an edge with
no geometry — draw.io accepts all three and silently omits them from the picture. Assert
those in the generator, where the instance data is still in hand.

Then lay out in place, reading and overwriting the same file:

```bash
.agents/skills/figure-authoring/scripts/drawio \
  -x -f xml --layout verticalFlow \
  -o resources/img/<figure>.drawio resources/img/<figure>.drawio
```

Presets are `verticalFlow`, `horizontalFlow`, `verticalTree`, `horizontalTree`,
`radialTree`, and `organic`. Apply `libavoid` instead to route connectors around shapes
without moving any node, which suits a diagram you positioned deliberately. Skip the
layout pass entirely for a Mermaid-converted diagram — its parser has already placed
everything.

Export to raster with `-e`, so the source travels inside the PNG and the image reopens as
an editable diagram:

```bash
.agents/skills/figure-authoring/scripts/drawio \
  -x -f png -e -b 12 \
  -o resources/img/<figure>.png resources/img/<figure>.drawio
```

Add `-s 2` when the figure carries small type and will be viewed at full page width;
draw.io rasterises at the scale you ask for, so ask once here rather than resampling after.

Display the result on the local machine:

| Platform | Command |
| --- | --- |
| macOS | `open resources/img/<figure>.png` |
| Linux | `xdg-open resources/img/<figure>.png` |
| WSL2 | `cmd.exe /c start "" "$(wslpath -w resources/img/<figure>.png)"` |
| Windows | `start resources/img/<figure>.png` |

When the open command fails, print the absolute path so the requester can open it by hand.

Never discard the source after exporting. A figure is revised far more often than it is
created, and a render whose source is gone forces the next change to start over.

## 6. Verify by looking

Read the exported image back and look at it. Collisions, clipping, and overlap are
invisible in the source and obvious in the render, so never write assertions about layout
that your eyes settle in one pass.

Check, in this order:

- **Nothing is unreadable.** No label clipped at an edge, overflowing its shape, or
  overlapping another label or a connector.
- **Every connector lands.** Each edge touches both endpoints and crosses no shape it
  does not connect.
- **The legend matches the canvas.** Every entry appears in the figure, and every
  distinction drawn appears in the legend.
- **The claim is legible.** The sentence from section 2 is what the figure actually shows.
- **It survives greyscale.** Every distinction is still readable with hue removed.

Fix what you find by changing the source and re-exporting, then look again. Report a
figure as finished only after looking at the render you are shipping — not at an earlier
one, and not at the source.

## Reference

The draw.io tool this skill wraps is open source. Consult these when a style string,
shape library, or CLI flag is not covered above — never guess at a style string:

| Resource | Use it for |
| --- | --- |
| `https://github.com/jgraph/drawio` | the editor itself — shape libraries, style semantics, issue history |
| `https://github.com/jgraph/drawio-desktop` | the desktop build and its command-line interface, including release notes for flag changes |
| `https://github.com/jgraph/drawio-mcp` | the model-facing references below, and the MCP servers that expose draw.io to agents |

The `drawio-mcp` repository publishes three references worth fetching in full:

- `https://raw.githubusercontent.com/jgraph/drawio-mcp/main/shared/xml-reference.md`
- `https://raw.githubusercontent.com/jgraph/drawio-mcp/main/shared/style-reference.md`
- `https://raw.githubusercontent.com/jgraph/drawio-mcp/main/shared/mermaid-reference.md`

When the session already carries a dedicated draw.io skill, follow it for XML and layout
syntax rather than restating it here; this skill governs the prompt, the specification,
and the verification around it.
