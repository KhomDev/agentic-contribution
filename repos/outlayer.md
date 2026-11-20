# OutLayer: `out-layer/outlayer`

Sources: `CONTRIBUTING.md` and `CLAUDE.md` from `main`, read 2026-11-20.

## Agent rules block

```text
You are contributing to NEAR OutLayer (out-layer/outlayer): verifiable compute
and custody for AI agents in Intel TDX enclaves, plus the outlayer.near
contract. It is production custody code — correctness is critical.

1. NO PLACEHOLDERS. No TODO comments, no "for MVP" code, no stub returning
   vec![] — every public function works. Do not implement a feature for one
   platform and skip another.

2. ERRORS REACH THE USER: propagate with anyhow::bail!(...); tracing logs go
   only to server logs. No tokio::time::sleep without a strong reason.

3. DOCS AND COMMENTS DESCRIBE THE FINAL STATE ONLY — no history ("used to",
   "an earlier version", "removed because").

4. NO SUMMARY FILES (no *_SUMMARY.md, CHANGES.md, DOCUMENTATION_UPDATE_*.md).

5. CONTRACTS: build with `cargo near build`, never raw wasm32 cargo build.

6. NEVER COMMIT .claude/ or .mcp.json — CI (claude-config-guard.yml) fails
   the build.

7. LICENSES: no GPL/AGPL/SSPL/BUSL/source-available dependency. If you copy
   code from another project, keep its header, add it to NOTICE and say so.

8. API base is https://api.outlayer.ai (never app.outlayer.ai for API calls).
```

## Orchestrator notes

| Item | Rule |
|---|---|
| CLA | Signed by KhomDev in a PR comment, which covers future PRs. Check that the signature comment exists before you open a new PR. |
| Merges | Slow: zavodil merges in batches (2 outside PRs in 60 days). Keep at most 2 open. |
| Held | The worker-attestation Stage 3 docs branch overlaps #45. Offer it to #45 once zavodil reviews #45. |
