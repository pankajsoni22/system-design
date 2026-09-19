---
title: System Design Tutorials
description: High-level and low-level system design tutorials with real-life tradeoffs, written for interview preparation.
---

# System Design Tutorials

Worked system design examples that explain **why** each decision is made, not just what the final architecture looks like. Every design walks through the requirements, the alternatives considered, and the tradeoffs, so you can defend your choices in an interview and in a real design review.

## How to use this repository

- **[High-Level Design](high-level-design/README.md)**: architecture, components, data flow and scaling (e.g. "Design BookMyShow").
- **[Low-Level Design](low-level-design/README.md)**: classes, interfaces, design patterns and code (e.g. "Design a Parking Lot").
- **Concepts**: each section has a `concept/` folder with reusable building blocks (caching, load balancing, SOLID, ...). Designs link to these instead of re-explaining them.

Read the concepts first if a term is new, then work through the designs in the order listed below.

## Progress

Status: `planned` → `draft` → `complete`.

### High-level design

| Type | Topic | Status |
|------|-------|--------|
| Concept | _none yet_ | |
| Design | _none yet_ | |

### Low-level design

| Type | Topic | Status |
|------|-------|--------|
| Concept | [UML basics: class diagrams](low-level-design/concept/uml-basics.md) | `complete` |
| Design pattern | [Singleton, with a worked Logger design](low-level-design/design-principles/singleton-design-pattern/README.md) | `complete` |
| Design pattern | [Factory (Simple, Method, Abstract), with a worked Notification Service design](low-level-design/design-principles/factory-design-pattern/README.md) | `complete` |
| Design | _none yet_ | |

## Run the docs site locally

```bash
pip install -r requirements.txt
mkdocs serve           # live preview at http://127.0.0.1:8000
mkdocs build --strict  # fails on broken links and nav errors
```
