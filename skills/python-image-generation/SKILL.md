---
name: python-image-generation
description: Draw a raster figure with a deterministic Python renderer — no image model in the loop. Invoke when authoring a diagram, chart, or illustration as a PNG, writing a figure prompt, or rendering with Pillow.
disable-model-invocation: true
---

# Python image generation

**Objective.** Produce a raster figure from a written specification and a temporary
Python renderer, then keep only the prompt and the accepted PNG.

**Your tasks.** Author the prompt and renderer as a pair, apply the drawing rules,
avoid the known failure modes, and verify the PNG by looking at it.

## 1. Author the prompt and the renderer

There is no image model in the loop. Draw the figure with a deterministic Python
program. That program is a temporary production tool.

| Artifact | Role |
| --- | --- |
| `resources/img_prompt/<figure>_prompt.txt` | the retained **specification** — format, palette, type scale, instance, layout, what to keep out |
| `tools/render_<figure>.py` | the temporary **renderer** — the only implementation while the figure is being produced |
| `resources/img/<figure>.png` | the retained **accepted output** |

Create a missing prompt or renderer — that is your job, not a precondition to wait on.
Keep the prompt and the renderer in step. When the render cannot do what the prompt
describes, change the prompt. A prompt that describes a figure nobody drew is worse
than no prompt.

Once the output is accepted, delete the renderer and any private drawing helper.
Retain the prompt and the accepted PNG. Later visual changes start a new authoring
pass. Never claim the retained PNG can still be reproduced from source.

## 2. Apply the drawing rules

**Author the instance as data, derive every number.** Put item lists, group membership,
and which containers are touched in one dict at the top of the renderer. Compute every
count printed in the figure from that dict. Never type a number into the figure, so a
changed instance cannot leave a stale total behind.

**Draw at 2× and downsample once with LANCZOS.** Small type, hatch lines, and hairline
rules are otherwise ragged. Do it at the end, in one place — never per element.

**Encode state on three channels, never on colour.** Fill *and* shape *and* a word.
Reserve shape for one meaning only, and say in the legend which meaning it carries.
Never let a shape do double duty (packaging *and* selection state).

**Fonts.** Load `SFNS.ttf` / `SFNSMono.ttf` from `/System/Library/Fonts` and select
weight with `set_variation_by_name` — the SF variable fonts expose `Regular`…`Bold`.
Cache by `(size, weight, mono)`. Use `anchor=` rather than measuring by hand.

**Draw glyphs, do not type them.** A check mark set as text depends on a face that may
not have it, and `.notdef` renders as a box that passes a naive "is it blank" test.
Two lines cost less. Do the same for Unicode subscripts.

**Composite silhouettes need a mask.** To hatch or fill a shape made of several
primitives, draw the primitives into an `L` mask and paste through it. Paste
coordinates must be `int` — Pillow raises on floats, and the accumulator in a laid-out
row will produce them.

## 3. Avoid the known failure modes

**A figure that takes minutes is hung, not slow.** A static 1920 × 1080 frame renders
in about 0.2 s. If it does not, stop optimising and find the loop:
`faulthandler.dump_traceback_later(25, exit=True)` names the line.

**Dashed paths: walk by remaining length.** Never carry dash phase across corners by
subtracting an accumulator. That goes negative whenever `dash > gap`, drives the walk
position backwards, and never terminates. Track "distance left in the current dash"
and flip state when it reaches zero.

**Full-canvas per-frame work is the cost.** Blur and composite dominate, not the frame
count. A blur is low-frequency: blur at quarter size and upscale. For any animation,
redraw only the bounding box of what changed.

**Show a thing leaving its place, and it must clear that place.** An element drawn as
pulled out of a slot must move further than its own width, or it covers the slot it
left and the point is lost. Link the two with a connector so the pairing is explicit.

**Labels belong where there is room.** Four names will not fit across one narrow
container. Draw the silhouettes in place and name the items where they land. Keep
arrow tags ~20 px clear of the shaft, and check that a tag centred on a curve's
midpoint does not sit on the curve.

## 4. Verify by looking

Read the rendered PNG back and inspect it. Collisions, clipping, and overlap are
invisible in the source and obvious in the image. Never write assertions about layout
that the eye can check in one pass. Do assert the instance-derived counts.
