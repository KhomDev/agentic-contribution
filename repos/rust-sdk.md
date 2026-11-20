# MCP Rust SDK: `modelcontextprotocol/rust-sdk`

Sources: the repo `README.md` and `.github/instructions/fetch-mcp-doc.instructions.md`, plus the
org-wide `modelcontextprotocol/modelcontextprotocol:AI_POLICY.md`, read 2026-11-20. The repo has no
CONTRIBUTING and no PR template. CI runs commitlint (config-conventional) over every commit in the PR.

## Agent rules block

```text
You are contributing to rmcp, the official Model Context Protocol SDK for Rust
(crates/rmcp, macros, transports). Other MCP servers and clients build on it —
spec conformance is critical.

1. SPEC FIRST. For protocol behaviour, read the MCP specification version the
   code targets (the links in .github/instructions/fetch-mcp-doc.instructions.md).
   Cite the spec section; never guess message shapes.

2. EVERY COMMIT is a conventional commit (commitlint checks each one, not just
   the PR title): fix(client): ..., feat(transport): ..., docs: ...

3. CHECKS (from the justfile/CI): `cargo +nightly fmt --all -- --check`,
   `cargo clippy --all-targets --all-features -- -D warnings`,
   `cargo test --all-features -p rmcp -- <filter>`. Run them on CI.

4. TESTS assert protocol-visible behaviour (serialized JSON, errors returned to
   the peer), not internals.

5. DISCLOSE AI USE. The org AI policy requires the PR (and any AI-written
   comment) to say that AI was used and how much. Write the disclosure in the
   PR draft.

6. ISSUE FIRST for anything beyond a small bug fix; bugs and actionable items
   go in an issue first.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| Disclosure | Required in the PR body and in any AI-written review reply. Example: "This PR was written primarily by Claude Code; I reviewed and tested every change." `pr_lint.py` enforces it. |
| Claims | Most issues get a claimant or a PR within hours. Check `gh pr list --search <n>` right before you start and again before you open. |
| Release | release-plz writes CHANGELOG.md from the commits, so no changelog entry is needed. |
