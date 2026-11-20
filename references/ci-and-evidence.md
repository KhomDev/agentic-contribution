# CI and evidence

## Where builds run

This host has about 1 GB of free RAM, so large Rust workspaces (nearcore, agave, foundry, mpc,
intents) never build locally. Everything runs on the public repo `KhomDev/oss-ci`. Public repos get
free Actions minutes. The earlier private CI repo hit the account's billing limit on 2026-11-19.

`oss-ci` is public, so never put anything private there: no security findings, no unreleased
material, no private-note content. Run names and commands are visible to anyone.

| Workflow | Use | Inputs |
|---|---|---|
| `fork-branch-verify.yml` | any public repo or fork, any command | `repo`, `ref`, `toolchain` (rust/node/rust+node/none), `command`, `label`, optional `apt` and `node_version` |
| `mpc-branch-verify.yml` | KhomDev/mpc: fmt, clippy and test of one crate | `ref`, `crate`, `test_filter` |

`fork-branch-verify` names each run `<repo>@<ref>: <label>`, and `ci.py` finds the run id by that
title. It frees about 30 GB of disk and sets `CARGO_PROFILE_DEV_DEBUG=0`.

```bash
python scripts/ci.py dispatch --target KhomDev/nearcore --ref verify/12401-home-dirs \
  --toolchain rust --apt 'clang cmake' --label green \
  --command 'cargo test -p integration-tests -- test_env --exact'
python scripts/ci.py status <id>          # at most every 5 minutes
python scripts/ci.py grep <id> 'test result|panicked|FAILED'
```

`--target` can be any public repo at any ref, e.g. `foundry-rs/foundry` at a maintainer's PR head
SHA. That's how #18627 was checked against the reporter's real-RPC repro.

## GitHub quota

The REST limit is 5000 requests an hour, shared by every session and agent on the account. On
2026-11-19 parallel `gh run watch` drained it, which blocked review work for an hour. The rules:

- No `gh run watch`, and no loop that polls faster than once every 5 minutes.
- `ci.py` and `signed_check.py` refuse to start below `min_rest_quota`, which is 300.
- Check the quota with `gh api rate_limit --jq '.resources.core'`. The `reset` field is a Unix time.
- A background wait is `sleep 1800; python scripts/ci.py status <id>` run with
  `run_in_background`. The harness wakes you when it ends, so never poll the wait itself.

## Evidence standard

| Claim | Proof required |
|---|---|
| Bug fix | The same test, red on the baseline (or on a mutant of the fix) and green on the branch. Both CI URLs and the pasted result lines go in the body. |
| Flaky or order-dependent test | A 20-seed shuffle on the baseline and the branch, e.g. "13/20 fail on main, 0/20 on the branch". |
| Docs snippet | The old snippet fails to compile or run (paste the error) and the new one succeeds, on CI. |
| Regression bisect | The last-good and first-bad builds, from source when nightlies are coarse. |
| "X doesn't exist" | A grep under at least three names. |

```bash
for s in $(seq 1 20); do
  RUSTC_BOOTSTRAP=1 cargo test -p <crate> -- -Z unstable-options --shuffle-seed $s >/dev/null 2>&1 \
    && echo "seed $s pass" || echo "seed $s FAIL"
done
```

Baseline branch: `verify/baseline-<short-sha>`, pushed from the unchanged upstream default branch.

## Writing evidence into a PR body

Paste only real lines and real URLs, with nothing summarised beyond what the output shows. Foundry
is the exception: its AGENTS.md wants prose with no command lists, so state the result in a sentence
and keep the URLs in the gate packet for the operator.
