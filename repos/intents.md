# NEAR Intents: `near/intents`

Sources: `.agents/AGENTS.md` (`.claude/CLAUDE.md` holds the same text), read 2026-11-20. The project
sections are still "TODO" upstream, so the facts below come from CI and the merge history. The repo
has no CONTRIBUTING, no PR template and no CLA.

## Agent rules block

```text
You are contributing to NEAR Intents (near/intents), the verifier contract and
crates that settle cross-chain intents. It holds user funds — correctness and
storage compatibility are critical.

1. READ THE TERMINOLOGY in .agents/AGENTS.md (NEP-448, NEP-519 yield/resume,
   NEP-591 global contracts, NEP-616 deterministic account ids) before touching
   contract code. Do not invent NEP behaviour; cite the NEP or the code.

2. MATCH EXISTING PATTERNS. Read the surrounding crate first. Reuse the
   workspace's helpers and test fixtures; do not add a dependency or a new
   helper when one exists.

3. NO STATE OR ABI CHANGES unless the task asks for them. Contract storage
   layout, events and method signatures are public surface.

4. TESTS ASSERT BEHAVIOUR. Each test checks a concrete value or error. Tests
   that touch the filesystem use an exclusive temp directory with a Drop guard
   and never a shared path.

5. CHECKS BEFORE HANDING BACK, the Makefile targets CI runs: `make check-fmt`
   (cargo fmt --all --check; taplo checks TOML), `make check` (clippy,
   including the wasm32 contract targets), `make check-unused-deps` (cargo
   machete), `make doc`, then `cargo test -p <crate>` for the touched crate
   (CI runs `make test`, i.e. cargo test --all --all-features). Run builds on
   CI, not on this host.

6. COMMIT AND PR TITLE: conventional commits. Allowed types: feat, fix, chore,
   docs, style, refactor, perf, test, build, ci, revert. A title-lint job checks
   that the type matches the changed files (test-only changes are `test:`).

7. NO SECURITY TALK IN PUBLIC TEXT. Anything that looks like a way to move
   funds goes to the private note, not to a commit, PR, comment or test name.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| PR title | Linted by `pr-title-lint.yml`. A Claude-based job also checks that the type fits the changed files. |
| PR body | No template. Use Problem, Change and Tests, kept short. |
| Security-sensitive | The verifier contract holds user funds. Public work stays on tests, tooling and docs; anything with security impact goes through the project's security process only. |
| Merges | Most merges come from the core team (mitinarseny, hlgltvnnk). Expect slow review, and keep at most 3 PRs open. |
