# System Design Tutorials

## About this workspace
This is a public tutorial repository. Act as a system design teacher: explain how systems are designed, with real-life tradeoffs, and with a strong focus on being useful for interview preparation.

The repository covers:
- **High-level design (HLD)**: architecture, components, data flow, scaling, e.g. "Design BookMyShow".
- **Low-level design (LLD)**: classes, interfaces, relationships, design patterns, code, e.g. "Design a Parking Lot".
- **Concepts**: reusable building blocks that designs link back to, e.g. caching, load balancing, SOLID.

All content is written as Markdown so it can be published as a documentation website. Diagrams must be text-based (see [Diagrams](#diagrams)) so they render both on GitHub and on the docs site.

## Audience and teaching approach
- Readers are engineers preparing for interviews or learning to design real systems. Assume programming knowledge, not system design knowledge.
- Teach the *why*, not only the *what*. Every significant decision states the alternatives considered, what was chosen, and the tradeoff (consistency vs availability, latency vs cost, simplicity vs flexibility, etc.).
- Build designs incrementally: start with a simple version that works, find its bottleneck, then evolve it. Do not present the final architecture as if it appeared fully formed.
- Use concrete numbers (QPS, storage, latency, cost) in HLD, and show the arithmetic.
- Call out where real systems differ from the interview answer, and what to say when the interviewer pushes back.
- Prefer accuracy over confidence. If a number or claim is an estimate or an assumption, say so.

## Project structure
```
system-design/
├── CLAUDE.md
├── README.md                     # Landing page: what this is, how to navigate, index of all designs
├── mkdocs.yml                    # Docs site config (nav must be updated with every new page)
├── requirements.txt              # Python deps to build the docs site
├── docs/                         # Symlinks only (index.md, high-level-design, low-level-design); never put content here
├── .github/workflows/docs.yml    # Builds and deploys the site to GitHub Pages
├── high-level-design/
│   ├── README.md                 # Index of HLD concepts and designs
│   ├── concept/                  # e.g. caching.md, load-balancing.md, sharding.md
│   └── design-<name>/            # e.g. design-book-my-show/
└── low-level-design/
    ├── README.md                 # Index of LLD concepts and designs
    ├── design-principles/        # Principles and design patterns, one page each: singleton-design-pattern.md, solid-principles.md
    ├── concept/                  # Other LLD building blocks (UML notation, concurrency primitives, ...)
    └── design-<name>/            # e.g. design-parking-lot/
```

Rules:
1. There are two top-level content directories: `high-level-design` and `low-level-design`.
2. Each may contain a `concept` directory with one file per concept. Concepts are self-contained and are linked from designs instead of being re-explained in them.
3. `low-level-design/design-principles/` holds OO design principles and design patterns (SOLID, Singleton, Factory, ...), one file per topic named `<topic>-design-pattern.md` for patterns or `<topic>.md` for principles. It has its own `README.md` index. Pattern and principle pages follow this flow: problem → intuition/analogy → plain-words explanation → official definition explained → structure diagrams → step-by-step Python 3.12 implementation → real-world uses and when not to use → tradeoffs → interview tips → key takeaways → references.
4. Every design example lives in its own directory named `design-<kebab-case-name>`, e.g. `design-book-my-show`.
5. Each design directory has a `README.md` as its entry point. Longer designs split into numbered files (see templates) so pages stay readable.
6. Directory and file names are lowercase kebab-case. No spaces.
7. Every new page is added to the parent `README.md` index and to the `nav` in `mkdocs.yml`.

## Design directory templates
Use these as the default outline. Skip a section only if it genuinely does not apply, and never leave it empty.

### High-level design (`high-level-design/design-<name>/`)
```
README.md                 # Problem summary, scope, table of contents, key takeaways
01-requirements.md        # Functional, non-functional, out of scope, assumptions
02-estimation.md          # Traffic, storage, bandwidth, with arithmetic shown
03-api-and-data-model.md  # Endpoints/contracts, entities, schema, DB choice and why
04-high-level-design.md   # Block diagram, request flows, component responsibilities
05-deep-dives.md          # The 2-3 hardest problems (e.g. seat locking, fan-out)
06-scaling-and-failures.md# Bottlenecks, caching, sharding, replication, failure modes
07-tradeoffs-and-followups.md # Decision table, alternatives, interviewer follow-ups
```
Small designs may collapse this into a single `README.md` with the same headings.

### Low-level design (`low-level-design/design-<name>/`)
```
README.md                 # Problem summary, scope, table of contents, key takeaways
01-requirements.md        # Functional, non-functional, use cases, assumptions
02-class-design.md        # Entities, class diagram, relationships, responsibilities
03-behavior.md            # Sequence, state, activity diagrams for key flows
04-patterns-and-principles.md # Design patterns and SOLID applied, and why
05-implementation/        # Runnable, tested reference code
06-extensibility-and-followups.md # Concurrency, new requirements, interviewer follow-ups
```

## Page conventions
Every page starts with YAML front matter and a single H1:
```markdown
---
title: <Page title>
description: <One-sentence summary, used for search and SEO>
---

# <Page title>
```
- Exactly one H1 per page; use H2/H3 for structure. Do not skip heading levels.
- Open with a short summary of what the reader will learn, close with key takeaways.
- Use relative links between pages (`../concept/caching.md`), never absolute URLs to the repo or site. Link to a concept the first time it is used on a page.
- Use tables for comparisons and tradeoffs. Use admonitions for callouts (`!!! tip "Interview tip"`, `!!! warning "Common mistake"`, `!!! note "Real world"`).
- Put code in fenced blocks with a language tag. Keep prose paragraphs short.
- Avoid content that depends on a specific renderer beyond what is listed here (MkDocs Material + Mermaid), so pages still read acceptably on GitHub.
- Do not copy text from books, courses, blogs or paid interview resources. Write in original words; cite sources in a `## References` section when a design is based on a published engineering blog or paper.

## Diagrams
Diagrams are **Mermaid** code blocks, so they live in version control, diff cleanly, and render on GitHub and the docs site. Do not commit exported images for diagrams that Mermaid can express.

| Need | Mermaid type |
|------|--------------|
| Block / architecture diagram, request flow | `flowchart` (use `subgraph` for tiers/regions) |
| UML class diagram | `classDiagram` |
| UML sequence diagram | `sequenceDiagram` |
| UML state diagram | `stateDiagram-v2` |
| Activity diagram | `flowchart` |
| ER / data model | `erDiagram` |
| Timeline, rollout, gantt | `gantt` / `timeline` |

Guidelines:
- One idea per diagram. Split large diagrams; a diagram with more than about 12 nodes needs to be broken up.
- Every diagram is introduced by a sentence saying what it shows, and followed by a walkthrough of the important parts.
- Label edges with what flows on them (protocol, event, data). Show data stores, caches and queues with distinct shapes.
- Class diagrams show visibility, key attributes and methods, multiplicities and relationship types (inheritance, composition, aggregation, association, dependency) correctly. Do not show every getter/setter.
- Start with a simple diagram and show its evolved version after the bottleneck discussion.
- Validate that each diagram renders before finishing (see [Build and preview](#build-and-preview)).

```mermaid
flowchart LR
    Client --> LB[Load Balancer] --> API[API Servers]
    API --> Cache[(Cache)]
    API --> DB[(Database)]
```

## Content standards

### High-level design
- Always begin with requirements clarification: functional, non-functional (scale, latency, availability, consistency), and explicit out-of-scope items.
- Estimation is required: state assumptions (DAU, read/write ratio, item size), then derive QPS, peak QPS, storage and bandwidth.
- Justify every technology choice against at least one alternative (e.g. SQL vs NoSQL, Kafka vs SQS, push vs pull). Name the tradeoff, not just the winner.
- Cover: APIs, data model, main flows, caching, partitioning/sharding, replication, consistency model, failure handling, and observability. Skip only what is irrelevant to the problem.
- Include a "what would change at 10x scale" discussion.

### Low-level design
- Start from requirements and use cases, then identify entities and responsibilities before drawing classes.
- Apply SOLID and design patterns only where they solve a stated problem. Name the pattern, the problem it solves and what the design would look like without it. Do not force patterns.
- Show both a class diagram and at least one sequence or state diagram for the main flow.
- Provide working reference code and address concurrency, extensibility (what changes when requirement X is added) and testability.
- Prefer composition over inheritance unless the domain is a real is-a hierarchy.

### Concepts
- Structure: what it is, why it exists (the problem), how it works, variants, tradeoffs, when to use and when not to, real-world examples, and interview tips.
- Keep concepts general. Design-specific usage belongs in the design, which links to the concept.

## Code conventions
- Language for all code (LLD reference code and any snippets in HLD): **Python 3.12**. Do not use syntax or features newer than 3.12, and do not switch languages.
- Use modern 3.12 idioms where they help the design: type hints on all public signatures (`list[str]`, `X | None`, the `type` statement and PEP 695 generics where useful), `abc.ABC` / `typing.Protocol` for interfaces, `dataclasses` and `enum` for entities and states, `threading` / `asyncio` for concurrency examples.
- Run and test code on 3.12 specifically, e.g. `uv run --python 3.12 --with pytest pytest`, since the machine's default Python may be newer.
- Follow PEP 8 and name things after the domain. Format with `ruff format`, lint with `ruff check`, and type-check with `mypy --strict` (or `pyright`).
- Use only the standard library in reference code, apart from `pytest` for tests. If a third-party package is genuinely needed, say why on the page.
- Code must run. Keep each example minimal, with an `if __name__ == "__main__":` demo or tests. Include `pytest` tests for behavior that is non-obvious, and for concurrency where relevant.
- Code lives in the design's `05-implementation/` directory as a plain package (`__init__.py`, one module per class or small group of related classes, `tests/`). It is referenced from the docs. Prefer including snippets from real files (with `pymdownx.snippets`, e.g. `--8<-- "path/to/file.py"`) over pasting code that can drift out of sync.
- Write idiomatic Python: use properties, first-class functions, `Protocol`s and composition instead of getters/setters, deep inheritance or pattern boilerplate. Say so when a classic pattern collapses into a language feature (e.g. Strategy as a callable).

## Docs site
- Generator: **MkDocs with the Material theme**, with Mermaid enabled through `pymdownx.superfences` custom fences, plus `admonition`, `pymdownx.details`, `tables`, `toc` and search.
- `mkdocs.yml` at the repo root defines `nav`. Keep navigation ordered: Concepts first, then designs, in the order they should be studied. Nav paths are relative to `docs/`, e.g. `high-level-design/concept/caching.md`.
- MkDocs requires `docs_dir` to be a child of the config directory, so `docs/` contains only symlinks to the real content (`index.md` → `../README.md`, plus the two design folders). Edit content in the real locations, and do not add files inside `docs/`.
- Hosting: GitHub Pages via a GitHub Actions workflow that builds on push to `main`.
- Do not commit the built `site/` directory.

### Build and preview
```bash
pip install mkdocs-material
mkdocs serve          # live preview at http://127.0.0.1:8000
mkdocs build --strict # fails on broken links and nav errors; run before committing
```
Without a local install: `uvx --from mkdocs-material mkdocs build --strict -d <temp dir>`.

## Workflow
1. **Agree on scope first.** Before writing a new design or concept, confirm what is in and out of scope, and the depth expected (interview-length vs deep dive).
2. **Outline, then write.** Share the section outline for the design, then fill it in following the template above.
3. **One design or concept per change.** Keep commits focused, and update the relevant index pages and `mkdocs.yml` in the same change.
4. **Self-review before finishing:** requirements covered, tradeoffs explicit, diagrams render, links resolve (`mkdocs build --strict`), code runs, `ruff` / `mypy` are clean and `pytest` passes, no copied text.
5. Commit messages: short imperative subject, e.g. `Add design-parking-lot class design`.

## Public repository rules
- Never commit secrets, credentials, personal data or company-confidential material. Do not present proprietary internal details of any employer as fact.
- Add a `LICENSE` (content and code) and a `CONTRIBUTING.md` before inviting outside contributions.
- Treat outside contributions like any other content: same templates, same review checklist.

## Progress tracking
Keep a table in the root `README.md` listing every concept and design with its status (`planned`, `draft`, `complete`), so readers and future sessions can see what exists and what is next.
