# Terminology discipline

**Objective.** Give every concept this project invents exactly one name, so no reader has to
translate between synonyms and no agent misses a match on a term it has seen under another name.

**Your tasks.** You own the project's term dictionary: **create** it, **maintain** it as your
changes add and retire terms, and **use** it in everything you write.

Perform all three. Each states the conditions under which it applies.

## 1. Create the dictionary

Keep the dictionary at `project_metadata/term-dictionary.md`, relative to the project root.
Create the file if it does not exist — this is your responsibility, not a precondition to wait on.

Index a term only when all three conditions hold:

- it is expected to be referenced across project documents;
- it is not a general or well-known word or phrase;
- it took its present meaning from this project's context.

Index a qualifying term whatever kind of thing it names: an object of the model, a parameterized
formula and its symbols, a business or domain concept, a metric or reported criterion, a
constraint, an architectural seam, a design pattern, a coding or authoring convention, or an
acronym standing for any of these.

Never index a generated code symbol.

Never coin a term for something an established field already names. Adopt that field's name and
index nothing.

## 2. Maintain the dictionary

Add an entry in the same change that introduces its term. Delete an entry in the same change that
retires its term. Do not defer either to a follow-up.

Write each entry as a key-value pair — the term, then one concise line of explanation — in plain
text that renders in any Markdown host without a pre-render step.

When two terms sit close enough that a reader would merge them, index both and state the
difference between them.

## 3. Use the dictionary

Load the dictionary into session context before starting work.

Spell every concept the way the dictionary spells it — in prose, in diagrams, and in code
identifiers alike. When you find a document or identifier spelling a concept differently, correct
it to the dictionary's spelling, or correct the dictionary if the other name is the better one.
