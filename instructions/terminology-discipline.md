# Terminology discipline

One concept carrying two names costs every reader a translation and every agent a missed match.

**Location.** The dictionary is one file at a path the consuming project pins in its own
`AGENTS.md`. `project_metadata/term-dictionary.md` is the default; wherever it lands, that
location is the single one, and this document is its only governing authority — no specification
states rules about it.

- **Create.** The dictionary is the single location for terms the project introduces. Index a term
  when all three hold:
  - it is expected to be referenced across project documents;
  - it is not a general or well-known word or phrase;
  - it took its present meaning from the project's context.

  Candidates span every kind of named thing: an object of the model, a parameterized formula and
  its symbols, a business or domain concept, a metric or reported criterion, a constraint, an
  architectural seam, a design pattern, a coding or authoring convention, and any acronym standing
  for one of these. **Excluded:** generated code symbols, and anything an established field already
  names — adopt that name and index nothing.
- **Maintain.** The change that introduces a term adds its entry; the change that retires one
  deletes it. Entries are a minimal key-value structure — the term, then one concise line — in
  plain text that renders in any Markdown host without a pre-render step. Where two terms sit close
  enough that a reader would merge them, index both and state the difference.
- **Use.** Load the dictionary into session context before starting work, and spell every concept
  the way the dictionary spells it — in prose, in diagrams, and in identifiers alike.
