# Foundry: `foundry-rs/foundry`

Sources: `AGENTS.md` (`CLAUDE.md` has the same content), `CONTRIBUTING.md` and
`.github/PULL_REQUEST_TEMPLATE.md` from `master`, read 2026-11-20.

## Agent rules block

```text
You are contributing to Foundry (forge, cast, anvil, chisel), the Ethereum
development toolkit in Rust. Auditors and teams rely on its test results —
correctness of output is critical.

1. READ AGENTS.md and the docs/dev/ guide for the area (output-channels.md for
   CLI output, networks.md for custom networks, lintrules.md for lints).

2. REUSE OWNERS: before building or converting an alloy/evm2/Foundry value by
   hand, use the owning type's constructor or helper (foundry_common,
   foundry_config). Put behaviour in the component that owns the state.

3. CLI OUTPUT uses the sh_* / prompt! macros; never std::print*/eprint*.

4. TESTS for every fix or feature. Forge CLI tests in crates/forge/tests/cli/
   with #[forgetest]/#[forgetest_init]; cast in crates/cast/tests/cli/ with
   #[casttest]. Assert with snapbox (stdout_eq(str![...]), assert_json_stdout)
   and full snapshots with redactions, not String::contains. Fork tests have
   "fork" in their name.

5. FORMAT AND LINT with nightly: `cargo +nightly fmt --all`,
   `cargo +nightly clippy --workspace --all-targets --all-features`. Tests:
   `cargo nextest run -p <crate> <filter>`. Builds run on CI, not on this host.

6. COMMITS AND TITLE: `type(scope): description` with feat, fix, perf, chore,
   docs, test or refactor; imperative, under 50 characters when practical, no
   trailing period. Bug fixes and complex changes get a body.

7. PR DESCRIPTION: what changed and why, in flowing prose. No templates, no
   bullet lists, no "Tested with" command lists, only real measurements.

8. CONFIG SETTINGS and CHEATCODES follow the step lists in AGENTS.md exactly
   (including the book update for config and `cargo cheats` twice).
```

## Orchestrator notes

| Item | Rule |
|---|---|
| Template vs AGENTS.md | The GitHub template has Motivation, Solution and Checklist. AGENTS.md (the agent rules) says prose with no templates. We follow AGENTS.md and keep the body to 2-4 short paragraphs. |
| Labels | AGENTS.md says to label PRs. Outside contributors cannot set labels: leave it to the maintainers and don't mention it. |
| Maintainer edits | Tick "Allow edits from maintainers". |
| Speed | The core team fixes most bugs within hours, so check for an open maintainer PR right before you open ours (e.g. #18627 beat our #18616 analysis). Independent confirmation on their PR is still useful. |
| CI | `ci.py dispatch --target <ref repo> --toolchain rust --command 'cargo test -p forge --test cli -- <filter>'` (the CI runner has no cargo-nextest; 24 Nov). Lint exactly as upstream's `ci.yml` does: `RUSTFLAGS=-Dwarnings cargo +<pinned nightly> clippy --workspace --all-targets --all-features --locked` (pinned in the clippy job, `nightly-2026-10-31` on 24 Nov) and `cargo +nightly fmt --all --check`. Latest nightly fails on renamed lints, and `-p <crate> --all-features` turns anvil's features off and fails on untouched code. Real-RPC repros use dRPC endpoints (base.drpc.org, polygon.drpc.org); polygon-rpc.com returns 401. |
