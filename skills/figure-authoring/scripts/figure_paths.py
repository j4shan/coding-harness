"""Path constants for figure artifacts. Import these instead of retyping prefixes.

The same three paths are written out in SKILL.md section 2 for a human reader.
Change one, change the other.

    from figure_paths import SOURCE
    SOURCE.format(figure="checkout_flow")   # resources/img/checkout_flow.drawio
"""

PROMPT_DIR = "resources/img_prompt"
DATA_DIR = "resources/data"
IMG_DIR = "resources/img"

PROMPT = PROMPT_DIR + "/{figure}_prompt.md"
SOURCE = IMG_DIR + "/{figure}.drawio"
RENDER = IMG_DIR + "/{figure}.png"
MODEL = DATA_DIR + "/{figure}_model.json"
