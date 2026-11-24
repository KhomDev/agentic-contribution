# Anchor: `otter-sec/anchor` (formerly `coral-xyz/anchor`)

Sources: `CONTRIBUTING.md` and `.github/pull_request_template.md` from `master`, read 2026-11-22.
The old `coral-xyz/anchor` path redirects here; verify the remote before cloning.

## Agent rules block

```text
You are contributing to Anchor (otter-sec/anchor), the Solana program
framework. Programs holding user funds compile against it — correctness is
critical.

1. CLAIM THE ISSUE by commenting, then open a draft PR as soon as there is
   something to review. Maintainers track work by PR.

2. BRANCH TARGET: `master`. Breaking changes target `anchor-next`.

3. SIGN EVERY COMMIT (CONTRIBUTING requires commit signing).

4. ONE CONCERN PER PR. File an issue instead of drive-by refactors.

5. COMMENTS: at most 80 characters per line.

6. RUST: fully qualified paths inside macros (for example
   `anchor_lang::accounts::account::Account`), except in IDL build codegen.

7. TESTS: adversarial tests — the success path and the failure path where a
   check is violated. If you add a folder under `tests/`, add it to the CI
   workflow.

8. LLMs: allowed for code and for drafting the PR description, but write the
   description mostly by hand and never let a model answer review comments
   autonomously.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| PR title | Conventional, loosely enforced (`fix(lang): ...`, `doc(lang): ...`); recent merges use `doc`, not `docs` |
| PR body | Template: `## Summary` and `## Branch Target` |
| Signing | Required by CONTRIBUTING; our commits are signed regardless |
| AI disclosure | Allowed; footer is enough; never let a model answer reviewers autonomously |
| CI | `cargo test`; `cargo +nightly fmt`; `cargo clippy --all-targets -- -D warnings`; TypeScript tests with `yarn test` in the relevant package |
| Changelog | `CHANGELOG.md` under `## [Unreleased]` (Keep a Changelog); confirm the maintainers' practice for small fixes |
| Tracker speed | Very fast: 61 merged PRs and 21 from outside authors in the 30 days to 2026-11-22 |
| Volume | Budget 2 open PRs; draft PRs are expected early |
