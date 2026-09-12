---
name: figure-authoring
description: Author a figure through a written visualization prompt, then render it locally with the draw.io desktop tool. Invoke whenever a diagram, schematic, architecture sketch, flow, block diagram, chart, or explanatory illustration is being produced or revised for a document, paper, README, slide, or design note — including when the request is phrased as "draw", "sketch", "make a figure", "add a diagram", or "update the diagram" after the system it depicts changed. Also covers figures of a data model — an ER diagram, a database schema, tables and foreign keys, a JSON or YAML document shape, a class or type model — from a schema file, from sample documents, or from a prose description. Collects content and style requirements into a prompt, completes the missing colour, type, and layout specifications automatically, and renders a raster image on the local machine.
disable-model-invocation: true
---

# Figure authoring

**Objective.** Turn a figure request into a written visualization prompt, complete that
prompt into a full specification without interrogating the requester, and render it to a
raster image with the local draw.io tool.

**Your tasks.** Confirm draw.io is available, collect the requirements into a prompt,
complete the specification, generate the source — from a model spec when the figure
depicts a data model — then validate, render, and verify by looking.

Perform them in order. Each states the conditions under which it applies.

## 0. Keep every artifact local

Render on this machine only. Never upload a diagram to `app.diagrams.net` or any other
hosted editor, and never build a `#create=` payload URL that carries diagram content to a
web service. A figure routinely encodes unreleased architecture and internal topology, and
a link cannot be recalled once shared.

Deliver files. When someone needs to edit the figure elsewhere, hand them the `.drawio`
file and let them open it in their own installation.

## 1. Confirm draw.io is available before you start

Check first, before writing a prompt or a line of XML. Discovering a missing renderer
after the specification is written wastes the whole pass.

```bash
.agents/skills/figure-authoring/scripts/drawio --check
```

When it exits `127`, say so at once and choose: either the requester installs draw.io, or
you author the `.drawio` file and deliver it unrendered. Never silently skip the render
and present the source as though it were the finished figure.

## 2. Collect the requirements into a visualization prompt

Every figure owns these files, named for the figure, relative to the project root:

| Path | Role |
| --- | --- |
| `resources/img_prompt/<figure>_prompt.md` | the **prompt** — the retained specification |
| `resources/img/<figure>.drawio` | the **source** — the editable diagram |
| `resources/img/<figure>.png` | the **render** — the accepted output, carrying the source inside it |
| `resources/data/<figure>_model.json` | the **model spec** — data-model figures only, see section 4 |

Create the directories and files as you reach them — that is your job, not a precondition
to wait on. Retain them all when the figure is finished.

Name the figure in lowercase from `[a-z0-9_-]`, and use that one name in every path.
Import the prefixes rather than retyping them:
`.agents/skills/figure-authoring/scripts/figure_paths.py`.

Write the prompt first. It outlives the source and the render, and it is what a later
pass reads to reproduce or revise the figure.

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

Keep **Instance data** literal — lists, pairs, counts — because the source is derived from
it and a later reader checks the figure against it. A data-model figure keeps its instance
data in the model spec and points at it from here.

### Finalize a component id for every component

Give every node, edge, group, and legend key its own **component id**, and settle it here.
Downstream steps carry that id; they never invent one.

Declare each one on its own line, in the form `id: <value>`. The check in section 5 reads
that form; an id written any other way is invisible to it and the check passes vacuously.

Write each id in lowercase from `[a-z0-9_.:-]`, with no spaces, so it needs no XML
escaping and cannot trip the entity traps in section 5.

An id names the component, not its label. Never regenerate an id on a later pass, and
never use a randomly generated value: a component keeps the id it was given for the life
of the figure. Keep ids unique within the figure.

## 3. Complete the specification

Read the prompt back and fill every gap yourself, then write the choices into the same
prompt file so they are recorded rather than re-improvised on the next pass.

Ask the requester only where a choice changes the figure's meaning and the documents give
no answer. A figure blocked on a style question is a figure that did not get drawn — pick
something, record it, move on.

Decide and record at least these:

