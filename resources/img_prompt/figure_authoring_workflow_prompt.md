# figure_authoring_workflow

## Claim
The figure-authoring skill runs six ordered steps that turn a request into three retained
artifacts, and every step happens on the local machine.

## Audience
Someone deciding whether to install this skill, or invoking it for the first time. They
know what a diagram is; they do not know this skill's vocabulary, its file layout, or that
a preflight gate exists.

## Instance data
steps:
  - {id: s1, label: "Confirm draw.io\nis available",      kind: gate}
  - {id: s2, label: "Collect requirements\ninto a prompt", kind: step}
  - {id: s3, label: "Complete the\nspecification",         kind: step}
  - {id: s4, label: "Generate the\ndiagram source",        kind: step}
  - {id: s5, label: "Validate, lay out,\nexport, display",  kind: step}
  - {id: s6, label: "Verify by\nlooking",                  kind: step}
artifacts:
  - {id: a1, label: "resources/img_prompt/\n<figure>_prompt.md", produced_by: s3}
  - {id: a2, label: "resources/img/\n<figure>.drawio",           produced_by: s4}
  - {id: a3, label: "resources/img/\n<figure>.png",              produced_by: s5}
fallback:
  - {id: f1, label: "Deliver the source\nunrendered", reached_from: s1}
flow:
  - {id: fl.s1-s2, from: s1, to: s2, label: found}
  - {id: fl.s2-s3, from: s2, to: s3}
  - {id: fl.s3-s4, from: s3, to: s4}
  - {id: fl.s4-s5, from: s4, to: s5}
  - {id: fl.s5-s6, from: s5, to: s6}
produces:
  - {id: pr.s3-a1, from: s3, to: a1}
  - {id: pr.s4-a2, from: s4, to: a2}
  - {id: pr.s5-a3, from: s5, to: a3}
fallback_edge:
  - {id: fb.s1-f1, from: s1, to: f1, label: missing}
revise:
  - {id: rv.s6-s4, from: s6, to: s4, label: "on defect"}

Component ids above are final. Every id appears once in the generated source as
`spec_id`, and nothing in the source carries an id absent from this list. Annotation and
legend components are minted here too, under the `an.` and `lg.` prefixes.

## Emphasis
The three retained artifacts, and the gate at step 1. A reader who takes away only that
the skill checks for draw.io before writing anything and leaves three files behind has
the point.

## Exclusions
The colour, font, and chart sub-specifications inside step 3 — naming them would triple
the node count and bury the six-step spine. The local-only constraint is stated in the
caption rather than drawn, because it governs every step and would need six edges.

## Destination
Project README, screen, light background, roughly 800px wide.

## Colour theme (generated)
| Category | Role | Fill | Stroke |
| --- | --- | --- | --- |
| gate | attention, boundary | #ffe6cc | #d79b00 |
| step | healthy, internal | #d5e8d4 | #82b366 |
| artifact | primary subject | #dae8fc | #6c8ebf |
| fallback | deferred, out of scope | #f5f5f5 | #666666 |

Four fills plus no neutral spare — within the five-fill cap.

## Font configuration (generated)
Family Helvetica throughout; Courier New for the artifact paths, which are literal file
paths. Node label 12 regular; artifact path 10 regular; edge label 10 regular;
caption 11 italic; title 18 bold.

## Chart and graph specification (generated)
- Shape per category: gate = rhombus; step = rounded rectangle; artifact = note;
  fallback = dashed rounded rectangle.
- Edge semantics, one line style each:
  solid = "proceeds to"; dashed = "produces"; dotted = "revise on defect".
- Gate outcomes are labelled "found" and "missing"; no other edge is labelled except the
  revise loop.
- Layout: verticalFlow — the structure is a pipeline with one branch and one back-edge.
- Legend: lists all four categories and all three edge meanings. Placed after layout,
  outside the graph's bounding box, so the layout engine does not treat legend keys as
  pipeline nodes.
- Encoding redundancy: every category carries fill + shape; artifacts additionally carry
  a monospace path as their label, and the fallback carries a dashed outline.
