# Public text: titles, bodies, commits, comments

Everything here is read by maintainers who decide in seconds whether a contribution is careful.

## Voice

- First person singular ("I"). Never "we" or "our team".
- Plain and specific: what is wrong, where (repo-relative path), what changes, and how it was
  proven. No filler ("This PR aims to…", "comprehensive", "robust", "seamless").
- Say only what the evidence shows. "The test fails on main and passes here" is fine only with both
  runs in hand.

## Never in public text

`pr_lint.py` turns most of these into errors through `public_text.error_patterns` in
`config/repos.json`:

- the operator's other projects, programs or private work (the overlay's patterns cover the names);
- agents, sub-agents, orchestration, Haiku, "this brief", the workspace or its tools;
- host paths (`C:\Users\…`, `/c/Users/…`), Windows usernames, personal emails;
- security details of unfixed issues, or hints that point at one;
- other projects of the operator.

The warn patterns (`audit`, `exploit`, `vulnerab`, `attacker`, `agent`) can be legitimate, e.g. "the
review agent's commands" in an mpc CI PR. Each hit gets a look and a one-line reason in the gate
packet.

## PR body skeleton (template repos)

Use the repo's own template headings when it has one (see `repos/<key>.md`). Otherwise:

```markdown
Fixes #<n>.

## Problem
<2-4 sentences: the observable failure, on current main, with a file:line>

## Change
<what the diff does and why this approach, 2-5 sentences or a short list>

## Tests
<the test added; red on main <url>, green here <url>; pasted result lines>

<AI disclosure sentence, where the repo needs one>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

Foundry is the exception: 2-4 paragraphs of prose with no headings, lists or command lists (its
AGENTS.md).

## Review replies

- One reply per thread: "Fixed in <sha>: <one line on what changed>". If you disagree, give the
  evidence, keep it short and polite, and end with a question if the point is open.
- Bots (Greptile, CodeRabbit, Copilot) get the same treatment: fix what is right, and briefly explain
  what is not.
- Every reply goes through the operator gate.

## Prior art comments

When someone else's stale PR already fixes the issue, the comment credits them by name and PR
number, says what was re-checked (e.g. "still applies to main at <sha>; CI passes"), and asks the
maintainers whether they'd like it reopened. It never offers our own copy.
