# STYLE.md

This file documents style expectations to reduce ambiguity for agents
and humans.

## General principles

-   Prefer clarity over cleverness.
-   Prefer small, composable functions/modules.
-   Make dependencies explicit.
-   Use types where available.
-   Write tests that explain behavior.

## Naming

-   Names should reveal intent.
-   Avoid abbreviations unless ubiquitous in the domain.
-   Prefer "what it is" names for data and "what it does" names for
    functions.

## Comments and docs

-   Use comments to explain *why*, not *what*.
-   Document public interfaces and non-obvious invariants.

## Error messages

-   Errors should be actionable.
-   Prefer structured errors with codes/categories.
-   Don't leak secrets or sensitive data.

## Formatting

Formatting should be automated. Configure formatter/linter commands in
`harness.toml`.
