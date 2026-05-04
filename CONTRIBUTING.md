# Contributing to x3d_mcp

## Issue lifecycle

Each issue follows the same three-step pattern:

1. **Plan comment** — post the implementation plan as a comment on the issue before writing code: problem, approach, files to be changed, tests to be added.
2. **Implement** — code on the host, tests in Docker.
3. **Test evidence comment** — after `docker compose up --build` passes, post a comment with the relevant test names and the final `N passed` line. Save the full container log to `output/logs/<issue-number>.log` and commit it.

The closing commit references the issue with `Closes #N` so it auto-closes on push to `main`.

## Testing

All code lives on the host. The Dockerfile and `docker-compose.yml` exist solely to run `pytest` in a clean container. There is no runtime MCP Docker image.

```bash
docker compose up --build
```

Per-issue log goes to `output/logs/<issue-number>.log` and is committed with the work.

## Commit messages

- Sentence-case subject, no conventional-commit prefix (`feat:`, `fix:` etc.). Match the existing log style.
- Body explains *why*, not what.
- Reference the originating mailing-list discussion or contributor when the work came from outside the repo.
- Do **not** add `Co-Authored-By:` trailers for AI assistants. This project ships under the Web3D Consortium Open-Source License; commits should attribute only the human authors.

## Labels — what not to use

Do **not** apply `help wanted` or `good first issue` to issues on this repo. Both labels are aggressively scraped by bounty-farming accounts that drop LLM-generated "I can have a PR ready in N days" comments without producing any code (see the hidden-as-spam comment thread on #13 for an example pattern).

If an issue is genuinely waiting on community input from the X3D AI WG / Web3D Consortium, use `question` and explain in the issue body who you're waiting on. The deferral comment carries the meaning; the label does not need to.

## Docs

When changing behaviour that's described in `README.md` or `docs/`, update the prose in the same commit. The README "Validation Pipeline", "Architecture", and Dependencies sections are load-bearing — they're how the WG reviews this work.

## Secrets

`.env` is in `.gitignore`. Never stage it. When adding new env vars, document them in the README and reference them in `docker-compose.yml` if the test runner needs them.
