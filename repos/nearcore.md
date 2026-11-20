# nearcore: `near/nearcore`

Sources: `AGENTS.md` and `CONTRIBUTING.md` from `master`, read 2026-11-20.

## Agent rules block

```text
You are contributing to nearcore, the reference NEAR Protocol node. Code here
runs every validator — correctness and determinism are critical.

1. RUST STYLE (AGENTS.md): never use fully qualified paths such as
   std::collections::HashMap::new(); add a `use`. Do not capitalize string
   literals in logs, errors, expect() or panic!(). Borrow from an Arc with
   `arc.as_ref()`, not `&*arc`.

2. TESTS: run one test with
   `cargo test --package <pkg> --features test_features -- <path::to::test> --exact --show-output`
   (include test_features only if the package defines it). Test-loop tests:
   read test-loop-tests/README.md and the examples first.

3. FORMAT AND LINT: `cargo fmt` after every change; Python
   `scripts/formatting --fix`. Clippy only before committing, with exactly
   `RUSTFLAGS="-D warnings" cargo clippy --all-features --all-targets` — never
   per package. On this host run both on CI, not locally.

4. DO NOT run the protocol schema check, update the OpenAPI spec, or edit
   protocol-model/ unless the task says so.

5. READ THE AREA DOC before touching it: chain/chain/AGENTS.md,
   runtime/runtime/AGENTS.md, docs/architecture/how/*.md.

6. PR TITLE: `<type>: <title>` or `<type>(<project>): <title>`. Types: fix,
   feat, refactor, doc, test, chore, perf, revert (note `doc`, not `docs`).
   Lowercase project and lowercase title; no [brackets].

7. CHANGELOG.md [unreleased] only for user-observable changes (protocol
   feature, config option, Prometheus metric).

8. STAY OUT of consensus, networking, crypto and validator logic. Tooling,
   test utilities and docs only.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| PR checkbox | Tick "Allow edits and access to secrets by maintainers". Without it the merge bot cannot land the PR. `gh pr create` sets it by default for forks; check it in the UI after opening. |
| Merging | Commits are squashed. An approved PR enters the merge queue. |
| Review bots | Greptile comments on every PR. Treat its P1/P2 items like a human review: fix what is right, reply with the sha. |
| CI | `ci.py dispatch --target KhomDev/nearcore --toolchain rust --apt 'clang cmake' --command 'cargo test -p <pkg> -- <filter>'`. The workflow frees disk; full builds take 30-60 min. |
| Windows | Long paths: keep checkouts and worktrees close to the drive root, e.g. `C:\nc\`. |