| Decision | What to record |
| --- | --- |
| **Colour** | which fill and stroke each category of thing takes, and what each colour means |
| **Type** | the family, and a size for each level of the hierarchy |
| **Shape** | which shape each category takes |
| **Edge semantics** | what a connector means, and the line style for each meaning |
| **Layout** | the direction the structure implies, and the preset from section 6 that produces it |
| **Grouping** | which nodes sit inside a container, and what the container means |
| **Legend** | every distinction the figure uses |

The choices are yours. Recording them is what lets a later pass revise the figure without
re-deriving the whole design, and what lets section 7 check the render against something.

Two of these are constrained by the tool rather than by taste:

- **State a font family and size in every style string.** A cell that omits them falls back
  to the viewer's default, so the figure renders differently on another machine.
- **Name the layout preset from section 6**, since those are the only presets draw.io
  accepts.

## 4. Generate a data-model figure

Apply when the figure depicts the structure of data: database tables and their keys, a
document shape, a class or type model.

These tools take a **model spec** — the figure's instance data as literal JSON — and emit a
diagram from it. Section 2 points at the spec instead of repeating it, and every component
id derives from it mechanically, so a hundred-field model stays joined to its prompt.

### 4.1 Build the model spec

Write it to `resources/data/<figure>_model.json`. Its `kind` selects the Mermaid diagram
type the emitter targets:

| `kind` | Emits | Which draws |
| --- | --- | --- |
| `relational` | `erDiagram` | tables with typed columns, key markers, crow's-foot cardinality |
| `document` | `classDiagram` | records with typed fields, nesting as composition, multiplicities |

Two importers build the spec from what already exists, so forty columns need not be
retyped by hand:

```bash
python3 .agents/skills/figure-authoring/scripts/model_spec.py from-sql <schema.sql> --figure <figure>
python3 .agents/skills/figure-authoring/scripts/model_spec.py from-json <samples...> --figure <figure>
```

`from-sql` reads `CREATE TABLE` for columns, types, primary keys, and foreign keys.
`from-json` walks sample JSON, NDJSON, or YAML documents and derives the shape: which
fields are always present, which appear in only some documents and in how many, which are
nullable, which arrays hold mixed types, and where objects nest. It counts rather than
guesses, and caps depth and field count so a large document still yields a figure.

Write the spec by hand when neither a schema nor samples exist. Then validate it:

```bash
python3 .agents/skills/figure-authoring/scripts/model_spec.py validate resources/data/<figure>_model.json
```

### 4.2 Group the entities

An importer puts every entity in one category, because it cannot know which one the figure
is about. Set `category` on each entity to whatever grouping the figure needs — the term is
yours to choose. It travels into the source as `spec_category`, so it is what lets a later
pass ask which components belong together.

An importer reports what the schema or the samples contain, which is not necessarily what
the figure should show. Edit the spec before drawing it — what stays and what goes is your
call, and section 2 has a place to record why.

### 4.3 Emit the prompt and the source

```bash
python3 .agents/skills/figure-authoring/scripts/model_figure.py <figure> --emit prompt
python3 .agents/skills/figure-authoring/scripts/model_figure.py <figure> --emit drawio
```

`--emit prompt` scaffolds the prompt with every component id already declared, and with
the derived entity, field, and relation counts filled in. Write the Claim, Audience,
Emphasis, Exclusions, and Destination into it yourself.

`--emit drawio` converts the spec through draw.io's Mermaid parser, which lays the diagram
out, then attaches each component's `spec_id` and `spec_category` — the one thing the
converter will not do. It leaves the converter's own styling alone; restyle the result
however the figure needs. Converting hand-written Mermaid yourself works too, but the
result carries no `spec_id`, so nothing joins it back to the prompt.

Inspect `--emit mermaid` when a conversion produces something unexpected; it prints the
text being converted without writing anything.

**draw.io exits `0` on a Mermaid diagram type it does not support and writes a diagram
with no labels.** Only `erDiagram` and `classDiagram` are verified here; `treeView-beta`
and `treemap-beta` convert to an empty skeleton. `--emit drawio` fails loudly on a
labelless result rather than letting one through.

Skip the layout pass for the figure this produces. The Mermaid parser has already placed
everything, and section 6 detects this and skips it for you.

## 5. Generate the diagram source

