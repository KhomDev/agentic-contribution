# Signing, identity and attribution

## Identity

Every commit is authored as `KhomDev <KhomDev@users.noreply.github.com>`. It's set per repository,
never with `--global`, because other projects on this host use other identities.

## SSH signing (once per clone or worktree)

```bash
git config user.name KhomDev
git config user.email KhomDev@users.noreply.github.com
git config gpg.format ssh
git config user.signingkey "<signing_key from local/config.json>"
git config commit.gpgsign true
```

Locally, `git log --format=%G?` shows `N`. That only means no `allowedSignersFile` is configured on
this host. GitHub's verdict is the one that counts:

```bash
python scripts/signed_check.py --repo <key> --pr <n>       # or --sha <sha>
```

## Re-signing an agent's commits

Agents commit unsigned, with their own trailer. Before anything leaves `verify/*`:

```bash
# one commit, clean tree
git commit --amend -S --no-edit            # after fixing the trailer in the message
# dirty tree or a branch you must not check out: build the commit from its tree
git commit-tree -S -p <parent> -F msg.txt <tree-sha>     # prints the new sha
git branch -f <branch> <new-sha>      # branch not checked out
git reset --soft <new-sha>            # branch checked out (keeps the dirty tree)
```

The message keeps the agent's subject and body, but its last line becomes this attribution,
exactly once:

```
Authored by KhomDev with AI assistance.
```

Do not add a `Co-Authored-By: Claude ...` trailer. `pr_lint.py` requires the attribution line and
rejects a leftover Claude Co-Authored-By trailer.

Some upstreams forbid AI co-author trailers outright. When a repo sets `commit_trailer: "none"` in
`config/repos.json` (OpenZeppelin/cairo-contracts is the first), commit with **no attribution line
and no Co-Authored-By trailer**; `pr_lint.py` then errors if either is present. The PR body footer
is unaffected.

Before force-pushing a branch behind an open PR, ask yourself whether the reviewer has already seen
it. If they have, a new commit beats a rewrite. Either way, the push is a gated action.

## PR body footer

Every PR body ends with this line, which `pr_lint.py` checks:

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## AI disclosure

| Repo | Requirement |
|---|---|
| modelcontextprotocol/* | Org `AI_POLICY.md`: disclose any AI use and its extent in the PR, and in AI-written replies too. |
| x402 | Disclose significant AI use. Ours is always significant. |
| OpenZeppelin | AI welcome, but low-effort output gets closed. The footer is enough. |
| others | The footer is enough. Never deny AI use if asked. |

The disclosure is one plain sentence, e.g. "Most of this change was written with Claude Code; I
reviewed every line and ran the tests below." It must be true: the operator does review at the gate.
