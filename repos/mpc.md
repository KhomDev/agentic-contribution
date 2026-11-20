# NEAR MPC (Chain Signatures): `near/mpc`

Sources: `AGENTS.md` and `CONTRIBUTING.md` from `main`, read 2026-11-20. Both point to
`docs/development/engineering-standards.md`, which is mandatory reading before any code change.

## Agent rules block

```text
You are contributing to near/mpc, the threshold-signature network behind NEAR
Chain Signatures (contract, node, TEE launcher). It secures keys for real
assets — correctness is critical.

1. READ FIRST: AGENTS.md and docs/development/engineering-standards.md. They
   are mandatory for every change.

2. TEST SHAPE. New tests are named `<system_under_test>__should_<assertion>`
   and use `// Given`, `// When`, `// Then` blocks. Same steps on different
   inputs → one `rstest` test with named `#[case::...]`s, not copies.

3. NO `as` NUMERIC CASTS. Use From for lossless conversions, TryFrom otherwise.
   Plain arithmetic in tests is fine (no checked_/saturating_ there).

4. TEST-ONLY CODE is `#[cfg(test)]` or behind the crate's `test-utils`
   feature. Never `#[allow(dead_code)]` to keep it compiled.

5. COMMENTS: default to none. Keep one only for a non-obvious why, public API,
   or a `TODO(#issue)`. Strip comments that restate the code. In doc comments
   use intra-doc links ([`Foo`]), not plain backticks.

6. PARSE, DON'T VALIDATE: validation returns a validated type, not a bool.
   Traits are named after the action (`ReadContractState`), and a referencing
   type is declared before the type it references.

7. FILES stay under 1000 lines (aim for 500). Do not split an existing large
   file unless asked; mention it instead.

8. DOCS ALIGNMENT: if you rename or reshape code, update the live docs under
   docs/ and nearby doc comments in the same change. Never edit a document with
   a `**Status:** ARCHIVED` banner.

9. CHECKS: `cargo fmt -- --check`, `cargo clippy --all-targets --locked -- -D
   warnings`, and `cargo nextest run --cargo-profile=test-release <filter>`
   for the touched crate. Snapshot changes go through `cargo insta`. Run builds
   on CI (mpc-branch-verify.yml), not on this host.

10. COMMIT AND PR TITLE: conventional commits with a scope, e.g.
    `refactor(node): ...`, `test(contract): ...`, `ci: ...`.

11. ISSUES FIRST. Work only on an issue; the PR description links it. The
    issue template is Background / Acceptance Criteria / (User Story).
```

## Orchestrator notes

| Item | Rule |
|---|---|
| Process | Assign yourself to the issue (a comment asking for assignment when you can't self-assign), then link the issue in the PR. |
| Reviews | Maintainers request changes explicitly. Answer each one with a commit, then reply "Fixed in <sha>". |
| CI | `ci.py mpc --ref verify/<n>-<slug> --crate <crate> --test-filter <name>`. The `mpc-contract` crate builds cargo-near. Order-dependent tests need the 20-seed shuffle. |
| Security-sensitive | The node, contract, TEE and crypto code secure keys. Only test isolation, tooling, CI and docs work is eligible for public PRs. |
| Exclusions | Items already done or held are in the state file and the private repo notes (local overlay). |
