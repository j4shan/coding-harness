# Terminology discipline

**Objective.** Capture the project's context-dependent language — words and phrases a reader
cannot recover from a general dictionary or from the public literature — so later documents
keep one spelling and one meaning for each.

**Your tasks.** You own the project's term dictionary: **create** it, **admit** terms into it,
**maintain** it as your changes add and retire terms, and **use** it in everything you write.

Perform all four. Each states the conditions under which it applies.

## 1. Create the dictionary

Keep the dictionary at `project_metadata/term-dictionary.md`, relative to the project root.
Create the file if it does not exist — this is your responsibility, not a precondition to wait on.

## 2. Admit a term

Index a word or phrase only when all three conditions hold:

- it names a key project concept, not a passing detail;
- a reader who knows the field still cannot recover this project's meaning from a general
  dictionary or from the public literature — the meaning is bound to this project's context;
- it is already reused across project documents, or it will be.

Admit only these three kinds of text. Write the entry in the matching shape.

| Kind | What it is | Entry shape |
| --- | --- | --- |
| coined name | a name or compound this project introduced | **term:** the project-bound meaning, one line |
| reserved word | an ordinary or field word this project binds against its common sense — the common reading would pick the wrong referent | **term:** reserved for \<referent\>; not \<the reading it rejects\> |
| project phrase | a multi-word claim the project treats as load-bearing | **phrase:** the claim it carries, one line |

Never index a word a general dictionary or the field already defines in the sense you are using.
A model object, formula, metric, or constraint that the product requirement document already
names under such a word does not become an entry just because this project uses it.

Never coin a term for something an established field already names. Adopt that field's name
and index nothing.

Never index a generated code symbol.

Never turn the dictionary into a restatement, symbol index, or section digest of another
project document.

## 3. Maintain the dictionary

Add an entry in the same change that introduces its term. Delete an entry in the same change that
retires its term. Do not defer either to a follow-up.

Write each entry as a key-value pair in plain Markdown that renders without a pre-render step.
The key is the term or phrase. The value is one concise line in the shape the kind requires.

When two admitted terms sit close enough that a reader would merge them, keep both entries and
state the difference in each line.

## 4. Use the dictionary

Load the dictionary into session context before starting work.

Spell every admitted concept the way the dictionary spells it — in prose, in diagrams, and in
code identifiers alike. When you find a document or identifier spelling an admitted concept
differently, correct it to the dictionary's spelling, or correct the dictionary if the other
name is the better one.