Write the source to `resources/img/<figure>.drawio`, generating it from the instance data
recorded in section 2. Section 4 already wrote the source for a data-model figure; this
section covers everything else.

**Derive every number.** Never type a count, total, or percentage into a figure. Compute
it from the instance data and assert the result in the generator.

Author the structure and let the layout engine place it — supply `0,0` for every
coordinate. Name the nodes and their connections; never compute a coordinate by hand.

### Carry the component id into the source

Wrap every component in an `<object>` so it carries its component id and its category as
attributes. draw.io shows these under *Edit Data* and never draws them, so the join stays
invisible in the render:

```xml
<object id="n1" label="Ingest" spec_id="ingest" spec_category="internal">
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

Carry `spec_category` alongside the id, naming the grouping you recorded in section 3.
That turns "is this drawn the way its category should be?" into a lookup rather than a
guess.

Never rely on `id` alone for this: draw.io rewrites `id` values when it repairs a
collision, and reorders attributes as it saves, but it has no reason to touch `spec_id`.

### Avoid the four traps

- Give every edge an `<mxGeometry>` child. A self-closing edge silently fails to render.
- Break a label across lines with `&#10;`. A literal newline in the `value` attribute
  collapses to a space, and the label overruns the shape that was sized to hold it.
- Double-escape a literal angle bracket in any label carrying `html=1`: write
  `&amp;lt;name&amp;gt;` to display `<name>`. A single `&lt;name&gt;` survives the XML
  parse, then the HTML pass reads it as a tag and drops it — the label renders with the
  placeholder silently missing, which is easy to miss in a path like `img/<figure>.png`.
- Never emit XML comments. They buy nothing and break parsing.

For a standard flow, sequence, class, state, or ER diagram, prefer Mermaid as the source
language and let its parser lay the diagram out — section 4 for a data model, or
`render_figure.py --from-mermaid` for anything else.

### Check the source before rendering

```bash
python3 .agents/skills/figure-authoring/scripts/check_figure.py <figure>
```

It reports the defects the render cannot show you: an id the prompt declared and the
source omits, a `spec_id` used twice, a dangling edge, an edge with no geometry, a literal
newline in a label, a label whose angle brackets the HTML pass will eat, and an XML
comment. It notes, without failing, any cell that states no font.

It checks correctness, never taste. It has no opinion on your colours, type sizes, or
shapes.

Fix what it reports before you render. draw.io accepts every one of these and simply omits
the broken part from the picture, so a figure that fails this check still looks finished.

## 6. Render and display locally

```bash
python3 .agents/skills/figure-authoring/scripts/render_figure.py <figure> [--layout verticalFlow] [--scale 2]
```

One call validates the source, lays it out, exports the PNG with the source embedded, and
opens it. Presets are `verticalFlow`, `horizontalFlow`, `verticalTree`, `horizontalTree`,
`radialTree`, `organic`, and `libavoid` — the last routes connectors around shapes without
moving any node, which suits a diagram you positioned deliberately.

Pass `--scale 2` when the figure carries small type and will be viewed at full page width;
draw.io rasterises at the scale you ask for, so ask here rather than resampling after.
Pass `--no-layout` to keep positions you placed on purpose. A source that draw.io's Mermaid
parser already placed is detected and its layout pass skipped.

Validation runs before the layout pass, without `--layout`, and writes to a throwaway
path — the layout pass accepts malformed XML that a plain export rejects.

Never discard the source after exporting. A figure is revised far more often than it is
created, and a render whose source is gone forces the next change to start over.

## 7. Verify by looking

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

Consult these when a style string, shape library, or CLI flag is not covered above — never
guess at a style string:

- `https://github.com/jgraph/drawio` — the editor, its shape libraries and style semantics
- `https://github.com/jgraph/drawio-desktop` — the desktop build and its command line
- `https://raw.githubusercontent.com/jgraph/drawio-mcp/main/shared/xml-reference.md`
- `https://raw.githubusercontent.com/jgraph/drawio-mcp/main/shared/style-reference.md`
- `https://raw.githubusercontent.com/jgraph/drawio-mcp/main/shared/mermaid-reference.md`

When the session already carries a dedicated draw.io skill, follow it for XML and layout
syntax rather than restating it here; this skill governs the prompt, the specification,
and the verification around it.
